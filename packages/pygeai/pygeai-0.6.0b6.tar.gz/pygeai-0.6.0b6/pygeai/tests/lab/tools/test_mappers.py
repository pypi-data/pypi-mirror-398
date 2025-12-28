import unittest
import json
from pygeai.lab.tools.mappers import ToolMapper
from pygeai.lab.models import Tool, ToolParameter, ToolMessage, ToolList


class TestToolMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.tools.test_mappers.TestToolMapper
    """

    def test_map_parameters_success(self):
        params_data = [
            {
                "key": "param1",
                "dataType": "String",
                "description": "First parameter",
                "isRequired": True,
                "type": "config",
                "fromSecret": False,
                "value": "default1"
            },
            {
                "key": "param2",
                "dataType": "Integer",
                "description": "Second parameter",
                "isRequired": False,
                "type": "app",
                "fromSecret": True,
                "value": "default2"
            }
        ]
        result = ToolMapper._map_parameters(params_data)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], ToolParameter)
        self.assertEqual(result[0].key, "param1")
        self.assertEqual(result[0].data_type, "String")
        self.assertEqual(result[0].description, "First parameter")
        self.assertTrue(result[0].is_required)
        self.assertEqual(result[0].type, "config")
        self.assertFalse(result[0].from_secret)
        self.assertEqual(result[0].value, "default1")
        self.assertEqual(result[1].key, "param2")
        self.assertEqual(result[1].data_type, "Integer")
        self.assertEqual(result[1].type, "app")
        self.assertTrue(result[1].from_secret)

    def test_map_messages_success(self):
        messages_data = [
            {"description": "Warning message", "type": "warning"},
            {"description": "Error message", "type": "error"}
        ]
        result = ToolMapper._map_messages(messages_data)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], ToolMessage)
        self.assertEqual(result[0].description, "Warning message")
        self.assertEqual(result[0].type, "warning")
        self.assertEqual(result[1].description, "Error message")
        self.assertEqual(result[1].type, "error")

    def test_map_to_tool_success_flat_data(self):
        data = {
            "name": "TestTool",
            "description": "A test tool",
            "scope": "builtin",
            "parameters": [
                {"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True}
            ],
            "accessScope": "private",
            "publicName": "test-tool",
            "icon": "http://example.com/icon.png",
            "openApi": "http://example.com/api",
            "openApiJson": "{\"info\": {\"title\": \"Test API\"}}",
            "reportEvents": "All",
            "id": "tool-123",
            "isDraft": False,
            "messages": [{"description": "Test warning", "type": "warning"}],
            "revision": 1,
            "status": "active"
        }
        result = ToolMapper.map_to_tool(data)

        self.assertIsInstance(result, Tool)
        self.assertEqual(result.name, "TestTool")
        self.assertEqual(result.description, "A test tool")
        self.assertEqual(result.scope, "builtin")
        self.assertEqual(len(result.parameters), 1)
        self.assertIsInstance(result.parameters[0], ToolParameter)
        self.assertEqual(result.access_scope, "private")
        self.assertEqual(result.public_name, "test-tool")
        self.assertEqual(result.icon, "http://example.com/icon.png")
        self.assertEqual(result.open_api, "http://example.com/api")
        self.assertIsInstance(result.open_api_json, dict)
        self.assertEqual(result.report_events, "All")
        self.assertEqual(result.id, "tool-123")
        self.assertFalse(result.is_draft)
        self.assertEqual(len(result.messages), 1)
        self.assertIsInstance(result.messages[0], ToolMessage)
        self.assertEqual(result.revision, 1)
        self.assertEqual(result.status, "active")

    def test_map_to_tool_success_nested_data(self):
        data = {
            "tool": {
                "name": "NestedTool",
                "description": "A nested test tool",
                "scope": "external",
                "parameters": [
                    {"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True}
                ]
            }
        }
        result = ToolMapper.map_to_tool(data)

        self.assertIsInstance(result, Tool)
        self.assertEqual(result.name, "NestedTool")
        self.assertEqual(result.description, "A nested test tool")
        self.assertEqual(result.scope, "external")
        self.assertEqual(len(result.parameters), 1)

    def test_map_to_tool_invalid_open_api_json(self):
        data = {
            "name": "InvalidTool",
            "description": "A tool with invalid JSON",
            "scope": "api",
            "openApiJson": "invalid_json_string"
        }
        with self.assertRaises(ValueError) as context:
            ToolMapper.map_to_tool(data)
        self.assertEqual(str(context.exception), "open_api_json must be a valid JSON string or a dict")

    def test_map_to_tool_list_success_with_list(self):
        data = [
            {"name": "Tool1", "description": "First tool", "scope": "builtin"},
            {"name": "Tool2", "description": "Second tool", "scope": "external"}
        ]
        result = ToolMapper.map_to_tool_list(data)

        self.assertIsInstance(result, ToolList)
        self.assertEqual(len(result.tools), 2)
        self.assertIsInstance(result.tools[0], Tool)
        self.assertEqual(result.tools[0].name, "Tool1")
        self.assertEqual(result.tools[1].name, "Tool2")

    def test_map_to_tool_list_success_with_dict(self):
        data = {
            "tools": [
                {"name": "Tool1", "description": "First tool", "scope": "builtin"},
                {"name": "Tool2", "description": "Second tool", "scope": "external"}
            ]
        }
        result = ToolMapper.map_to_tool_list(data)

        self.assertIsInstance(result, ToolList)
        self.assertEqual(len(result.tools), 2)
        self.assertIsInstance(result.tools[0], Tool)
        self.assertEqual(result.tools[0].name, "Tool1")
        self.assertEqual(result.tools[1].name, "Tool2")

    def test_map_to_tool_list_empty(self):
        data = {"tools": []}
        result = ToolMapper.map_to_tool_list(data)

        self.assertIsInstance(result, ToolList)
        self.assertEqual(len(result.tools), 0)

    def test_map_to_parameter_list_success_with_list(self):
        data = [
            {"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True},
            {"key": "param2", "dataType": "Integer", "description": "Param 2", "isRequired": False}
        ]
        result = ToolMapper.map_to_parameter_list(data)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], ToolParameter)
        self.assertEqual(result[0].key, "param1")
        self.assertEqual(result[1].key, "param2")

    def test_map_to_parameter_list_success_with_dict(self):
        data = {
            "parameters": [
                {"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True}
            ]
        }
        result = ToolMapper.map_to_parameter_list(data)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], ToolParameter)
        self.assertEqual(result[0].key, "param1")

    def test_map_to_parameter_list_empty(self):
        data = {"parameters": []}
        result = ToolMapper.map_to_parameter_list(data)

        self.assertEqual(len(result), 0)

