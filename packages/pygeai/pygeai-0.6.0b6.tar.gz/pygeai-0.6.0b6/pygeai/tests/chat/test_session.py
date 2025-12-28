import unittest
from unittest.mock import patch, MagicMock
from pygeai.chat.session import AgentChatSession
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestAgentChatSession(unittest.TestCase):
    """
    python -m unittest pygeai.tests.chat.test_session.TestAgentChatSession
    """
    def setUp(self):
        self.agent_name = "test_agent"
        with patch('pygeai.chat.clients.ChatClient', return_value=MagicMock()):
            self.session = AgentChatSession(agent_name=self.agent_name)
        self.mock_client = MagicMock()
        self.session.client = self.mock_client
        self.messages = [{"role": "user", "content": "Hello"}]

    def test_init_sets_agent_name_and_client(self):
        self.assertEqual(self.session.agent_name, self.agent_name)
        self.assertIsNotNone(self.session.client)

    def test_stream_answer_calls_chat_completion_with_stream_true(self):
        expected_response = {"stream": "data"}
        self.mock_client.chat_completion.return_value = expected_response

        result = self.session.stream_answer(self.messages)

        self.mock_client.chat_completion.assert_called_once()
        call_args = self.mock_client.chat_completion.call_args
        self.assertEqual(call_args[1]['model'], f"saia:agent:{self.agent_name}")
        self.assertEqual(call_args[1]['messages'], self.messages)
        self.assertTrue(call_args[1]['stream'])
        self.assertEqual(result, expected_response)

    def test_get_answer_calls_chat_completion_with_stream_false(self):
        expected_content = "Hi there!"
        expected_response = {"choices": [{"message": {"content": expected_content}}]}
        self.mock_client.chat_completion.return_value = expected_response

        result = self.session.get_answer(self.messages)

        self.mock_client.chat_completion.assert_called_once()
        call_args = self.mock_client.chat_completion.call_args
        self.assertEqual(call_args[1]['model'], f"saia:agent:{self.agent_name}")
        self.assertEqual(call_args[1]['messages'], self.messages)
        self.assertFalse(call_args[1]['stream'])
        self.assertEqual(result, expected_content)

    def test_get_answer_handles_exception_and_raises_invalid_api_response_exception(self):
        self.mock_client.chat_completion.side_effect = Exception("API error")

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.session.get_answer(self.messages)

        self.mock_client.chat_completion.assert_called_once()
        call_args = self.mock_client.chat_completion.call_args
        self.assertEqual(call_args[1]['model'], f"saia:agent:{self.agent_name}")
        self.assertEqual(call_args[1]['messages'], self.messages)
        self.assertFalse(call_args[1]['stream'])
        self.assertIn(f"Unable to communicate with specified agent {self.agent_name}", str(context.exception))

