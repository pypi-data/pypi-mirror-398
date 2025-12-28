import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import json
import uuid
from pygeai.proxy.managers import ServerManager
from pygeai.proxy.config import ProxySettingsManager
from pygeai.proxy.clients import ProxyClient, ToolProxyData, ToolProxyJobResult
from pygeai.proxy.tool import ProxiedTool


class TestServerManager(unittest.IsolatedAsyncioTestCase):
    """
    python -m unittest pygeai.tests.proxy.test_managers.TestServerManager
    """

    def setUp(self):
        """Set up test fixtures."""
        self.servers_cfg = [
            {
                "name": "test_mcp_server",
                "type": "mcp",
                "command": "test_command",
                "args": ["arg1", "arg2"]
            },
            {
                "name": "test_a2a_server",
                "type": "a2a",
                "url": "https://test.a2a.com",
                "headers": {"Authorization": "Bearer token"}
            }
        ]
        self.settings = ProxySettingsManager()
        self.manager = ServerManager(self.servers_cfg, self.settings)

    def test_initialization(self):
        """Test manager initialization."""
        self.assertEqual(self.manager.servers_cfg, self.servers_cfg)
        self.assertEqual(self.manager.settings, self.settings)
        self.assertEqual(self.manager.servers, {})
        self.assertEqual(self.manager.tools, {})

    @patch('pygeai.proxy.managers.MCPServer')
    @patch('pygeai.proxy.managers.A2AServer')
    @patch('pygeai.proxy.managers.Console')
    async def test_initialize_servers_success(self, mock_console, mock_a2a_server_class, mock_mcp_server_class):
        """Test successful server initialization."""
        # Mock server instances
        mock_mcp_server = AsyncMock()
        mock_mcp_server.name = "test_mcp_server"
        mock_mcp_server.exit_stack = AsyncMock()
        mock_mcp_server.list_tools.return_value = []
        
        mock_a2a_server = AsyncMock()
        mock_a2a_server.name = "test_a2a_server"
        mock_a2a_server.exit_stack = AsyncMock()
        mock_a2a_server.list_tools.return_value = []
        
        mock_mcp_server_class.return_value = mock_mcp_server
        mock_a2a_server_class.return_value = mock_a2a_server
        
        await self.manager._initialize_servers()
        
        # Verify servers were created and initialized
        mock_mcp_server_class.assert_called_once_with(
            "test_mcp_server", self.servers_cfg[0], self.settings
        )
        mock_a2a_server_class.assert_called_once_with(
            "test_a2a_server", self.servers_cfg[1], self.settings
        )
        
        mock_mcp_server.initialize.assert_called_once()
        mock_a2a_server.initialize.assert_called_once()

    @patch('pygeai.proxy.managers.MCPServer')
    @patch('pygeai.proxy.managers.Console')
    async def test_initialize_servers_invalid_type(self, mock_console, mock_mcp_server_class):
        """Test server initialization with invalid server type."""
        invalid_config = [{"name": "invalid_server", "type": "invalid_type"}]
        manager = ServerManager(invalid_config, self.settings)
        
        with self.assertRaises(ValueError, msg="Invalid server type: invalid_type"):
            await manager._initialize_servers()

    @patch('pygeai.proxy.managers.MCPServer')
    @patch('pygeai.proxy.managers.Console')
    async def test_initialize_servers_initialization_error(self, mock_console, mock_mcp_server_class):
        """Test server initialization error."""
        mock_server = AsyncMock()
        mock_server.name = "test_server"
        mock_server.initialize.side_effect = Exception("Initialization failed")
        mock_mcp_server_class.return_value = mock_server
        
        with self.assertRaises(Exception):
            await self.manager._initialize_servers()

    @patch('pygeai.proxy.managers.ProxyClient')
    @patch('pygeai.proxy.managers.Console')
    async def test_initialize_client_success(self, mock_console, mock_client_class):
        """Test successful client initialization."""
        # Mock settings methods
        self.settings.get_current_alias = Mock(return_value="default")
        self.settings.get_api_key = Mock(return_value="test_api_key")
        self.settings.get_base_url = Mock(return_value="https://api.example.com")
        self.settings.get_proxy_id = Mock(return_value=uuid.uuid4())
        self.settings.get_proxy_name = Mock(return_value="Test Proxy")
        self.settings.get_proxy_description = Mock(return_value="Test Description")
        self.settings.get_proxy_affinity = Mock(return_value=uuid.uuid4())
        
        # Mock client
        mock_client = Mock()
        mock_client.register.return_value = {"status": "success"}
        mock_client_class.return_value = mock_client
        
        # Add some tools to the manager
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        self.manager.tools["test_server__test_tool"] = tool
        
        result = await self.manager._initialize_client()
        
        self.assertEqual(result, mock_client)
        mock_client.register.assert_called_once()

    @patch('pygeai.proxy.managers.ProxyClient')
    @patch('pygeai.proxy.managers.Console')
    async def test_initialize_client_connection_error(self, mock_console, mock_client_class):
        """Test client initialization with connection error."""
        # Mock settings methods
        self.settings.get_current_alias = Mock(return_value="default")
        self.settings.get_api_key = Mock(return_value="test_api_key")
        self.settings.get_base_url = Mock(return_value="https://api.example.com")
        self.settings.get_proxy_id = Mock(return_value=uuid.uuid4())
        
        # Mock client to raise connection error
        mock_client = Mock()
        mock_client.register.side_effect = ConnectionError("Connection failed")
        mock_client_class.return_value = mock_client
        
        with self.assertRaises(ConnectionError):
            await self.manager._initialize_client()

    async def test_execute_tool_server_not_found(self):
        """Test executing tool with non-existent server."""
        with self.assertRaises(RuntimeError, msg="Server non_existent not found"):
            await self.manager.execute_tool("non_existent", "test_tool", {})

    async def test_execute_tool_tool_not_found(self):
        """Test executing non-existent tool."""
        # Add a server but no tools
        self.manager.servers["test_server"] = Mock()
        
        with self.assertRaises(RuntimeError, msg="Tool non_existent not found"):
            await self.manager.execute_tool("test_server", "non_existent", {})

    @patch('pygeai.proxy.managers.Console')
    async def test_execute_tool_success(self, mock_console):
        """Test successful tool execution."""
        # Mock server
        mock_server = AsyncMock()
        mock_server.execute_tool.return_value = "success"
        self.manager.servers["test_server"] = mock_server
        
        # Add tool
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        self.manager.tools["test_server__test_tool"] = tool
        
        result = await self.manager.execute_tool("test_server", "test_server__test_tool", {"param": "value"})
        
        self.assertEqual(result, "success")
        mock_server.execute_tool.assert_called_once_with("test_tool", {"param": "value"}, 2, 1.0)

    @patch('pygeai.proxy.managers.Console')
    async def test_execute_tool_with_custom_retries(self, mock_console):
        """Test tool execution with custom retry parameters."""
        mock_server = AsyncMock()
        mock_server.execute_tool.return_value = "success"
        self.manager.servers["test_server"] = mock_server
        
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        self.manager.tools["test_server__test_tool"] = tool
        
        await self.manager.execute_tool("test_server", "test_server__test_tool", {}, retries=5, delay=2.0)
        
        mock_server.execute_tool.assert_called_once_with("test_tool", {}, 5, 2.0)

    @patch('pygeai.proxy.managers.Console')
    async def test_execute_tool_execution_error(self, mock_console):
        """Test tool execution with error."""
        mock_server = AsyncMock()
        mock_server.execute_tool.side_effect = RuntimeError("Tool execution failed")
        self.manager.servers["test_server"] = mock_server
        
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        self.manager.tools["test_server__test_tool"] = tool
        
        with self.assertRaises(Exception, msg="Failed to execute tool test_server__test_tool on server test_server: Tool execution failed"):
            await self.manager.execute_tool("test_server", "test_server__test_tool", {})

    def test_extract_function_call_info_success(self):
        """Test successful function call info extraction."""
        function_call_json = json.dumps({
            "function": {
                "name": "test_function",
                "arguments": '{"param": "value"}'
            }
        })
        
        name, arguments = self.manager.extract_function_call_info(function_call_json)
        
        self.assertEqual(name, "test_function")
        self.assertEqual(arguments, '{"param": "value"}')

    def test_extract_function_call_info_invalid_json(self):
        """Test function call info extraction with invalid JSON."""
        name, arguments = self.manager.extract_function_call_info("invalid json")
        
        self.assertIsNone(name)
        self.assertIsNone(arguments)

    def test_extract_function_call_info_missing_keys(self):
        """Test function call info extraction with missing keys."""
        function_call_json = json.dumps({"other_key": "value"})
        
        name, arguments = self.manager.extract_function_call_info(function_call_json)
        
        self.assertIsNone(name)
        self.assertIsNone(arguments)

    @patch('pygeai.proxy.managers.ServerManager._initialize_servers')
    @patch('pygeai.proxy.managers.ServerManager._initialize_client')
    @patch('pygeai.proxy.managers.Console')
    async def test_start_success(self, mock_console, mock_init_client, mock_init_servers):
        """Test successful start method."""
        # Mock client
        mock_client = Mock()
        mock_client.dequeue.return_value = []
        mock_init_client.return_value = mock_client
        
        # Mock settings
        self.settings.get_current_alias = Mock(return_value="default")
        self.settings.get_proxy_id = Mock(return_value=uuid.uuid4())
        
        # Create a task to run start method
        task = asyncio.create_task(self.manager.start())
        
        # Let it run for a short time
        await asyncio.sleep(0.1)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify initialization was called
        mock_init_servers.assert_called_once()
        mock_init_client.assert_called_once()

    @patch('pygeai.proxy.managers.ServerManager._initialize_servers')
    @patch('pygeai.proxy.managers.ServerManager._initialize_client')
    @patch('pygeai.proxy.managers.Console')
    async def test_start_client_initialization_error(self, mock_console, mock_init_client, mock_init_servers):
        """Test start method with client initialization error."""
        mock_init_client.side_effect = ConnectionError("Connection failed")
        
        # Create a task to run start method
        task = asyncio.create_task(self.manager.start())
        
        # Let it run for a short time
        await asyncio.sleep(0.1)
        
        # Cancel the task
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verify initialization was called
        mock_init_servers.assert_called_once()
        mock_init_client.assert_called_once()


if __name__ == '__main__':
    unittest.main() 