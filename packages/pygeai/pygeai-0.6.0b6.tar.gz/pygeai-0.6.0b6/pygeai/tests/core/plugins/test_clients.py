import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError

from pygeai.core.plugins.clients import PluginClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestPluginClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.plugins.test_clients.TestPluginClient
    """

    def setUp(self):
        self.client = PluginClient()
        self.mock_response = MagicMock()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_assistants_success(self, mock_get):
        self.mock_response.json.return_value = {
            "assistants": [
                {"id": "assistant-1", "name": "Assistant 1"},
                {"id": "assistant-2", "name": "Assistant 2"}
            ]
        }
        mock_get.return_value = self.mock_response
        
        result = self.client.list_assistants(
            organization_id="org-123",
            project_id="proj-456"
        )
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['organization'], "org-123")
        self.assertEqual(call_args[1]['params']['project'], "proj-456")
        self.assertEqual(len(result["assistants"]), 2)

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_assistants_empty(self, mock_get):
        self.mock_response.json.return_value = {"assistants": []}
        mock_get.return_value = self.mock_response
        
        result = self.client.list_assistants(
            organization_id="org-123",
            project_id="proj-456"
        )
        
        self.assertEqual(result["assistants"], [])

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_assistants_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 500
        self.mock_response.text = "Internal server error"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_assistants("org-123", "proj-456")
        self.assertIn("Unable to list assistants for organization org-123 and project proj-456", str(context.exception))


if __name__ == '__main__':
    unittest.main()
