import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.health.clients import HealthClient
from pygeai.health.endpoints import STATUS_CHECK_V1


class TestHealthClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.health.test_clients.TestHealthClient
    """

    def setUp(self):
        self.client = HealthClient()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_check_api_status_success(self, mock_get):
        expected_response = {"status": "healthy", "version": "1.0.0"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.check_api_status()

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(endpoint=STATUS_CHECK_V1)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_check_api_status_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.check_api_status()

        self.assertEqual(str(context.exception), "Unable to check API status: Invalid JSON response")
        mock_get.assert_called_once_with(endpoint=STATUS_CHECK_V1)