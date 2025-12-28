import unittest
from unittest.mock import MagicMock
from pygeai.core.rerank.clients import RerankClient


class TestRerankClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.rerank.test_clients.TestRerankClient
    """

    def setUp(self):
        self.client = RerankClient()
        self.client.api_service = MagicMock()
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"results": [{"index": 0, "relevance_score": 0.95}]}

    def test_rerank_chunks_success(self):
        self.client.api_service.post.return_value = self.mock_response

        query = "What is AI?"
        model = "rerank-english-v3.0"
        documents = ["AI is artificial intelligence.", "AI stands for something else.", "Random text."]
        top_n = 2

        result = self.client.rerank_chunks(
            query=query,
            model=model,
            documents=documents,
            top_n=top_n
        )

        self.client.api_service.post.assert_called_once()
        data = self.client.api_service.post.call_args[1]['data']
        self.assertEqual(data['query'], query)
        self.assertEqual(data['model'], model)
        self.assertEqual(data['documents'], documents)
        self.assertEqual(data['top_n'], top_n)
        self.assertEqual(result, {"results": [{"index": 0, "relevance_score": 0.95}]})

    def test_rerank_chunks_default_top_n(self):
        self.client.api_service.post.return_value = self.mock_response

        query = "What is AI?"
        model = "rerank-english-v3.0"
        documents = ["AI is artificial intelligence.", "AI stands for something else."]

        result = self.client.rerank_chunks(
            query=query,
            model=model,
            documents=documents
        )

        self.client.api_service.post.assert_called_once()
        data = self.client.api_service.post.call_args[1]['data']
        self.assertEqual(data['top_n'], 3)  # Default value
        self.assertEqual(result, {"results": [{"index": 0, "relevance_score": 0.95}]})

    def test_rerank_chunks_empty_documents(self):
        self.client.api_service.post.return_value = self.mock_response

        query = "What is AI?"
        model = "rerank-english-v3.0"
        documents = []

        result = self.client.rerank_chunks(
            query=query,
            model=model,
            documents=documents
        )

        self.client.api_service.post.assert_called_once()
        data = self.client.api_service.post.call_args[1]['data']
        self.assertEqual(data['documents'], [])
        self.assertEqual(result, {"results": [{"index": 0, "relevance_score": 0.95}]})

