import unittest
from unittest.mock import patch, Mock
from pygeai.cli.commands.gam import (
    show_help,
    generate_signin_url,
    get_access_token,
    get_user_info,
    refresh_access_token,
    get_authentication_types,
    Option
)
from pygeai.core.common.exceptions import MissingRequirementException


class TestGamCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_gam.TestGamCommands
    """
    def setUp(self):
        # Helper to create Option objects for testing
        self.mock_option = lambda name, value: (Option(name, [f"--{name}"], f"Description for {name}", True), value)

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.build_help_text')
    def test_show_help(self, mock_build_help, mock_write_stdout):
        mock_help_text = "Mocked help text"
        mock_build_help.return_value = mock_help_text

        show_help()

        mock_build_help.assert_called_once()
        mock_write_stdout.assert_called_once_with(mock_help_text)

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_generate_signin_url_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.generate_signing_url.return_value = "https://example.com/signin"
        option_list = [
            self.mock_option("client_id", "client123"),
            self.mock_option("redirect_uri", "https://callback.com"),
            self.mock_option("scope", "gam_user_data"),
            self.mock_option("state", "random_state"),
            self.mock_option("response_type", "code")
        ]

        generate_signin_url(option_list)

        mock_instance.generate_signing_url.assert_called_once_with(
            client_id="client123",
            redirect_uri="https://callback.com",
            scope="gam_user_data",
            state="random_state",
            response_type="code"
        )
        mock_write_stdout.assert_called_once_with("GAM Signin URL: \nhttps://example.com/signin")

    def test_generate_signin_url_missing_required_fields(self):
        option_list = [
            self.mock_option("client_id", "client123"),
            self.mock_option("redirect_uri", "https://callback.com")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            generate_signin_url(option_list)

        self.assertEqual(str(context.exception), "client_id, redirect_uri, and state are required for generating signin URL")

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_get_access_token_success_with_client_credentials(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_access_token.return_value = {"access_token": "token123"}
        option_list = [
            self.mock_option("client_id", "client123"),
            self.mock_option("client_secret", "secret456"),
            self.mock_option("grant_type", "password"),
            self.mock_option("authentication_type_name", "local"),
            self.mock_option("scope", "gam_user_data")
        ]

        get_access_token(option_list)

        mock_instance.get_access_token.assert_called_once_with(
            client_id="client123",
            client_secret="secret456",
            grant_type="password",
            authentication_type_name="local",
            scope="gam_user_data",
            username=None,
            password=None,
            initial_properties=None,
            repository=None,
            request_token_type="OAuth"
        )
        mock_write_stdout.assert_called_once_with("GAM Access Token: \n{'access_token': 'token123'}")

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_get_access_token_success_with_username_password(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_access_token.return_value = {"access_token": "token123"}
        option_list = [
            self.mock_option("username", "user1"),
            self.mock_option("password", "pass123"),
            self.mock_option("grant_type", "password"),
            self.mock_option("authentication_type_name", "local"),
            self.mock_option("scope", "gam_user_data")
        ]

        get_access_token(option_list)

        mock_instance.get_access_token.assert_called_once_with(
            client_id=None,
            client_secret=None,
            grant_type="password",
            authentication_type_name="local",
            scope="gam_user_data",
            username="user1",
            password="pass123",
            initial_properties=None,
            repository=None,
            request_token_type="OAuth"
        )
        mock_write_stdout.assert_called_once_with("GAM Access Token: \n{'access_token': 'token123'}")

    def test_get_access_token_missing_credentials(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_access_token(option_list)

        self.assertEqual(str(context.exception), "Cannot get access token without specifying valid credentials")

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_get_user_info_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_user_info.return_value = {"user": "user1", "email": "user1@example.com"}
        option_list = [self.mock_option("access_token", "token123")]

        get_user_info(option_list)

        mock_instance.get_user_info.assert_called_once_with(access_token="token123")
        mock_write_stdout.assert_called_once_with("GAM User info: \n{'user': 'user1', 'email': 'user1@example.com'}")

    def test_get_user_info_missing_access_token(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_user_info(option_list)

        self.assertEqual(str(context.exception), "Cannot get user info without the access token")

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_refresh_access_token_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.refresh_access_token.return_value = {"access_token": "new_token123"}
        option_list = [
            self.mock_option("client_id", "client123"),
            self.mock_option("client_secret", "secret456"),
            self.mock_option("grant_type", "refresh_token"),
            self.mock_option("refresh_token", "refresh_token789")
        ]

        refresh_access_token(option_list)

        mock_instance.refresh_access_token.assert_called_once_with(
            client_id="client123",
            client_secret="secret456",
            grant_type="refresh_token",
            refresh_token="refresh_token789"
        )
        mock_write_stdout.assert_called_once_with("GAM Access Token: \n{'access_token': 'new_token123'}")

    def test_refresh_access_token_missing_credentials(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            refresh_access_token(option_list)

        self.assertEqual(str(context.exception), "Cannot refresh access token without specifying valid credentials")

    @patch('pygeai.cli.commands.gam.Console.write_stdout')
    @patch('pygeai.cli.commands.gam.GAMClient')
    def test_get_authentication_types_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_authentication_types.return_value = {"types": ["local", "oauth"]}

        get_authentication_types()

        mock_instance.get_authentication_types.assert_called_once()
        mock_write_stdout.assert_called_once_with("GAM Authentication Types: \n{'types': ['local', 'oauth']}")

