import unittest
from unittest.mock import patch, MagicMock

from pygeai.cli.commands.embeddings import show_help, generate_embeddings, embeddings_commands, generate_embeddings_options
from pygeai.cli.commands import Option, Command
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError


class TestEmbeddingsCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_embeddings.TestEmbeddingsCommands
    """
    def setUp(self):
        self.mock_console = MagicMock()
        self.mock_client = MagicMock()
        self.mock_client.generate_embeddings.return_value = {"embeddings": "test_data"}
        self.option_list_with_all_params = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("input", ["--input"], "", True), "input1"),
            (Option("input", ["--input"], "", True), "input2"),
            (Option("encoding_format", ["--encoding-format"], "", True), "float"),
            (Option("dimensions", ["--dimensions"], "", True), "512"),
            (Option("user", ["--user"], "", True), "user123"),
            (Option("input_type", ["--input-type"], "", True), "text"),
            (Option("timeout", ["--timeout"], "", True), "30"),
            (Option("cache", ["--cache"], "", True), "1")
        ]
        self.option_list_minimal = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("input", ["--input"], "", True), "input1")
        ]

    @patch('pygeai.cli.commands.embeddings.Console.write_stdout')
    @patch('pygeai.cli.commands.embeddings.EmbeddingsClient')
    def test_generate_embeddings_success_all_params(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        generate_embeddings(self.option_list_with_all_params)

        mock_client_class.assert_called_once()
        self.mock_client.generate_embeddings.assert_called_once_with(
            input_list=["input1", "input2"],
            model="test-model",
            encoding_format="float",
            dimensions="512",
            user="user123",
            input_type="text",
            timeout="30",
            cache=True
        )
        mock_write_stdout.assert_called_once_with("Embeddings detail: \n{'embeddings': 'test_data'}")

    @patch('pygeai.cli.commands.embeddings.Console.write_stdout')
    @patch('pygeai.cli.commands.embeddings.EmbeddingsClient')
    def test_generate_embeddings_success_minimal_params(self, mock_client_class, mock_write_stdout):
        mock_client_class.return_value = self.mock_client

        generate_embeddings(self.option_list_minimal)

        mock_client_class.assert_called_once()
        self.mock_client.generate_embeddings.assert_called_once_with(
            input_list=["input1"],
            model="test-model",
            encoding_format=None,
            dimensions=None,
            user=None,
            input_type=None,
            timeout=None,
            cache=None
        )
        mock_write_stdout.assert_called_once_with("Embeddings detail: \n{'embeddings': 'test_data'}")

    def test_generate_embeddings_missing_model(self):
        option_list_no_model = [
            (Option("input", ["--input"], "", True), "input1")
        ]

        with self.assertRaises(MissingRequirementException):
            generate_embeddings(option_list_no_model)

    def test_generate_embeddings_missing_input(self):
        option_list_no_input = [
            (Option("model", ["--model"], "", True), "test-model")
        ]

        with self.assertRaises(MissingRequirementException):
            generate_embeddings(option_list_no_input)

    def test_generate_embeddings_invalid_cache_value(self):
        option_list_invalid_cache = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("input", ["--input"], "", True), "input1"),
            (Option("cache", ["--cache"], "", True), "invalid")
        ]

        with self.assertRaises(WrongArgumentError):
            generate_embeddings(option_list_invalid_cache)

    def test_generate_embeddings_cache_out_of_range(self):
        option_list_cache_out_of_range = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("input", ["--input"], "", True), "input1"),
            (Option("cache", ["--cache"], "", True), "2")
        ]

        with self.assertRaises(WrongArgumentError):
            generate_embeddings(option_list_cache_out_of_range)


