import unittest
from unittest.mock import patch, MagicMock
from pygeai.core.embeddings.clients import EmbeddingsClient


class TestEmbeddingsClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.embeddings.test_clients.TestEmbeddingsClient
    """

    def setUp(self):
        self.client = EmbeddingsClient()
        self.input_list = ["test input"]
        self.model = "test-model"

    def test_generate_embeddings_basic(self):
        with patch('pygeai.core.base.clients.BaseClient.api_service') as mock_api_service:
            mock_response = MagicMock()
            mock_response.json.return_value = {"model": self.model, "data": [{"embedding": [0.1, 0.2]}]}
            mock_api_service.post.return_value = mock_response

            result = self.client.generate_embeddings(input_list=self.input_list, model=self.model)

            mock_api_service.post.assert_called_once()
            self.assertEqual(result["model"], self.model)
            self.assertIn("data", result)

    def test_generate_embeddings_with_all_parameters(self):
        with patch('pygeai.core.base.clients.BaseClient.api_service') as mock_api_service:
            mock_response = MagicMock()
            mock_response.json.return_value = {"model": self.model, "data": [{"embedding": [0.1, 0.2]}]}
            mock_api_service.post.return_value = mock_response

            result = self.client.generate_embeddings(
                input_list=self.input_list,
                model=self.model,
                encoding_format="float",
                dimensions=128,
                user="test-user",
                input_type="text",
                timeout=30,
                cache=True
            )

            mock_api_service.post.assert_called_once()
            call_args = mock_api_service.post.call_args
            self.assertEqual(call_args[1]["data"]["model"], self.model)
            self.assertEqual(call_args[1]["data"]["input"], self.input_list)
            self.assertEqual(call_args[1]["data"]["encoding_format"], "float")
            self.assertEqual(call_args[1]["data"]["dimensions"], 128)
            self.assertEqual(call_args[1]["data"]["user"], "test-user")
            self.assertEqual(call_args[1]["data"]["input_type"], "text")
            self.assertEqual(call_args[1]["data"]["timeout"], 30)
            self.assertEqual(call_args[1]["headers"]["X-Saia-Cache-Enabled"], "true")
            self.assertEqual(result["model"], self.model)
            self.assertIn("data", result)

    def test_generate_embeddings_without_optional_parameters(self):
        with patch('pygeai.core.base.clients.BaseClient.api_service') as mock_api_service:
            mock_response = MagicMock()
            mock_response.json.return_value = {"model": self.model, "data": [{"embedding": [0.1, 0.2]}]}
            mock_api_service.post.return_value = mock_response

            result = self.client.generate_embeddings(
                input_list=self.input_list,
                model=self.model,
                cache=False
            )

            mock_api_service.post.assert_called_once()
            call_args = mock_api_service.post.call_args
            self.assertEqual(call_args[1]["data"]["model"], self.model)
            self.assertEqual(call_args[1]["data"]["input"], self.input_list)
            self.assertNotIn("encoding_format", call_args[1]["data"])
            self.assertNotIn("dimensions", call_args[1]["data"])
            self.assertNotIn("user", call_args[1]["data"])
            self.assertNotIn("input_type", call_args[1]["data"])
            self.assertNotIn("timeout", call_args[1]["data"])
            self.assertNotIn("X-Saia-Cache-Enabled", call_args[1]["headers"])
            self.assertEqual(result["model"], self.model)
            self.assertIn("data", result)
