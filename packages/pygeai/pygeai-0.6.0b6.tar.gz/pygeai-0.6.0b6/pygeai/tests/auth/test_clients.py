import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError

from pygeai.auth.clients import AuthClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestAuthClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.auth.test_clients.TestAuthClient
    """

    def setUp(self):
        self.client = AuthClient()
        self.mock_response = MagicMock()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_oauth2_access_token_success(self, mock_get):
        self.mock_response.json.return_value = {"access_token": "token-123", "token_type": "Bearer"}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_oauth2_access_token(
            client_id="client-123",
            username="user@example.com",
            password="password123"
        )
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['client_id'], "client-123")
        self.assertEqual(call_args[1]['params']['username'], "user@example.com")
        self.assertEqual(call_args[1]['params']['password'], "password123")
        self.assertEqual(call_args[1]['params']['scope'], "gam_user_data gam_user_roles")
        self.assertEqual(result, {"access_token": "token-123", "token_type": "Bearer"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_oauth2_access_token_custom_scope(self, mock_get):
        self.mock_response.json.return_value = {"access_token": "token-123"}
        mock_get.return_value = self.mock_response
        
        result = self.client.get_oauth2_access_token(
            client_id="client-123",
            username="user@example.com",
            password="password123",
            scope="custom_scope"
        )
        
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['params']['scope'], "custom_scope")

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_oauth2_access_token_json_decode_error(self, mock_get):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 401
        self.mock_response.text = "Invalid credentials"
        mock_get.return_value = self.mock_response
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_oauth2_access_token(
                client_id="client-123",
                username="user@example.com",
                password="wrong"
            )
        self.assertIn("Unable to  obtain Oauth2 access token", str(context.exception))

    @patch.object(AuthClient, 'api_service', create=True)
    def test_get_user_profile_information_success(self, mock_api_service):
        self.mock_response.json.return_value = {
            "user_id": "user-123",
            "email": "user@example.com",
            "name": "Test User"
        }
        mock_api_service.get.return_value = self.mock_response
        mock_api_service.token = None
        
        client = AuthClient()
        client.api_service = mock_api_service
        result = client.get_user_profile_information("access-token-123")
        
        mock_api_service.get.assert_called_once()
        self.assertEqual(result, {
            "user_id": "user-123",
            "email": "user@example.com",
            "name": "Test User"
        })

    @patch.object(AuthClient, 'api_service', create=True)
    def test_get_user_profile_information_json_decode_error(self, mock_api_service):
        self.mock_response.json.side_effect = JSONDecodeError("error", "doc", 0)
        self.mock_response.status_code = 401
        self.mock_response.text = "Invalid token"
        mock_api_service.get.return_value = self.mock_response
        mock_api_service.token = None
        
        client = AuthClient()
        client.api_service = mock_api_service
        
        with self.assertRaises(InvalidAPIResponseException) as context:
            client.get_user_profile_information("invalid-token")
        self.assertIn("Unable to retrieve user profile information", str(context.exception))


if __name__ == '__main__':
    unittest.main()
