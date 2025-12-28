import unittest
from unittest.mock import patch, MagicMock

from pygeai.cli.commands.llm import show_help, get_provider_list, get_provider_data, get_provider_models, get_model_data, llm_commands
from pygeai.cli.commands import Option
from pygeai.core.common.exceptions import MissingRequirementException


class TestLlmCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_llm.TestLlmCommands
    """
    def setUp(self):
        self.mock_console = MagicMock()
        self.mock_client = MagicMock()
        self.mock_client.get_provider_list.return_value = {"providers": ["provider1", "provider2"]}
        self.mock_client.get_provider_data.return_value = {"name": "provider1", "details": "test_data"}
        self.mock_client.get_provider_models.return_value = {"models": ["model1", "model2"]}
        self.mock_client.get_model_data.return_value = {"name": "model1", "details": "test_data"}
        self.provider_option_list = [
            (Option("provider_name", ["--provider-name"], "", True), "provider1")
        ]
        self.model_option_list_with_name = [
            (Option("provider_name", ["--provider-name"], "", True), "provider1"),
            (Option("model_name", ["--model-name"], "", True), "model1")
        ]
        self.model_option_list_with_id = [
            (Option("provider_name", ["--provider-name"], "", True), "provider1"),
            (Option("model_id", ["--model-id"], "", True), "model1")
        ]

    @patch('pygeai.cli.commands.llm.Console.write_stdout')
    @patch('pygeai.cli.commands.llm.LlmClient')
    def test_get_provider_list(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        get_provider_list()

        mock_client_class.assert_called_once()
        self.mock_client.get_provider_list.assert_called_once()
        mock_write_stdout.assert_called_once_with("Provider list: \n{'providers': ['provider1', 'provider2']}")

    @patch('pygeai.cli.commands.llm.Console.write_stdout')
    @patch('pygeai.cli.commands.llm.LlmClient')
    def test_get_provider_data_success(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        get_provider_data(self.provider_option_list)

        mock_client_class.assert_called_once()
        self.mock_client.get_provider_data.assert_called_once_with(provider_name="provider1")
        mock_write_stdout.assert_called_once_with("Provider detail: \n{'name': 'provider1', 'details': 'test_data'}")

    def test_get_provider_data_missing_provider_name(self):
        option_list_empty = []

        with self.assertRaises(MissingRequirementException):
            get_provider_data(option_list_empty)

    @patch('pygeai.cli.commands.llm.Console.write_stdout')
    @patch('pygeai.cli.commands.llm.LlmClient')
    def test_get_provider_models_success(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        get_provider_models(self.provider_option_list)

        mock_client_class.assert_called_once()
        self.mock_client.get_provider_models.assert_called_once_with(provider_name="provider1")
        mock_write_stdout.assert_called_once_with("Provider models: \n{'models': ['model1', 'model2']}")

    def test_get_provider_models_missing_provider_name(self):
        option_list_empty = []

        with self.assertRaises(MissingRequirementException):
            get_provider_models(option_list_empty)

    @patch('pygeai.cli.commands.llm.Console.write_stdout')
    @patch('pygeai.cli.commands.llm.LlmClient')
    def test_get_model_data_success_with_model_name(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        get_model_data(self.model_option_list_with_name)

        mock_client_class.assert_called_once()
        self.mock_client.get_model_data.assert_called_once_with(provider_name="provider1", model_name="model1")
        mock_write_stdout.assert_called_once_with("Model details: \n{'name': 'model1', 'details': 'test_data'}")

    @patch('pygeai.cli.commands.llm.Console.write_stdout')
    @patch('pygeai.cli.commands.llm.LlmClient')
    def test_get_model_data_success_with_model_id(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        get_model_data(self.model_option_list_with_id)

        mock_client_class.assert_called_once()
        self.mock_client.get_model_data.assert_called_once_with(provider_name="provider1", model_name="model1")
        mock_write_stdout.assert_called_once_with("Model details: \n{'name': 'model1', 'details': 'test_data'}")

    def test_get_model_data_missing_provider_name(self):
        option_list_no_provider = [
            (Option("model_name", ["--model-name"], "", True), "model1")
        ]

        with self.assertRaises(MissingRequirementException):
            get_model_data(option_list_no_provider)

    def test_get_model_data_missing_model_info(self):
        option_list_no_model = [
            (Option("provider_name", ["--provider-name"], "", True), "provider1")
        ]

        with self.assertRaises(MissingRequirementException):
            get_model_data(option_list_no_model)

