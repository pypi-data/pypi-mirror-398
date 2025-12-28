import unittest
from unittest.mock import patch, MagicMock

from pygeai.evaluation.result.clients import EvaluationResultClient


class TestEvaluationResultClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.evaluation.result.test_clients.TestEvaluationResultClient
    """

    def setUp(self):
        self.client = EvaluationResultClient()
        self.mock_response = MagicMock()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_evaluation_results_success(self, mock_get):
        self.mock_response.content = b'[{"id": "result-1", "status": "completed"}, {"id": "result-2", "status": "pending"}]'
        mock_get.return_value = self.mock_response
        
        result = self.client.list_evaluation_results("plan-123")
        
        mock_get.assert_called_once()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["id"], "result-1")
        self.assertEqual(result[1]["id"], "result-2")

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_evaluation_results_empty(self, mock_get):
        self.mock_response.content = b'[]'
        mock_get.return_value = self.mock_response
        
        result = self.client.list_evaluation_results("plan-456")
        
        mock_get.assert_called_once()
        self.assertEqual(result, [])

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_evaluation_result_success(self, mock_get):
        self.mock_response.content = b'{"id": "result-123", "status": "completed", "score": 0.95}'
        mock_get.return_value = self.mock_response
        
        result = self.client.get_evaluation_result("result-123")
        
        mock_get.assert_called_once()
        self.assertEqual(result["id"], "result-123")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["score"], 0.95)

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_evaluation_result_with_details(self, mock_get):
        self.mock_response.content = b'{"id": "result-789", "status": "failed", "error": "Test error"}'
        mock_get.return_value = self.mock_response
        
        result = self.client.get_evaluation_result("result-789")
        
        mock_get.assert_called_once()
        self.assertEqual(result["id"], "result-789")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"], "Test error")


if __name__ == '__main__':
    unittest.main()
