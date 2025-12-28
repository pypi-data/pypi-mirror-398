import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError

from pygeai.admin.clients import AdminClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestAdminClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.admin.test_clients.TestAdminClient
    """

    def setUp(self):
        self.client = AdminClient()
        self.mock_response = MagicMock()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_validate_api_token_success(self, mock_get):
        self.mock_response.json.return_value = {"organizationId": "org-123", "projectId": "proj-123"}
        mock_get.return_value = self.mock_response
        
        result = self.client.validate_api_token()
        
        mock_get.assert_called_once()
        self.assertEqual(result, {"organizationId": "org-123", "projectId": "proj-123"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_validate_api_token_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 500
        self.mock_response.text = "Invalid response"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.validate_api_token()
        self.assertIn("Unable to validate API token", str(context.exception))

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_authorized_organizations_success(self, mock_get):
        self.mock_response.json.return_value = {"organizations": ["org1", "org2"]}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_authorized_organizations()
        
        mock_get.assert_called_once()
        self.assertEqual(result, {"organizations": ["org1", "org2"]})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_authorized_organizations_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 500
        self.mock_response.text = "Invalid response"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_authorized_organizations()
        self.assertIn("Unable to retrieve authorized organizations", str(context.exception))

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_authorized_projects_by_organization_success(self, mock_get):
        self.mock_response.json.return_value = {"projects": ["proj1", "proj2"]}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_authorized_projects_by_organization("org-123")
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['organization'], "org-123")
        self.assertEqual(result, {"projects": ["proj1", "proj2"]})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_authorized_projects_by_organization_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 500
        self.mock_response.text = "Invalid response"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_authorized_projects_by_organization("org-123")
        self.assertIn("Unable to retrieve authorized projects for organization", str(context.exception))

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_project_visibility_success(self, mock_get):
        self.mock_response.json.return_value = {}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_project_visibility(
            organization="org-123",
            project="proj-456",
            access_token="token-789"
        )
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['organization'], "org-123")
        self.assertEqual(call_args[1]['params']['project'], "proj-456")
        self.assertEqual(call_args[1]['params']['accessToken'], "token-789")
        self.assertEqual(result, {})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_project_visibility_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 403
        self.mock_response.text = "Forbidden"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_visibility("org-123", "proj-456", "token-789")
        self.assertIn("Unable to retrieve project visibility", str(context.exception))

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_project_api_token_success(self, mock_get):
        self.mock_response.json.return_value = {"apiToken": "api-token-123"}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_project_api_token(
            organization="org-123",
            project="proj-456",
            access_token="token-789"
        )
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['organization'], "org-123")
        self.assertEqual(call_args[1]['params']['project'], "proj-456")
        self.assertEqual(call_args[1]['params']['accessToken'], "token-789")
        self.assertEqual(result, {"apiToken": "api-token-123"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_project_api_token_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 401
        self.mock_response.text = "Unauthorized"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_api_token("org-123", "proj-456", "token-789")
        self.assertIn("Unable to retrieve project API token", str(context.exception))


if __name__ == '__main__':
    unittest.main()
