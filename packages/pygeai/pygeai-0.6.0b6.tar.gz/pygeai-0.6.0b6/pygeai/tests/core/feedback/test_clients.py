import unittest
from unittest.mock import patch, Mock
from pygeai.core.feedback.clients import FeedbackClient


class TestFeedbackClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.feedback.test_clients.TestFeedbackClient
    """
    def setUp(self):
        self.feedback_client = FeedbackClient()
        self.request_id = "test_request_123"
        self.origin = "user-feedback"
        self.answer_score = 1
        self.comments = "Great response!"

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_send_feedback_without_comments(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = self.feedback_client.send_feedback(
            request_id=self.request_id,
            origin=self.origin,
            answer_score=self.answer_score
        )

        expected_data = {
            "origin": self.origin,
            "answerScore": self.answer_score
        }
        mock_post.assert_called_once_with(
            endpoint=f"v1/feedback/request/{self.request_id}",
            data=expected_data
        )
        self.assertEqual(result, {})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_send_feedback_with_comments(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        result = self.feedback_client.send_feedback(
            request_id=self.request_id,
            origin=self.origin,
            answer_score=self.answer_score,
            comments=self.comments
        )

        expected_data = {
            "origin": self.origin,
            "answerScore": self.answer_score,
            "comments": self.comments
        }
        mock_post.assert_called_once_with(
            endpoint=f"v1/feedback/request/{self.request_id}",
            data=expected_data
        )
        self.assertEqual(result, {})

