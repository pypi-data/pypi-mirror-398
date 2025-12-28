import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.lab.constants import VALID_SCOPES, VALID_ACCESS_SCOPES, VALID_REPORT_EVENTS
from pygeai.lab.tools.clients import ToolClient
from pygeai.lab.tools.endpoints import CREATE_TOOL_V2, LIST_TOOLS_V2, GET_TOOL_V2, UPDATE_TOOL_V2, UPSERT_TOOL_V2, \
    PUBLISH_TOOL_REVISION_V2, GET_PARAMETER_V2, SET_PARAMETER_V2, DELETE_TOOL_V2


class TestToolClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.tools.test_clients.TestToolClient
    """

    def setUp(self):
        self.project_id = "project-123"
        self.tool_client = ToolClient(api_key="test_key", base_url="https://test.url", project_id=self.project_id)
        self.tool_id = "tool-123"
        self.tool_name = "TestTool"
        self.tool_public_name = "test-tool"
        self.parameters = [{"key": "param1", "dataType": "String", "description": "Param 1", "isRequired": True}]

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_tool_success(self, mock_post):
        name = "TestTool"
        description = "A test tool"
        scope = "builtin"
        access_scope = "private"
        public_name = "test-tool"
        icon = "http://example.com/icon.png"
        open_api = "http://example.com/api"
        open_api_json = {"info": {"title": "Test API"}}
        report_events = "All"
        automatic_publish = True
        expected_response = {"id": "tool-123", "name": name}
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.create_tool(
            name=name,
            description=description,
            scope=scope,
            access_scope=access_scope,
            public_name=public_name,
            icon=icon,
            open_api=open_api,
            open_api_json=open_api_json,
            report_events=report_events,
            parameters=self.parameters,
            automatic_publish=automatic_publish
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        data = call_args[1]['data']['tool']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['description'], description)
        self.assertEqual(data['scope'], scope)
        self.assertEqual(data['accessScope'], access_scope)
        self.assertEqual(data['publicName'], public_name)
        self.assertEqual(data['icon'], icon)
        self.assertEqual(data['openApi'], open_api)
        self.assertIsInstance(data['openApiJson'], str)
        self.assertEqual(data['reportEvents'], report_events)
        self.assertEqual(data['parameters'], self.parameters)
        self.assertIn("automaticPublish=true", call_args[1]['endpoint'])
        headers = call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_create_tool_invalid_scope(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.create_tool(
                name="TestTool",
                scope="invalid_scope"
            )
        self.assertEqual(str(context.exception), f"Scope must be one of {', '.join(VALID_SCOPES)}.")

    def test_create_tool_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.create_tool(
                name="TestTool",
                access_scope="invalid_access"
            )
        self.assertEqual(str(context.exception), f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

    def test_create_tool_invalid_report_events(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.create_tool(
                name="TestTool",
                report_events="invalid_event"
            )
        self.assertEqual(str(context.exception), f"Report events must be one of {', '.join(VALID_REPORT_EVENTS)}.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_tool_json_decode_error(self, mock_post):
        name = "TestTool"
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.create_tool(
                name=name
            )

        self.assertEqual(str(context.exception), f"Unable to create tool for project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_tools_success(self, mock_get):
        expected_response = {"tools": [{"id": "tool-1", "name": "Tool1"}]}
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.list_tools(
            id="tool-1",
            count="50",
            access_scope="public",
            allow_drafts=True,
            scope="api",
            allow_external=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_TOOLS_V2,
            headers=mock_get.call_args[1]['headers'],
            params={
                "id": "tool-1",
                "count": "50",
                "accessScope": "public",
                "allowDrafts": True,
                "scope": "api",
                "allowExternal": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_list_tools_invalid_scope(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.list_tools(
                scope="invalid_scope"
            )
        self.assertEqual(str(context.exception), f"Scope must be one of {', '.join(VALID_SCOPES)}.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_tools_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.list_tools(
                scope="api"
            )

        self.assertEqual(str(context.exception), f"Unable to list tools for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_tool_success(self, mock_get):
        expected_response = {"id": self.tool_id, "name": "TestTool"}
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.get_tool(
            tool_id=self.tool_id,
            revision="1",
            version=0,
            allow_drafts=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_TOOL_V2.format(toolId=self.tool_id),
            headers=mock_get.call_args[1]['headers'],
            params={
                "revision": "1",
                "version": 0,
                "allowDrafts": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_tool_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.get_tool(
                tool_id=self.tool_id
            )

        self.assertEqual(str(context.exception), f"Unable to retrieve tool {self.tool_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_tool_success_with_id(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.tool_client.delete_tool(
            tool_id=self.tool_id
        )

        self.assertEqual(result, {})
        mock_delete.assert_called_once_with(
            endpoint=DELETE_TOOL_V2.format(toolId=self.tool_id),
            headers=mock_delete.call_args[1]['headers']
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_tool_success_with_name(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.tool_client.delete_tool(
            tool_name=self.tool_name
        )

        self.assertEqual(result, {})
        mock_delete.assert_called_once_with(
            endpoint=DELETE_TOOL_V2.format(toolId=self.tool_name),
            headers=mock_delete.call_args[1]['headers']
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_delete_tool_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.delete_tool()
        self.assertEqual(str(context.exception), "Either tool_id or tool_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_tool_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.delete_tool(
                tool_id=self.tool_id
            )

        self.assertEqual(str(context.exception), f"Unable to delete tool {self.tool_id} in project {self.project_id}: Invalid JSON response")
        mock_delete.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_tool_success(self, mock_put):
        name = "UpdatedTool"
        description = "Updated description"
        scope = "external"
        access_scope = "public"
        public_name = "updated-tool"
        icon = "http://example.com/new-icon.png"
        open_api = "http://example.com/new-api"
        open_api_json = {"info": {"title": "Updated API"}}
        report_events = "Start"
        automatic_publish = True
        upsert = False
        expected_response = {"id": self.tool_id, "name": name}
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.update_tool(
            tool_id=self.tool_id,
            name=name,
            description=description,
            scope=scope,
            access_scope=access_scope,
            public_name=public_name,
            icon=icon,
            open_api=open_api,
            open_api_json=open_api_json,
            report_events=report_events,
            parameters=self.parameters,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=f"{UPDATE_TOOL_V2.format(toolId=self.tool_id)}?automaticPublish=true",
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        call_args = mock_put.call_args
        data = call_args[1]['data']['tool']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['description'], description)
        self.assertEqual(data['scope'], scope)
        self.assertEqual(data['accessScope'], access_scope)
        self.assertEqual(data['publicName'], public_name)
        self.assertEqual(data['icon'], icon)
        self.assertEqual(data['openApi'], open_api)
        self.assertIsInstance(data['openApiJson'], str)
        self.assertEqual(data['reportEvents'], report_events)
        self.assertEqual(data['parameters'], self.parameters)
        headers = call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_tool_with_upsert(self, mock_put):
        name = "UpsertedTool"
        expected_response = {"id": self.tool_id, "name": name}
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.update_tool(
            tool_id=self.tool_id,
            name=name,
            upsert=True
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPSERT_TOOL_V2.format(toolId=self.tool_id),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )

    def test_update_tool_invalid_scope(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.update_tool(
                tool_id=self.tool_id,
                scope="invalid_scope"
            )
        self.assertEqual(str(context.exception), f"Scope must be one of {', '.join(VALID_SCOPES)}.")

    def test_update_tool_invalid_access_scope(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.update_tool(
                tool_id=self.tool_id,
                access_scope="invalid_access"
            )
        self.assertEqual(str(context.exception), f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")

    def test_update_tool_invalid_report_events(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.update_tool(
                tool_id=self.tool_id,
                report_events="invalid_event"
            )
        self.assertEqual(str(context.exception), f"Report events must be one of {', '.join(VALID_REPORT_EVENTS)}.")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_tool_json_decode_error(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.update_tool(
                tool_id=self.tool_id,
                name="UpdatedTool"
            )

        self.assertEqual(str(context.exception), f"Unable to update tool {self.tool_id} in project {self.project_id}: Invalid JSON response")
        mock_put.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_tool_revision_success(self, mock_post):
        revision = "2"
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.publish_tool_revision(
            tool_id=self.tool_id,
            revision=revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_TOOL_REVISION_V2.format(toolId=self.tool_id),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": revision}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_tool_revision_json_decode_error(self, mock_post):
        revision = "2"
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.publish_tool_revision(
                tool_id=self.tool_id,
                revision=revision
            )

        self.assertEqual(str(context.exception), f"Unable to publish revision {revision} for tool {self.tool_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_parameter_success_with_id(self, mock_get):
        expected_response = {"parameters": [{"key": "param1"}]}
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.get_parameter(
            tool_id=self.tool_id,
            revision="1",
            version=0,
            allow_drafts=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_PARAMETER_V2.format(toolPublicName=self.tool_id),
            headers=mock_get.call_args[1]['headers'],
            params={
                "revision": "1",
                "version": 0,
                "allowDrafts": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_parameter_success_with_public_name(self, mock_get):
        expected_response = {"parameters": [{"key": "param1"}]}
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = expected_response

        result = self.tool_client.get_parameter(
            tool_public_name=self.tool_public_name,
            revision="1",
            version=0,
            allow_drafts=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_PARAMETER_V2.format(toolPublicName=self.tool_public_name),
            headers=mock_get.call_args[1]['headers'],
            params={
                "revision": "1",
                "version": 0,
                "allowDrafts": True
            }
        )

    def test_get_parameter_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.get_parameter()
        self.assertEqual(str(context.exception), "Either tool_id or tool_public_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_parameter_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.get_parameter(
                tool_id=self.tool_id
            )

        self.assertEqual(str(context.exception), f"Unable to retrieve parameters for tool {self.tool_id} in project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_parameter_success_with_id(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 204

        result = self.tool_client.set_parameter(
            tool_id=self.tool_id,
            parameters=self.parameters
        )

        self.assertEqual(result, {})
        mock_post.assert_called_once_with(
            endpoint=SET_PARAMETER_V2.format(toolPublicName=self.tool_id),
            headers=mock_post.call_args[1]['headers'],
            data={"parameterDefinition": {"parameters": self.parameters}}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_parameter_success_with_public_name(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 204

        result = self.tool_client.set_parameter(
            tool_public_name=self.tool_public_name,
            parameters=self.parameters
        )

        self.assertEqual(result, {})
        mock_post.assert_called_once_with(
            endpoint=SET_PARAMETER_V2.format(toolPublicName=self.tool_public_name),
            headers=mock_post.call_args[1]['headers'],
            data={"parameterDefinition": {"parameters": self.parameters}}
        )

    def test_set_parameter_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.tool_client.set_parameter(parameters=self.parameters)
        self.assertEqual(str(context.exception), "Either tool_id or tool_public_name must be provided.")

        with self.assertRaises(ValueError) as context:
            self.tool_client.set_parameter(tool_id=self.tool_id, parameters=[])
        self.assertEqual(str(context.exception), "Parameters list must be provided and non-empty.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_set_parameter_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.tool_client.set_parameter(
                tool_id=self.tool_id,
                parameters=self.parameters
            )

        self.assertEqual(str(context.exception), f"Unable to set parameters for tool {self.tool_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()
