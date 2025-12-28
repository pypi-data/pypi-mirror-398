import unittest
from unittest.mock import patch, MagicMock
from pygeai.cli.commands.feedback import show_help, send_feedback
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.cli.commands import Option


class TestFeedback(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_feedback.TestFeedback
    """

    def test_show_help(self):
        with patch('pygeai.cli.commands.feedback.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_send_feedback_missing_required_parameters(self):
        option_list = [
            (Option("request_id", ["--request-id"], "", True), "req123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            send_feedback(option_list)
        self.assertEqual(str(cm.exception), "Cannot send feedback without specifying request_id and answer_score")

    def test_send_feedback_success_with_all_parameters(self):
        option_list = [
            (Option("request_id", ["--request-id"], "", True), "req123"),
            (Option("origin", ["--origin"], "", True), "custom-origin"),
            (Option("answer_score", ["--answer-score"], "", True), "1"),
            (Option("comments", ["--comments"], "", True), "Great response!")
        ]
        with patch('pygeai.cli.commands.feedback.FeedbackClient') as mock_client, \
             patch('pygeai.cli.commands.feedback.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.send_feedback.return_value = {"status": "success", "request_id": "req123"}
            send_feedback(option_list)
            mock_client_instance.send_feedback.assert_called_once_with(
                request_id="req123",
                origin="custom-origin",
                answer_score="1",
                comments="Great response!"
            )
            mock_stdout.assert_called_once_with("Feedback detail: \n{'status': 'success', 'request_id': 'req123'}")

    def test_send_feedback_success_with_minimum_parameters(self):
        option_list = [
            (Option("request_id", ["--request-id"], "", True), "req123"),
            (Option("answer_score", ["--answer-score"], "", True), "2")
        ]
        with patch('pygeai.cli.commands.feedback.FeedbackClient') as mock_client, \
             patch('pygeai.cli.commands.feedback.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.send_feedback.return_value = {"status": "success", "request_id": "req123"}
            send_feedback(option_list)
            mock_client_instance.send_feedback.assert_called_once_with(
                request_id="req123",
                origin="user-feedback",  # Default value
                answer_score="2",
                comments=None  # Default value when not provided
            )
            mock_stdout.assert_called_once_with("Feedback detail: \n{'status': 'success', 'request_id': 'req123'}")

