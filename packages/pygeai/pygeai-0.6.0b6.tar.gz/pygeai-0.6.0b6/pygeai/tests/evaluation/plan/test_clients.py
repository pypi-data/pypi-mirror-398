import unittest
from unittest.mock import patch, MagicMock
import json

from pygeai.evaluation.plan.clients import EvaluationPlanClient


class TestEvaluationPlanClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.evaluation.plan.test_clients.TestEvaluationPlanClient
    """

    def setUp(self):
        self.client = EvaluationPlanClient()
        self.mock_response = MagicMock()
        self.mock_response.content = json.dumps({"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_evaluation_plans(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_evaluation_plans()
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_evaluation_plan_minimal(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.create_evaluation_plan(
            name="Test Plan",
            type="TextPromptAssistant"
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['evaluationPlanName'], "Test Plan")
        self.assertEqual(call_args[1]['data']['evaluationPlanType'], "TextPromptAssistant")

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_evaluation_plan_with_assistant(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.create_evaluation_plan(
            name="Test Plan",
            type="TextPromptAssistant",
            assistant_id="asst-123",
            assistant_name="Test Assistant",
            assistant_revision="1.0"
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['evaluationPlanAssistantId'], "asst-123")
        self.assertEqual(call_args[1]['data']['evaluationPlanAssistantName'], "Test Assistant")
        self.assertEqual(call_args[1]['data']['evaluationPlanAssistantRevision'], "1.0")

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_evaluation_plan_with_all_params(self, mock_post):
        mock_post.return_value = self.mock_response
        system_metrics = [{"systemMetricId": "metric-1", "systemMetricWeight": 0.5}]
        result = self.client.create_evaluation_plan(
            name="Test Plan",
            type="RAG Assistant",
            profile_name="Test Profile",
            dataset_id="dataset-123",
            system_metrics=system_metrics
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['evaluationPlanProfileName'], "Test Profile")
        self.assertEqual(call_args[1]['data']['dataSetId'], "dataset-123")
        self.assertEqual(call_args[1]['data']['systemMetrics'], system_metrics)

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_evaluation_plan(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_evaluation_plan("plan-123")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_evaluation_plan_name_only(self, mock_put):
        mock_put.return_value = self.mock_response
        result = self.client.update_evaluation_plan(
            evaluation_plan_id="plan-123",
            name="Updated Plan"
        )
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[1]['data']['evaluationPlanName'], "Updated Plan")
        self.assertEqual(len(call_args[1]['data']), 1)

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_evaluation_plan_multiple_fields(self, mock_put):
        mock_put.return_value = self.mock_response
        system_metrics = [{"systemMetricId": "metric-1", "systemMetricWeight": 0.8}]
        result = self.client.update_evaluation_plan(
            evaluation_plan_id="plan-123",
            name="Updated Plan",
            type="RAG Assistant",
            assistant_id="asst-456",
            assistant_name="Updated Assistant",
            assistant_revision="2.0",
            profile_name="Updated Profile",
            dataset_id="dataset-456",
            system_metrics=system_metrics
        )
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[1]['data']['evaluationPlanName'], "Updated Plan")
        self.assertEqual(call_args[1]['data']['evaluationPlanType'], "RAG Assistant")
        self.assertEqual(call_args[1]['data']['evaluationPlanAssistantId'], "asst-456")
        self.assertEqual(call_args[1]['data']['systemMetrics'], system_metrics)

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_evaluation_plan(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_evaluation_plan("plan-123")
        mock_delete.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_evaluation_plan_system_metrics(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_evaluation_plan_system_metrics("plan-123")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_add_evaluation_plan_system_metric(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.add_evaluation_plan_system_metric(
            evaluation_plan_id="plan-123",
            system_metric_id="metric-456",
            system_metric_weight=0.75
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['systemMetricId'], "metric-456")
        self.assertEqual(call_args[1]['data']['systemMetricWeight'], 0.75)

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_evaluation_plan_system_metric(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_evaluation_plan_system_metric(
            evaluation_plan_id="plan-123",
            system_metric_id="metric-456"
        )
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_evaluation_plan_system_metric(self, mock_put):
        mock_put.return_value = self.mock_response
        result = self.client.update_evaluation_plan_system_metric(
            evaluation_plan_id="plan-123",
            system_metric_id="metric-456",
            system_metric_weight=0.9
        )
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[1]['data']['systemMetricWeight'], 0.9)

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_evaluation_plan_system_metric(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_evaluation_plan_system_metric(
            evaluation_plan_id="plan-123",
            system_metric_id="metric-456"
        )
        mock_delete.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_system_metrics(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_system_metrics()
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_system_metric(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_system_metric("metric-456")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_execute_evaluation_plan(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.execute_evaluation_plan("plan-123")
        mock_post.assert_called_once()
        self.assertEqual(result, {"id": "plan-123", "status": "success"})


if __name__ == '__main__':
    unittest.main()
