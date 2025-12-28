import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.organization.clients import OrganizationClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.organization.endpoints import GET_ASSISTANT_LIST_V1, GET_PROJECT_LIST_V1, GET_PROJECT_V1, CREATE_PROJECT_V1, \
    UPDATE_PROJECT_V1, DELETE_PROJECT_V1, GET_PROJECT_TOKENS_V1, GET_REQUEST_DATA_V1


class TestOrganizationClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.test_clients.TestOrganizationClient
    """

    def setUp(self):
        self.client = OrganizationClient()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_assistant_list_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"assistants": [{"name": "assistant1"}, {"name": "assistant2"}]}

        result = self.client.get_assistant_list(detail="summary")

        mock_get.assert_called_once_with(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": "summary"})
        self.assertIsNotNone(result)
        self.assertEqual(len(result['assistants']), 2)
        self.assertEqual(result['assistants'][0]['name'], "assistant1")
        self.assertEqual(result['assistants'][1]['name'], "assistant2")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_assistant_list_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_assistant_list(detail="full")

        mock_get.assert_called_once_with(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": "full"})
        self.assertEqual(str(context.exception), "Unable to get assistant list: Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_list_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"projects": [{"name": "project1"}, {"name": "project2"}]}

        result = self.client.get_project_list(detail="summary")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_LIST_V1, params={"detail": "summary"})
        self.assertIsNotNone(result)
        self.assertEqual(len(result['projects']), 2)
        self.assertEqual(result['projects'][0]['name'], "project1")
        self.assertEqual(result['projects'][1]['name'], "project2")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_list_with_name(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"projects": [{"name": "specific_project"}]}

        result = self.client.get_project_list(detail="full", name="specific_project")

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_LIST_V1,
            params={"detail": "full", "name": "specific_project"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['projects']), 1)
        self.assertEqual(result['projects'][0]['name'], "specific_project")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_list_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_list(detail="full")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_LIST_V1, params={"detail": "full"})
        self.assertEqual(str(context.exception), "Unable to get project list: Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_data_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}

        result = self.client.get_project_data(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_data_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_data(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to get project data for ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_project_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}

        result = self.client.create_project(name="project1", email="admin@example.com", description="A test project")

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": "A test project"
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_project_with_usage_limit(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}

        usage_limit = {"type": "Requests", "threshold": 1000}
        result = self.client.create_project(
            name="project1", email="admin@example.com", description="A test project", usage_limit=usage_limit
        )

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": "A test project",
                "usageLimit": usage_limit
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_project_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_project(name="project1", email="admin@example.com")

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": None
            }
        )
        self.assertEqual(str(context.exception), "Unable to create project with name 'project1': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_project_success(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "updated_project"}}

        result = self.client.update_project(project_id="123", name="updated_project", description="Updated description")

        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROJECT_V1.format(id="123"),
            data={"name": "updated_project", "description": "Updated description"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "updated_project")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_project_json_decode_error(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_project(project_id="123", name="updated_project")

        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROJECT_V1.format(id="123"),
            data={"name": "updated_project", "description": None}
        )
        self.assertEqual(str(context.exception), "Unable to update project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_project_success(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.json.return_value = {"status": "deleted"}

        result = self.client.delete_project(project_id="123")

        mock_delete.assert_called_once_with(endpoint=DELETE_PROJECT_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], "deleted")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_project_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_project(project_id="123")

        mock_delete.assert_called_once_with(endpoint=DELETE_PROJECT_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to delete project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_tokens_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"tokens": ["token1", "token2"]}

        result = self.client.get_project_tokens(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_TOKENS_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(len(result['tokens']), 2)
        self.assertEqual(result['tokens'][0], "token1")
        self.assertEqual(result['tokens'][1], "token2")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_project_tokens_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_tokens(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_TOKENS_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to get tokens for project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_export_request_data_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"requests": [{"id": "1", "status": "pending"}]}

        result = self.client.export_request_data()

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": None, "status": None, "skip": 0, "count": 0}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['requests']), 1)
        self.assertEqual(result['requests'][0]['status'], "pending")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_export_request_data_with_params(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"requests": [{"id": "1", "status": "completed"}]}

        result = self.client.export_request_data(assistant_name="assistant1", status="completed", skip=10, count=5)

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": "assistant1", "status": "completed", "skip": 10, "count": 5}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['requests']), 1)
        self.assertEqual(result['requests'][0]['status'], "completed")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_export_request_data_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.export_request_data(assistant_name="assistant1")

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": "assistant1", "status": None, "skip": 0, "count": 0}
        )
        self.assertEqual(str(context.exception), "Unable to export request data: Invalid JSON response")

