from contextlib import AsyncExitStack
from typing import Any, List, Dict, Tuple
import asyncio
import json
import sys
import requests
from urllib3.exceptions import MaxRetryError
import mcp.types as types
import a2a.types as a2a_types
from pygeai.proxy.servers import MCPServer, ToolServer, ProxiedTool, A2AServer
from pygeai.proxy.config import ProxySettingsManager
from pygeai.proxy.clients import ProxyClient, ToolProxyData, ToolProxyJobResult
from pygeai.core.utils.console import Console

class ServerManager:
    """
    Manages multiple MCP servers.

    :param servers_cfg: List[Dict[str, Any]] - List of server configurations
    :param settings: ProxySettingsManager - Proxy settings manager
    """

    def __init__(self, servers_cfg: List[Dict[str, Any]], settings: ProxySettingsManager):
        """
        Initialize the server manager.

        :param servers_cfg: List[Dict[str, Any]] - List of server configurations
        :param settings: ProxySettingsManager - Proxy settings manager
        """
        self.servers_cfg = servers_cfg
        self.settings = settings
        self.servers: Dict[str, ToolServer] = {}
        self.tools: Dict[str, ProxiedTool] = {}
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    async def _initialize_servers(self) -> None:
        """
        Initialize all servers.

        :return: None
        :raises: Exception - If server initialization fails
        """
        for server_cfg in self.servers_cfg:
            Console.write_stdout(f"Initializing server {server_cfg['name']} type: {server_cfg['type']}")
            if server_cfg['type'] == 'mcp':
                server = MCPServer(server_cfg['name'], server_cfg, self.settings)
            elif server_cfg['type'] == 'a2a':
                server = A2AServer(server_cfg['name'], server_cfg, self.settings)
            else:
                raise ValueError(f"Invalid server type: {server_cfg['type']}")
            try:
                await self.exit_stack.enter_async_context(server.exit_stack)
                await server.initialize()
                self.servers[server.name] = server
                Console.write_stdout(f"\nServer {server.name} initialized successfully", end="\n\n")        
            except Exception as e:
                Console.write_exception(f"Failed to initialize server {server.name}:", e)
                raise

        for server in self.servers.values():
            Console.write_stdout(f"Listing tools for server {server.name}", end="")
            if server.public_prefix:
                Console.write_stdout(f" | access scope:public prefix: {server.public_prefix}")
            else:
                Console.write_stdout(" ! access scope:private")

            tools = await server.list_tools()
            for tool in tools:
                self.tools[tool.get_full_name()] = tool
                Console.write_stdout(f"\tTool {tool.get_full_name()} added to server {server.name}")

    async def _initialize_client(self) -> ProxyClient:
        """
        Initialize the client.

        :return: ProxyClient - Initialized client instance
        :raises: ConnectionError - If connection fails
        :raises: MaxRetryError - If max retries are exceeded
        """
        try:
            alias = self.settings.get_current_alias()
            client = ProxyClient(self.settings.get_api_key(alias), self.settings.get_base_url(alias), self.settings.get_proxy_id(alias))
            Console.write_stdout(f"\nRegistering proxy {self.settings.get_proxy_id(alias)} with name {self.settings.get_proxy_name(alias)} and description {self.settings.get_proxy_description(alias)}")
            result = client.register(proxy_data=ToolProxyData(
                id=self.settings.get_proxy_id(alias),
                name=self.settings.get_proxy_name(alias),
                description=self.settings.get_proxy_description(alias),
                affinity=self.settings.get_proxy_affinity(alias),
                tools=list(self.tools.values())
            ))
            Console.write_stdout("----------------------------------")
            Console.write_stdout(f"Proxy registered successfully:")
            if isinstance(result, dict) and isinstance(result.get("Messages"), list):
                for message in result["Messages"]:
                    description = message.get("Description", "")
                    message_type = message.get("Type", None)

                    if message_type == 1:
                        Console.write_stderr(description)
                    elif message_type == 2:
                        Console.write_stdout(description)
                Console.write_stdout("----------------------------------")
            return client
        except (ConnectionError, MaxRetryError):
            Console.write_exception(f"Error registering proxy {self.settings.get_proxy_id(alias)}:")
            raise
    
    async def execute_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """
        Execute a tool with retry mechanism.

        :param server_name: str - Name of the server to execute the tool on
        :param tool_name: str - Name of the tool to execute
        :param arguments: dict[str, Any] - Tool arguments
        :param retries: int - Number of retry attempts
        :param delay: float - Delay between retries in seconds
        :return: Any - Tool execution result
        :raises: RuntimeError - If server is not found or not initialized
        :raises: Exception - If tool execution fails after all retries
        """
        if server_name not in self.servers:
            raise RuntimeError(f"Server {server_name} not found")
        
        if tool_name not in self.tools:
            raise RuntimeError(f"Tool {tool_name} not found")
            
        server = self.servers[server_name]
        
        try:
            result = await server.execute_tool(self.tools[tool_name].name, arguments, retries, delay)
            return result
        except (RuntimeError, ConnectionError, TimeoutError) as e:
            raise Exception(f"Failed to execute tool {tool_name} on server {server_name}: {e}") from e

    def extract_function_call_info(self, raw_json: str) -> Tuple[str, str]:
        """
        Extract function call info from raw JSON.

        :param raw_json: str - Raw JSON string
        :return: Tuple[str, str] - Tuple containing function name and arguments
        """
        try:
            data = json.loads(raw_json)
            return data['function']['name'], data['function']['arguments']
        except (json.JSONDecodeError, KeyError) as e:
            Console.write_stdout(f"Error extracting function call info: {e}")
            return None, None
        
    async def start(self) -> None:
        """
        Main proxy session handler.

        :return: None
        """
        retry_count = 0
        MAX_RETRIES = 10
        while retry_count < MAX_RETRIES:
            try:
                await self._initialize_servers()
                try:
                    client = await self._initialize_client()
                except (ConnectionError, TimeoutError, RuntimeError) as e:
                    Console.write_exception(f"Error during client initialization:", e)
                    for i in range(15, 0, -1):
                        Console.write_stdout(f"\rRetrying in {i} seconds...   ",'')
                        await asyncio.sleep(1)
                    Console.write_stdout("\rRetrying now...           ")
                    retry_count += 1
                    continue

                retry_count = 0
                Console.write_stdout(f"Waiting for jobs...")
                while True:
                    try:
                        jobs = client.dequeue()
                        retry_count = 0
                    except requests.exceptions.RequestException as e:
                        retry_count += 1
                        if retry_count >= MAX_RETRIES:
                            Console.write_stderr(f"Failed to dequeue jobs after {MAX_RETRIES} retries.")
                            Console.write_exception(f"Exception:", e, "\nExiting...")
                            return
                        Console.write_stderr(f"Failed to dequeue jobs (attempt {retry_count}/{MAX_RETRIES}):")
                        for i in range(15, 0, -1):
                            Console.write_stdout(f"\rRetrying in {i} seconds...   ",'')
                            await asyncio.sleep(1)
                        Console.write_stdout("\rRetrying now...           ")
                        continue
                    for job in jobs:
                        Console.write_stdout(f"----------------------------------Job: {job.id}----------------------------------")
                        tool_name, arguments = self.extract_function_call_info(job.input)
                        if tool_name:
                            Console.write_stdout(f"Executing tool {job.server}/{tool_name} with arguments {arguments}")
                            try:
                                result = await self.execute_tool(job.server, tool_name, json.loads(arguments))
                            except (Exception) as e:
                                Console.write_exception(f"Error executing tool {tool_name}:", e)
                                continue

                            if isinstance(result.content, list):
                                text_parts = []
                                for item in result.content:
                                    if isinstance(item, types.TextContent):
                                        text_parts.append(item.text)
                                    elif isinstance(item, a2a_types.Part):
                                        if isinstance(item.root, a2a_types.TextPart):
                                            text_parts.append(item.root.text)
                                        else:
                                            Console.write_stdout(f"Unknown content type {type(item.root)}")
                                    else:
                                        Console.write_stdout(f"Unknown content type {type(item)}")

                            if text_parts:
                                job.output = "\n".join(text_parts)
                                Console.write_stdout(f"result: {job.output} success: {not result.isError}")
                                try:
                                    client.send_result(ToolProxyJobResult(success=result.isError, job=job))
                                except (ConnectionError, TimeoutError, RuntimeError) as e:
                                    Console.write_exception("Error sending result:", e)
                            else:
                                Console.write_stdout(f"{result}")
                    await asyncio.sleep(1)
            finally:
                Console.write_stdout("Proxy stopped")
                await self.exit_stack.aclose()
