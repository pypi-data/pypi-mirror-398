import unittest
import json
from pygeai.proxy.tool import ProxiedTool


class TestProxiedTool(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_tool.TestProxiedTool
    """

    def setUp(self):
        """Set up test fixtures."""
        self.server_name = "test_server"
        self.tool_name = "test_tool"
        self.description = "Test tool description"
        self.public_prefix = "public.prefix"
        self.input_schema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        }
        self.tool = ProxiedTool(
            server_name=self.server_name,
            name=self.tool_name,
            description=self.description,
            public_prefix=self.public_prefix,
            input_schema=self.input_schema
        )

    def test_initialization(self):
        """Test tool initialization."""
        self.assertEqual(self.tool.server_name, self.server_name)
        self.assertEqual(self.tool.name, self.tool_name)
        self.assertEqual(self.tool.description, self.description)
        self.assertEqual(self.tool.public_prefix, self.public_prefix)
        self.assertEqual(self.tool.input_schema, self.input_schema)

    def test_get_openai_compatible_name(self):
        """Test OpenAI compatible name generation."""
        # Test basic name
        self.assertEqual(self.tool.openai_compatible_name, "test_tool")
        
        # Test name with spaces
        tool_with_spaces = ProxiedTool(
            server_name="server",
            name="tool with spaces",
            description="desc",
            public_prefix="prefix",
            input_schema={}
        )
        self.assertEqual(tool_with_spaces.openai_compatible_name, "tool_with_spaces")
        
        # Test name with special characters
        tool_with_special = ProxiedTool(
            server_name="server",
            name="tool@#$%^&*()",
            description="desc",
            public_prefix="prefix",
            input_schema={}
        )
        self.assertEqual(tool_with_special.openai_compatible_name, "tool_________")

    def test_get_full_name(self):
        """Test getting full tool name."""
        expected = f"{self.server_name}__{self.tool.openai_compatible_name}"
        self.assertEqual(self.tool.get_full_name(), expected)

    def test_is_public(self):
        """Test public tool detection."""
        # Tool with public prefix should be public
        self.assertTrue(self.tool.is_public())
        
        # Tool without public prefix should not be public
        private_tool = ProxiedTool(
            server_name="server",
            name="tool",
            description="desc",
            public_prefix=None,
            input_schema={}
        )
        self.assertFalse(private_tool.is_public())

    def test_get_public_name_with_server_in_prefix(self):
        """Test getting public name when server name is in prefix."""
        tool = ProxiedTool(
            server_name="server",
            name="tool",
            description="desc",
            public_prefix="server.prefix",
            input_schema={}
        )
        expected = "server.prefix.tool"
        self.assertEqual(tool.get_public_name(), expected)

    def test_get_public_name_with_server_not_in_prefix(self):
        """Test getting public name when server name is not in prefix."""
        expected = f"{self.public_prefix}.{self.tool.get_full_name()}"
        self.assertEqual(self.tool.get_public_name(), expected)

    def test_get_public_name_private_tool(self):
        """Test getting public name for private tool."""
        private_tool = ProxiedTool(
            server_name="server",
            name="tool",
            description="desc",
            public_prefix=None,
            input_schema={}
        )
        # Should not raise exception, but behavior depends on implementation
        try:
            result = private_tool.get_public_name()
            # If it doesn't raise, it should return some value
            self.assertIsInstance(result, str)
        except AttributeError:
            # If it raises AttributeError, that's also acceptable
            pass

    def test_format_for_llm(self):
        """Test formatting tool for LLM."""
        result = self.tool.format_for_llm()
        
        # Parse the JSON result
        parsed = json.loads(result)
        
        # Check structure
        self.assertIn('type', parsed)
        self.assertEqual(parsed['type'], 'function')
        
        self.assertIn('function', parsed)
        function_data = parsed['function']
        
        self.assertIn('name', function_data)
        self.assertEqual(function_data['name'], self.tool.get_full_name())
        
        self.assertIn('description', function_data)
        self.assertEqual(function_data['description'], self.description)
        
        self.assertIn('parameters', function_data)
        self.assertEqual(function_data['parameters'], self.input_schema)

    def test_format_for_llm_with_empty_description(self):
        """Test formatting tool for LLM with empty description."""
        tool_empty_desc = ProxiedTool(
            server_name="server",
            name="tool",
            description="",
            public_prefix="prefix",
            input_schema={}
        )
        
        result = tool_empty_desc.format_for_llm()
        parsed = json.loads(result)
        
        self.assertEqual(parsed['function']['description'], '')

    def test_format_for_llm_with_none_description(self):
        """Test formatting tool for LLM with None description."""
        tool_none_desc = ProxiedTool(
            server_name="server",
            name="tool",
            description=None,
            public_prefix="prefix",
            input_schema={}
        )
        
        result = tool_none_desc.format_for_llm()
        parsed = json.loads(result)
        
        self.assertEqual(parsed['function']['description'], '')


if __name__ == '__main__':
    unittest.main() 