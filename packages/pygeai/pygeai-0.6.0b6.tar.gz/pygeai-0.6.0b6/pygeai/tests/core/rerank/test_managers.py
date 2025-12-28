import unittest
from unittest.mock import MagicMock, patch
from pygeai.core.rerank.managers import RerankManager
from pygeai.core.rerank.models import RerankResponse, RerankResult, RerankMetaData, ApiVersion, BilledUnits
from pygeai.core.common.exceptions import APIError


class TestRerankManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.rerank.test_managers.TestRerankManager
    """
    def setUp(self):
        self.manager = RerankManager(api_key="test_key", base_url="test_url", alias="test_alias")
        self.manager._RerankManager__client = MagicMock()

    def test_rerank_chunks_success(self):
        mock_response = {
            "id": "00a3bfe3-67e6-4aab-a19a-592bda2920a7",
            "results": [
                {"index": 2, "relevance_score": 0.8963332},
                {"index": 0, "relevance_score": 0.17393301},
                {"index": 1, "relevance_score": 0.08103136}
            ],
            "meta": {
                "api_version": {"version": "2"},
                "billed_units": {"search_units": 1}
            }
        }
        self.manager._RerankManager__client.rerank_chunks.return_value = mock_response
        with patch('pygeai.core.rerank.managers.RerankResponseMapper.map_to_rerank_response') as mock_mapper:
            mock_mapper.return_value = RerankResponse(
                id="00a3bfe3-67e6-4aab-a19a-592bda2920a7",
                results=[
                    RerankResult(index=2, relevance_score=0.8963332),
                    RerankResult(index=0, relevance_score=0.17393301),
                    RerankResult(index=1, relevance_score=0.08103136)
                ],
                meta=RerankMetaData(
                    api_version=ApiVersion(version="2"),
                    billed_units=BilledUnits(search_units=1)
                )
            )

            result = self.manager.rerank_chunks(
                query="What is the Capital of the United States?",
                model="cohere/rerank-v3.5",
                documents=[
                    "Carson City is the capital city of the American state of Nevada.",
                    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
                    "Washington, D.C. is the capital of the United States.",
                    "Capital punishment has existed in the United States since before it was a country."
                ],
                top_n=3
            )

            self.assertIsInstance(result, RerankResponse)
            self.assertEqual(result.id, "00a3bfe3-67e6-4aab-a19a-592bda2920a7")
            self.assertEqual(len(result.results), 3)
            self.assertEqual(result.results[0].index, 2)
            self.assertEqual(result.results[0].relevance_score, 0.8963332)
            self.manager._RerankManager__client.rerank_chunks.assert_called_once_with(
                query="What is the Capital of the United States?",
                model="cohere/rerank-v3.5",
                documents=[
                    "Carson City is the capital city of the American state of Nevada.",
                    "The Commonwealth of the Northern Mariana Islands is a group of islands in the Pacific Ocean. Its capital is Saipan.",
                    "Washington, D.C. is the capital of the United States.",
                    "Capital punishment has existed in the United States since before it was a country."
                ],
                top_n=3
            )
            mock_mapper.assert_called_once_with(mock_response)

    def test_rerank_chunks_error_response(self):
        mock_error_response = {
            "errors": [
                {"id": 1001, "description": "Invalid request"},
                {"id": 1002, "description": "Model not found"}
            ]
        }
        self.manager._RerankManager__client.rerank_chunks.return_value = mock_error_response
        with patch('pygeai.core.rerank.managers.ErrorHandler.has_errors', return_value=True):
            with patch('pygeai.core.rerank.managers.ErrorHandler.extract_error', return_value="Invalid request; Model not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.rerank_chunks(
                        query="Invalid query",
                        model="invalid/model",
                        documents=["This should fail"],
                        top_n=3
                    )

                self.assertIn("Error received while reranking chunks", str(context.exception))
                self.manager._RerankManager__client.rerank_chunks.assert_called_once_with(
                    query="Invalid query",
                    model="invalid/model",
                    documents=["This should fail"],
                    top_n=3
                )

