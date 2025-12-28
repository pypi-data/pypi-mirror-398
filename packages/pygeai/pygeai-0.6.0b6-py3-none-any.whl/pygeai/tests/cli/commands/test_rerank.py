import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from pygeai.cli.commands.rerank import show_help, rerank_chunks, rerank_commands, rerank_chunks_options
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.cli.commands import Option


class TestRerankCommands(TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_rerank.TestRerankCommands
    """

    def setUp(self):
        # Mock Console to avoid actual stdout writes
        self.console_patch = patch('pygeai.cli.commands.rerank.Console')
        self.mock_console = self.console_patch.start()
        self.mock_console.write_stdout = MagicMock()

    def tearDown(self):
        self.console_patch.stop()

    def test_show_help(self):
        show_help()
        self.mock_console.write_stdout.assert_called_once()
        self.assertTrue(isinstance(self.mock_console.write_stdout.call_args[0][0], str))

    def test_rerank_chunks_valid_input(self):
        mock_client = MagicMock()
        mock_result = {"results": [{"index": 0, "relevance_score": 0.95}]}
        mock_client.rerank_chunks.return_value = mock_result

        with patch('pygeai.cli.commands.rerank.RerankClient', return_value=mock_client):
            option_list = [
                (Option("query", ["--query"], "string", True), "test query"),
                (Option("model", ["--model"], "string", True), "cohere/rerank-v3.5"),
                (Option("documents", ["--documents"], "string or array", True), '["doc1", "doc2"]'),
                (Option("top_n", ["--top-n"], "string", True), 2)
            ]
            rerank_chunks(option_list)
            mock_client.rerank_chunks.assert_called_once_with(
                query="test query",
                model="cohere/rerank-v3.5",
                documents=["doc1", "doc2"],
                top_n=2
            )
            self.mock_console.write_stdout.assert_called_once()
            self.assertIn("Rerank details", str(self.mock_console.write_stdout.call_args[0][0]))

    def test_rerank_chunks_valid_single_document(self):
        mock_client = MagicMock()
        mock_result = {"results": [{"index": 0, "relevance_score": 0.95}]}
        mock_client.rerank_chunks.return_value = mock_result

        with patch('pygeai.cli.commands.rerank.RerankClient', return_value=mock_client):
            option_list = [
                (Option("query", ["--query"], "string", True), "test query"),
                (Option("model", ["--model"], "string", True), "cohere/rerank-v3.5"),
                (Option("documents", ["--documents"], "string or array", True), "single doc"),
                (Option("top_n", ["--top-n"], "string", True), 1)
            ]
            rerank_chunks(option_list)
            mock_client.rerank_chunks.assert_called_once_with(
                query="test query",
                model="cohere/rerank-v3.5",
                documents=["single doc"],
                top_n=1
            )
            self.mock_console.write_stdout.assert_called_once()

    def test_rerank_chunks_missing_requirements(self):
        option_list = [
            (Option("query", ["--query"], "string", True), "test query")
            # Missing model and documents
        ]
        with self.assertRaises(MissingRequirementException) as context:
            rerank_chunks(option_list)
        self.assertIn("Cannot rerank chunks without model, query and documents", str(context.exception))

    def test_rerank_chunks_invalid_documents_json(self):
        option_list = [
            (Option("query", ["--query"], "string", True), "test query"),
            (Option("model", ["--model"], "string", True), "cohere/rerank-v3.5"),
            (Option("documents", ["--documents"], "string or array", True), "[{\"not\": \"a list}\"]"),  # Invalid JSON list
            (Option("top_n", ["--top-n"], "string", True), 3)
        ]
        with self.assertRaises(WrongArgumentError) as context:
            rerank_chunks(option_list)
        self.assertIn("Documents must be a list of strings", str(context.exception))

    def test_rerank_chunks_invalid_documents_format(self):
        option_list = [
            (Option("query", ["--query"], "string", True), "test query"),
            (Option("model", ["--model"], "string", True), "cohere/rerank-v3.5"),
            (Option("documents", ["--documents"], "string or array", True), '[{"1": "a"}'),
            (Option("top_n", ["--top-n"], "string", True), 3)
        ]
        with self.assertRaises(WrongArgumentError) as context:
            rerank_chunks(option_list)
        self.assertIn("Documents must be a list of strings", str(context.exception))

    def test_rerank_commands_structure(self):
        self.assertEqual(len(rerank_commands), 2)
        self.assertEqual(rerank_commands[0].name, "help")
        self.assertEqual(rerank_commands[1].name, "rerank")
        self.assertEqual(len(rerank_commands[1].options), len(rerank_chunks_options))
        self.assertEqual(rerank_commands[1].options[0].name, "query")
        self.assertEqual(rerank_commands[1].options[1].name, "model")
        self.assertEqual(rerank_commands[1].options[2].name, "documents")
        self.assertEqual(rerank_commands[1].options[3].name, "top_n")
