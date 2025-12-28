import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError
from pygeai.assistant.clients import AssistantClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestAssistantClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.test_clients.TestAssistantClient
    """
    def setUp(self):
        with patch('pygeai.core.base.clients.BaseClient.__init__', return_value=None):
            self.client = AssistantClient()
        self.mock_response = MagicMock()
        self.client.api_service = MagicMock()
        self.assistant_id = "test_id"
        self.assistant_name = "Test Assistant"
        self.request_id = "req_123"

    def test_get_assistant_data_successful_json_response(self):
        detail = "summary"
        expected_response = {"id": self.assistant_id, "name": "Test Assistant"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_assistant_data(self.assistant_id, detail)

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_assistant_data_json_decode_error(self):
        detail = "full"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Invalid JSON response"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_assistant_data(self.assistant_id, detail)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to get assistant data", str(context.exception))

    def test_create_assistant_successful_json_response(self):
        assistant_type = "text"
        name = "New Assistant"
        prompt = "Help with text"
        expected_response = {"id": "new_id", "name": name}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.create_assistant(assistant_type, name, prompt)

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_create_assistant_json_decode_error(self):
        assistant_type = "chat"
        name = "Chat Assistant"
        prompt = "Chat prompt"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error in response"
        self.mock_response.status_code = 500
        self.client.api_service.post.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_assistant(assistant_type, name, prompt)

        self.client.api_service.post.assert_called_once()
        self.assertIn("Unable to create assistant", str(context.exception))

    def test_update_assistant_successful_json_response(self):
        status = 1
        action = "save"
        expected_response = {"id": self.assistant_id, "status": status}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_assistant(self.assistant_id, status, action)

        self.client.api_service.put.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_update_assistant_json_decode_error(self):
        status = 2
        action = "saveNewRevision"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Update failed"
        self.mock_response.status_code = 500
        self.client.api_service.put.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_assistant(self.assistant_id, status, action)

        self.client.api_service.put.assert_called_once()
        self.assertIn("Unable to update assistant", str(context.exception))

    def test_delete_assistant_successful_json_response(self):
        expected_response = {"message": "Assistant deleted"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_assistant(self.assistant_id)

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_delete_assistant_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Delete error"
        self.mock_response.status_code = 500
        self.client.api_service.delete.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_assistant(self.assistant_id)

        self.client.api_service.delete.assert_called_once()
        self.assertIn("Unable to delete assistant", str(context.exception))

    def test_send_chat_request_successful_json_response(self):
        messages = [{"role": "user", "content": "Hello"}]
        expected_response = {"response": "Hi there!"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.send_chat_request(self.assistant_name, messages)

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_send_chat_request_json_decode_error(self):
        messages = [{"role": "user", "content": "Hello"}]
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Chat error"
        self.mock_response.status_code = 500
        self.client.api_service.post.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.send_chat_request(self.assistant_name, messages)

        self.client.api_service.post.assert_called_once()
        self.assertIn("Unable to send chat request", str(context.exception))

    def test_get_request_status_successful_json_response(self):
        expected_response = {"status": "completed"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_request_status(self.request_id)

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_request_status_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Status error"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_request_status(self.request_id)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to get request status", str(context.exception))

    def test_cancel_request_successful_json_response(self):
        expected_response = {"message": "Request cancelled"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.cancel_request(self.request_id)

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_cancel_request_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Cancel error"
        self.mock_response.status_code = 500
        self.client.api_service.post.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.cancel_request(self.request_id)

        self.client.api_service.post.assert_called_once()
        self.assertIn("Unable to cancel request", str(context.exception))

