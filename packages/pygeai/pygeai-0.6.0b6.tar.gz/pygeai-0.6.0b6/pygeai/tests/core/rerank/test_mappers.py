import unittest

from pygeai.core.base.mappers import ErrorMapper
from pygeai.core.base.responses import EmptyResponse, ErrorListResponse
from pygeai.core.rerank.mappers import RerankResponseMapper
from pygeai.core.rerank.models import RerankResponse, RerankResult, RerankMetaData


class TestRerankResponseMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.rerank.test_mappers.TestRerankResponseMapper
    """

    def test_map_to_rerank_response_success(self):
        response_data = {
            "id": "ad884ed0-d901-4025-ad98-a26174a52dda",
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

        result = RerankResponseMapper.map_to_rerank_response(response_data)

        self.assertIsInstance(result, RerankResponse)
        self.assertEqual(result.id, "ad884ed0-d901-4025-ad98-a26174a52dda")
        self.assertEqual(len(result.results), 3)
        self.assertEqual(result.results[0].index, 2)
        self.assertEqual(result.results[0].relevance_score, 0.8963332)
        self.assertEqual(result.meta.api_version.version, "2")
        self.assertEqual(result.meta.billed_units.search_units, 1)

    def test_map_to_rerank_response_empty_results(self):
        response_data = {
            "id": "empty-results-id",
            "results": [],
            "meta": {
                "api_version": {"version": "2"},
                "billed_units": {"search_units": 1}
            }
        }

        result = RerankResponseMapper.map_to_rerank_response(response_data)

        self.assertIsInstance(result, RerankResponse)
        self.assertEqual(result.id, "empty-results-id")
        self.assertEqual(len(result.results), 0)
        self.assertEqual(result.meta.api_version.version, "2")
        self.assertEqual(result.meta.billed_units.search_units, 1)
