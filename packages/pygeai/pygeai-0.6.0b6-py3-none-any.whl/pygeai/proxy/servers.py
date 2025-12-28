"""Server module for managing MCP server connections and tool execution."""
import asyncio
import os
import shutil
import httpx
from types import SimpleNamespace
from uuid import uuid4
from contextlib import AsyncExitStack
from abc import ABC, abstractmethod
from typing import Any, Dict
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from pygeai.proxy.tool import ProxiedTool
from pygeai.proxy.config import ProxySettingsManager
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    AgentCard, SendMessageRequest, MessageSendParams,
    Message, Task, SendMessageSuccessResponse
)

from pygeai.core.utils.console import Console

class ToolServer(ABC):
    """
    Interface for tool servers like MCP and A2A.

    Subclasses must implement methods to initialize the server,
    list available tools, and execute a tool.
    """
   
    def __init__(self, sever_name: str, config: Dict[str, Any], settings: ProxySettingsManager):
        """
        Initialize the server.
        
        :param sever_name: str - Name of the server
        :param config: Dict[str, Any] - Server configuration
        :param settings: ProxySettingsManager - Proxy settings manager
        """
        self.config = config
        self.settings = settings
        self.name: str = sever_name
        self.public_prefix: str | None = None
        self.exit_stack: AsyncExitStack = AsyncExitStack()

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the server connection.

        :return: None
        :raises: ValueError - If the command is invalid
        :raises: RuntimeError - If server initialization fails
        :raises: ConnectionError - If connection to server fails
        """
        pass

    @abstractmethod
    async def list_tools(self) -> list[ProxiedTool]:
        """
        List available tools from the server.

        :return: list[Tool] - List of available tools
        :raises: RuntimeError - If server is not initialized
        """
        pass

    @abstractmethod
    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """
        Execute a tool with retry mechanism.

        :param tool_name: str - Name of the tool to execute
        :param arguments: dict[str, Any] - Tool arguments
        :param retries: int - Number of retry attempts
        :param delay: float - Delay between retries in seconds
        :return: Any - Tool execution result
        :raises: RuntimeError - If server is not initialized
        :raises: ConnectionError - If connection to server fails
        :raises: ValueError - If tool execution fails
        """
        pass

class A2AServer(ToolServer):
    """
    Manages A2A server connections and tool execution.
    """
    def __init__(self, sever_name: str, config: Dict[str, Any], settings: ProxySettingsManager):
        super().__init__(sever_name, config, settings)
        self.client: A2AClient | None = None
        self.card_url: str = self.config["url"]
        self.agent_card: AgentCard | None = None
        self.httpx_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """
        Initialize the A2A client from the agent card and convert agent skills into tools
        compatible with OpenAI function call format.
        """
        try:
            self.httpx_client = httpx.AsyncClient(timeout=60.0)
            self.public_prefix = self.config.get("public_prefix")
            headers = self.config.get("headers")
            if headers:
                self.httpx_client.headers.update(headers)
            resolver = A2ACardResolver(httpx_client=self.httpx_client, base_url=self.card_url)
            self.agent_card = await resolver.get_agent_card()
            self.client = A2AClient(httpx_client=self.httpx_client, agent_card=self.agent_card)

        except httpx.HTTPError as e:
            Console.write_exception(f"HTTP error initializing A2A server {self.name}:", e)
            raise ConnectionError(f"Failed to connect to A2A server: {e}") from e
        except ValueError as e:
            Console.write_exception(f"Invalid configuration for A2A server {self.name}:" ,e)
            raise ValueError(f"Invalid A2A server configuration: {e}") from e
        except RuntimeError as e:
            Console.write_exception(f"Runtime error initializing A2A server {self.name}:", e)
            raise RuntimeError(f"A2A server initialization failed: {e}") from e
        
    async def list_tools(self) -> list[ProxiedTool]:
        if not self.client:
            raise RuntimeError(f"Server {self.name} not initialized")
        input_schema = {
            "type": "object",
            "properties": {
                "input-text": {
                    "type": "string",
                    "description": "The input text to send to the agent for execution."
                }
            },
            "required": ["input-text"]
        }
        tools = []
        for skill in self.agent_card.skills:
            tools.append(ProxiedTool(self.name, skill.id, skill.description, self.public_prefix, input_schema))
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        Console.write_stdout(f"Executing {tool_name}...")
        message_id = uuid4().hex
        send_message_payload: dict[str, Any] = {
            'message': {
                'role': 'user',
                'parts': [
                    {
                        'kind': 'text',
                        'text': (
                            'Use your skill:' + tool_name +
                            ' with this input:' + arguments["input-text"]
                        )
                    }
                ],
                'messageId': message_id,
            },
        }
        request = SendMessageRequest(
            id=message_id,
            params=MessageSendParams(**send_message_payload)
        )

        response = await self.client.send_message(request)
        result = []
        if isinstance(response.root, SendMessageSuccessResponse):
            if isinstance(response.root.result, Message):
                result = response.root.result.parts
            elif isinstance(response.root, Task):
                Console.write_stderr(f"Task response: {response.root.result}")
            else:
                Console.write_stderr(f"Unknown response type: {type(response.root)}")
                raise ValueError(f"Unknown response type: {type(response.root)}")
        
        return SimpleNamespace(content=result, isError=False)

class MCPServer(ToolServer):
    """
    Manages MCP server connections and tool execution.

    :param sever_name: str - Name of the server
    :param config: Dict[str, Any] - Server configuration
    :param settings: ProxySettingsManager - Proxy settings manager
    """
    def __init__(self, sever_name: str, config: Dict[str, Any], settings: ProxySettingsManager):
        super().__init__(sever_name, config, settings)
        self.public_prefix = config.get("public_prefix")
        self.stdio_context: Any | None = None
        self.session: ClientSession | None = None

    async def initialize(self) -> None:
        self.public_prefix = self.config.get("public_prefix")
        transport = self.config.get("transport") or (
            "sse" if ("uri" in self.config  or "url" in self.config) else "stdio"
        )
        try:
            if transport == "stdio":
                command = (
                    shutil.which("npx")
                    if self.config["command"] == "npx"
                    else self.config["command"]
                )
                if command is None:
                    raise ValueError("The command must be una cadena válida")

                server_params = StdioServerParameters(
                    command=command,
                    args=self.config["args"],
                    env=(
                        {**os.environ, **self.config["env"]}
                        if self.config.get("env")
                        else None
                    ),
                )
            
                stdio_transport = await self.exit_stack.enter_async_context(
                    stdio_client(server_params)
                )
                read, write = stdio_transport
            elif transport == "sse":
                uri = self.config.get("uri", self.config["url"])
                if not uri:
                    raise ValueError("Missing 'uri' for sse transport")
                try:
                    sse_transport = await self.exit_stack.enter_async_context(
                        sse_client(
                            url=uri,
                            headers=self.config.get("headers")
                        )
                    )
                    read, write = sse_transport
                except httpx.HTTPStatusError as e:
                    Console.write_exception(f"HTTP error initializing MCP server {self.name}:", e)
            else:
                raise ValueError(f"Unsupported transport: {transport}")
            
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.session = session
        except (RuntimeError, ConnectionError, ValueError) as e:
            Console.write_exception(f"Error initializing server {self.name}:", e)
            raise

    async def list_tools(self) -> list[ProxiedTool]:
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(
                        ProxiedTool(
                            self.name,
                            tool.name,
                            tool.description,
                            self.public_prefix,
                            tool.inputSchema
                        )
                    )

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
                Console.write_stdout(f"Executing {tool_name}...")
                result = await self.session.call_tool(tool_name, arguments)
                return result

            except (RuntimeError, ConnectionError, ValueError) as e:
                attempt += 1
                Console.write_exception(
                    "Error executing tool:", e, f". Attempt {attempt} of {retries}.\n"
                )
                if attempt < retries:
                    Console.write_stdout(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    Console.write_stdout("Max retries reached. Failing.")
                    raise