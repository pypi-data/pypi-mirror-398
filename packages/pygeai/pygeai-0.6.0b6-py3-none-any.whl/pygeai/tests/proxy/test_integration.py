import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
import uuid
import json
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from pygeai.proxy.config import ProxySettingsManager
from pygeai.proxy.tool import ProxiedTool
from pygeai.proxy.clients import ProxyClient, ToolProxyData, ToolProxyJob, ToolProxyJobResult
from pygeai.proxy.managers import ServerManager
from pygeai.proxy.servers import A2AServer, MCPServer
from types import SimpleNamespace


class TestProxyIntegration(unittest.IsolatedAsyncioTestCase):
    """
    python -m unittest pygeai.tests.proxy.test_integration.TestProxyIntegration
    """

    def setUp(self):
        """Set up test fixtures."""
        self.settings = ProxySettingsManager()
        self.test_uuid = uuid.uuid4()
        self.test_affinity = uuid.uuid4()

    def test_tool_to_proxy_data_integration(self):
        """Test integration between ProxiedTool and ToolProxyData."""
        # Create a tool
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool description",
            public_prefix="public.prefix",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "number"}
                }
            }
        )
        
        # Create proxy data with the tool
        proxy_data = ToolProxyData(
            id=self.test_uuid,
            name="Test Proxy",
            description="Test Description",
            affinity=self.test_affinity,
            tools=[tool]
        )
        
        # Convert to dictionary
        data_dict = proxy_data.to_dict()
        
        # Verify the tool data is correctly included
        self.assertEqual(len(data_dict["tools"]), 1)
        tool_dict = data_dict["tools"][0]
        
        self.assertEqual(tool_dict["name"], "test_server__test_tool")
        self.assertEqual(tool_dict["publicName"], "public.prefix.test_server__test_tool")
        self.assertEqual(tool_dict["server"], "test_server")
        self.assertEqual(tool_dict["description"], "Test tool description")
        
        # Verify the input schema is correctly formatted
        input_schema = json.loads(tool_dict["inputSchema"])
        self.assertEqual(input_schema["function"]["parameters"]["type"], "object")

    def test_job_processing_integration(self):
        """Test integration between job creation and result processing."""
        # Create a job
        job = ToolProxyJob(
            id=uuid.uuid4(),
            proxy_id=self.test_uuid,
            proxy_status="active",
            job_status="pending",
            input=json.dumps({
                "function": {
                    "name": "test_server__test_tool",
                    "arguments": '{"param1": "value1", "param2": 42}'
                }
            }),
            server="test_server"
        )
        
        # Simulate job execution
        job.job_status = "completed"
        job.output = "Execution completed successfully"
        
        # Create result
        result = ToolProxyJobResult(success=True, job=job)
        result_dict = result.to_dict()
        
        # Verify result structure
        self.assertTrue(result_dict["success"])
        self.assertEqual(result_dict["job"]["jobStatus"], "completed")
        self.assertEqual(result_dict["job"]["output"], "Execution completed successfully")

    @patch('pygeai.proxy.managers.ProxyClient')
    async def test_server_manager_integration(self, mock_client_class):
        """Test integration between ServerManager and its components."""
        # Configure settings
        self.settings.set_proxy_id(self.test_uuid)
        self.settings.set_proxy_name("Test Proxy")
        self.settings.set_proxy_description("Test Description")
        self.settings.set_proxy_affinity(self.test_affinity)
        
        # Mock settings methods
        self.settings.get_current_alias = Mock(return_value="default")
        self.settings.get_api_key = Mock(return_value="test_api_key")
        self.settings.get_base_url = Mock(return_value="https://api.example.com")
        
        # Create server configuration
        servers_cfg = [
            {
                "name": "test_mcp_server",
                "type": "mcp",
                "command": "test_command",
                "args": ["arg1", "arg2"]
            }
        ]
        
        # Create manager
        manager = ServerManager(servers_cfg, self.settings)
        
        # Add a mock server and tool
        tool = ProxiedTool(
            server_name="test_mcp_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        manager.tools["test_mcp_server__test_tool"] = tool
        
        # Mock client
        mock_client = Mock()
        mock_client.register.return_value = {"status": "registered"}
        mock_client_class.return_value = mock_client
        
        # Add a mock server and tool
        mock_server = AsyncMock()
        mock_server.name = "test_mcp_server"
        mock_server.exit_stack = AsyncMock()
        mock_server.list_tools.return_value = []
        
        manager.servers["test_mcp_server"] = mock_server
        
        # Test client initialization
        client = await manager._initialize_client()
        
        # Verifica que el mock fue llamado
        mock_client.register.assert_called_once()
        self.assertEqual(client, mock_client)
        
        # Verify registration data - get the actual arguments passed to register
        call_args = mock_client.register.call_args
        self.assertIsNotNone(call_args)
        
        # The register method is called with keyword arguments, so we need to access them properly
        proxy_data = call_args.kwargs.get('proxy_data')
        self.assertIsNotNone(proxy_data)
        self.assertEqual(proxy_data.id, self.test_uuid)
        self.assertEqual(proxy_data.name, "Test Proxy")
        self.assertEqual(proxy_data.description, "Test Description")
        self.assertEqual(proxy_data.affinity, self.test_affinity)
        self.assertEqual(len(proxy_data.tools), 1)

    @patch('pygeai.proxy.managers.Console')
    async def test_tool_execution_integration(self, mock_console):
        """Test integration of tool execution flow."""
        # Create manager
        servers_cfg = []
        manager = ServerManager(servers_cfg, self.settings)
        
        # Add mock server
        mock_server = AsyncMock()
        mock_server.execute_tool.return_value = "execution_result"
        manager.servers["test_server"] = mock_server
        
        # Add tool
        tool = ProxiedTool(
            server_name="test_server",
            name="test_tool",
            description="Test tool",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        manager.tools["test_server__test_tool"] = tool
        
        # Test tool execution
        result = await manager.execute_tool("test_server", "test_server__test_tool", {"param": "value"})
        
        # Verify execution
        self.assertEqual(result, "execution_result")
        mock_server.execute_tool.assert_called_once_with("test_tool", {"param": "value"}, 2, 1.0)

    def test_function_call_parsing_integration(self):
        """Test integration of function call parsing."""
        # Create manager
        servers_cfg = []
        manager = ServerManager(servers_cfg, self.settings)
        
        # Test function call parsing
        function_call_json = json.dumps({
            "function": {
                "name": "test_server__test_tool",
                "arguments": '{"param1": "value1", "param2": 42}'
            }
        })
        
        name, arguments = manager.extract_function_call_info(function_call_json)
        
        # Verify parsing
        self.assertEqual(name, "test_server__test_tool")
        self.assertEqual(arguments, '{"param1": "value1", "param2": 42}')
        
        # Test with parsed arguments
        parsed_args = json.loads(arguments)
        self.assertEqual(parsed_args["param1"], "value1")
        self.assertEqual(parsed_args["param2"], 42)

    @patch('pygeai.proxy.clients.requests.Session')
    def test_client_request_integration(self, mock_session):
        """Test integration of client request handling."""
        # Create client
        client = ProxyClient("test_api_key", "https://api.example.com", self.test_uuid)
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "data": "test_data"}
        mock_response.raise_for_status.return_value = None
        mock_session.return_value.request.return_value = mock_response
        
        # Test request
        result = client._make_request("GET", "/test")
        
        # Verify request
        self.assertEqual(result, {"status": "success", "data": "test_data"})
        mock_session.return_value.request.assert_called_once()

    def test_settings_integration(self):
        """Test integration of settings management."""
        # Set various settings
        self.settings.set_proxy_id(self.test_uuid)
        self.settings.set_proxy_name("Test Proxy")
        self.settings.set_proxy_description("Test Description")
        self.settings.set_proxy_affinity(self.test_affinity)
        
        # Get complete configuration
        config = self.settings.get_proxy_config()
        
        # Verify configuration
        expected = {
            "id": str(self.test_uuid),
            "name": "Test Proxy",
            "description": "Test Description",
            "affinity": str(self.test_affinity)
        }
        self.assertEqual(config, expected)

    def test_tool_formatting_integration(self):
        """Test integration of tool formatting for different scenarios."""
        # Test public tool
        public_tool = ProxiedTool(
            server_name="test_server",
            name="public_tool",
            description="Public tool description",
            public_prefix="public.prefix",
            input_schema={"type": "object"}
        )
        
        # Test private tool
        private_tool = ProxiedTool(
            server_name="test_server",
            name="private_tool",
            description="Private tool description",
            public_prefix=None,
            input_schema={"type": "object"}
        )
        
        # Create proxy data with both tools
        proxy_data = ToolProxyData(
            id=self.test_uuid,
            name="Test Proxy",
            tools=[public_tool, private_tool]
        )
        
        # Convert to dictionary
        data_dict = proxy_data.to_dict()
        
        # Verify public tool has publicName
        public_tool_dict = data_dict["tools"][0]
        self.assertIn("publicName", public_tool_dict)
        self.assertEqual(public_tool_dict["publicName"], "public.prefix.test_server__public_tool")
        
        # Verify private tool doesn't have publicName
        private_tool_dict = data_dict["tools"][1]
        self.assertNotIn("publicName", private_tool_dict)


if __name__ == '__main__':
    unittest.main() 