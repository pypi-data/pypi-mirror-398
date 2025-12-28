import unittest
from unittest.mock import patch, MagicMock
import json
from json import JSONDecodeError
from pygeai.core.secrets.clients import SecretClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestSecretClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.secrets.test_clients.TestSecretClient
    """
    def setUp(self):
        self.secret_client = SecretClient(api_key="test_key", base_url="test_url", alias="test_alias")
        self.mock_api_service = MagicMock()
        self.secret_client.api_service = self.mock_api_service

    def test_list_secrets_success(self):
        expected_response = {"secrets": [{"id": "1", "name": "secret1"}]}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.get.return_value = mock_response

        result = self.secret_client.list_secrets(name="secret1", start=0, count=5)

        self.assertEqual(result, expected_response)
        self.mock_api_service.get.assert_called_once()
        call_args = self.mock_api_service.get.call_args
        self.assertEqual(call_args[1]['params']['name'], "secret1")
        self.assertEqual(call_args[1]['params']['start'], 0)
        self.assertEqual(call_args[1]['params']['count'], 5)

    def test_list_secrets_json_decode_error(self):
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.get.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.list_secrets()

        self.assertIn("Unable to list secrets with params", str(context.exception))
        self.mock_api_service.get.assert_called_once()

    def test_get_secret_success(self):
        secret_id = "secret-123"
        expected_response = {"id": "secret-123", "name": "test-secret"}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.get.return_value = mock_response

        result = self.secret_client.get_secret(secret_id)

        self.assertEqual(result, expected_response)
        self.mock_api_service.get.assert_called_once()

    def test_get_secret_json_decode_error(self):
        secret_id = "secret-123"
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.get.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.get_secret(secret_id)

        self.assertIn(f"Unable to get secret with ID '{secret_id}'", str(context.exception))
        self.mock_api_service.get.assert_called_once()

    def test_get_secret_invalid_id(self):
        with self.assertRaises(ValueError) as context:
            self.secret_client.get_secret("")
        self.assertEqual(str(context.exception), "secret_id must be provided and non-empty.")

    def test_create_secret_success(self):
        name = "test-secret"
        secret_string = "secret-value"
        description = "A test secret"
        expected_response = {"id": "secret-123", "name": name}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.post.return_value = mock_response

        result = self.secret_client.create_secret(name, secret_string, description)

        self.assertEqual(result, expected_response)
        self.mock_api_service.post.assert_called_once()
        call_args = self.mock_api_service.post.call_args
        data = call_args[1]['data']['secretDefinition']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['secretString'], secret_string)
        self.assertEqual(data['description'], description)

    def test_create_secret_json_decode_error(self):
        name = "test-secret"
        secret_string = "secret-value"
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.post.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.create_secret(name, secret_string)

        self.assertIn(f"Unable to create secret with name '{name}'", str(context.exception))
        self.mock_api_service.post.assert_called_once()

    def test_create_secret_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.secret_client.create_secret("", "secret-value")
        self.assertEqual(str(context.exception), "name and secret_string must be provided and non-empty.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.create_secret("test-secret", "")
        self.assertEqual(str(context.exception), "name and secret_string must be provided and non-empty.")

    def test_update_secret_success(self):
        secret_id = "secret-123"
        name = "updated-secret"
        secret_string = "updated-value"
        description = "Updated description"
        expected_response = {"id": secret_id, "name": name}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.put.return_value = mock_response

        result = self.secret_client.update_secret(secret_id, name, secret_string, description)

        self.assertEqual(result, expected_response)
        self.mock_api_service.put.assert_called_once()
        call_args = self.mock_api_service.put.call_args
        data = call_args[1]['data']['secretDefinition']
        self.assertEqual(data['name'], name)
        self.assertEqual(data['secretString'], secret_string)
        self.assertEqual(data['description'], description)

    def test_update_secret_json_decode_error(self):
        secret_id = "secret-123"
        name = "updated-secret"
        secret_string = "updated-value"
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.put.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.update_secret(secret_id, name, secret_string)

        self.assertIn(f"Unable to update secret with ID '{secret_id}'", str(context.exception))
        self.mock_api_service.put.assert_called_once()

    def test_update_secret_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.secret_client.update_secret("", "name", "value")
        self.assertEqual(str(context.exception), "secret_id, name, and secret_string must be provided and non-empty.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.update_secret("id", "", "value")
        self.assertEqual(str(context.exception), "secret_id, name, and secret_string must be provided and non-empty.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.update_secret("id", "name", "")
        self.assertEqual(str(context.exception), "secret_id, name, and secret_string must be provided and non-empty.")

    def test_set_secret_accesses_success(self):
        secret_id = "secret-123"
        access_list = [
            {"accessLevel": "write", "principalType": "service"},
            {"accessLevel": "read", "principalType": "user"}
        ]
        expected_response = {"status": "success"}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.post.return_value = mock_response

        result = self.secret_client.set_secret_accesses(secret_id, access_list)

        self.assertEqual(result, expected_response)
        self.mock_api_service.post.assert_called_once()
        call_args = self.mock_api_service.post.call_args
        data = call_args[1]['data']['secretDefinition']
        self.assertEqual(data['accessList'], access_list)

    def test_set_secret_accesses_json_decode_error(self):
        secret_id = "secret-123"
        access_list = [
            {"accessLevel": "write", "principalType": "service"}
        ]
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.post.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.set_secret_accesses(secret_id, access_list)

        self.assertIn(f"Unable to set accesses for secret with ID '{secret_id}'", str(context.exception))
        self.mock_api_service.post.assert_called_once()

    def test_set_secret_accesses_invalid_input(self):
        with self.assertRaises(ValueError) as context:
            self.secret_client.set_secret_accesses("", [{"accessLevel": "write", "principalType": "service"}])
        self.assertEqual(str(context.exception), "secret_id must be provided and non-empty.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.set_secret_accesses("id", [])
        self.assertEqual(str(context.exception), "access_list must be provided and non-empty.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.set_secret_accesses("id", [{"accessLevel": "write"}])
        self.assertEqual(str(context.exception), "Each access entry must contain 'accessLevel' and 'principalType'.")

        with self.assertRaises(ValueError) as context:
            self.secret_client.set_secret_accesses("id", [{"accessLevel": "", "principalType": "service"}])
        self.assertEqual(str(context.exception), "'accessLevel' and 'principalType' must be non-empty strings.")

    def test_get_secret_accesses_success(self):
        secret_id = "secret-123"
        expected_response = {"accesses": [{"accessLevel": "write", "principalType": "service"}]}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.get.return_value = mock_response

        result = self.secret_client.get_secret_accesses(secret_id)

        self.assertEqual(result, expected_response)
        self.mock_api_service.get.assert_called_once()

    def test_get_secret_accesses_json_decode_error(self):
        secret_id = "secret-123"
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        mock_response.status_code = 500
        self.mock_api_service.get.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.secret_client.get_secret_accesses(secret_id)

        self.assertIn(f"Unable to get accesses for secret with ID '{secret_id}'", str(context.exception))
        self.mock_api_service.get.assert_called_once()

    def test_get_secret_accesses_invalid_id(self):
        with self.assertRaises(ValueError) as context:
            self.secret_client.get_secret_accesses("")
        self.assertEqual(str(context.exception), "secret_id must be provided and non-empty.")

