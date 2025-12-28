import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError
from pygeai.core.llm.clients import LlmClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestLlmClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.llm.test_clients.TestLlmClient
    """
    def setUp(self):
        with patch('pygeai.core.base.clients.BaseClient.__init__', return_value=None):
            self.client = LlmClient()
        self.mock_response = MagicMock()
        self.client.api_service = MagicMock()
        self.provider_name = "test-provider"
        self.model_name = "test-model"
        self.model_id = "test-model-id"

    def test_get_provider_list_success(self):
        expected_response = {"providers": [{"name": "provider1"}, {"name": "provider2"}]}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_provider_list()

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_provider_list_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error text"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_provider_list()

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to obtain provider list", str(context.exception))

    def test_get_provider_data_success(self):
        expected_response = {"name": self.provider_name, "details": "test details"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_provider_data(provider_name=self.provider_name)

        self.client.api_service.get.assert_called_once()
        endpoint = self.client.api_service.get.call_args[1]['endpoint']
        self.assertIn(self.provider_name, endpoint)
        self.assertEqual(result, expected_response)

    def test_get_provider_data_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error text"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_provider_data(provider_name=self.provider_name)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to obtain provider data", str(context.exception))

    def test_get_provider_models_success(self):
        expected_response = {"models": [{"name": "model1"}, {"name": "model2"}]}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_provider_models(provider_name=self.provider_name)

        self.client.api_service.get.assert_called_once()
        endpoint = self.client.api_service.get.call_args[1]['endpoint']
        self.assertIn(self.provider_name, endpoint)
        self.assertEqual(result, expected_response)

    def test_get_provider_models_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error text"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_provider_models(provider_name=self.provider_name)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to obtain provider models", str(context.exception))

    def test_get_model_data_with_model_name_success(self):
        expected_response = {"name": self.model_name, "provider": self.provider_name}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_model_data(
            provider_name=self.provider_name,
            model_name=self.model_name
        )

        self.client.api_service.get.assert_called_once()
        endpoint = self.client.api_service.get.call_args[1]['endpoint']
        self.assertIn(self.provider_name, endpoint)
        self.assertIn(self.model_name, endpoint)
        self.assertEqual(result, expected_response)

    def test_get_model_data_with_model_id_success(self):
        expected_response = {"id": self.model_id, "provider": self.provider_name}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_model_data(
            provider_name=self.provider_name,
            model_id=self.model_id
        )

        self.client.api_service.get.assert_called_once()
        endpoint = self.client.api_service.get.call_args[1]['endpoint']
        self.assertIn(self.provider_name, endpoint)
        self.assertIn(self.model_id, endpoint)
        self.assertEqual(result, expected_response)

    def test_get_model_data_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error text"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_model_data(
                provider_name=self.provider_name,
                model_name=self.model_name
            )

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to obtain model data", str(context.exception))

