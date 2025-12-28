import unittest
from unittest.mock import patch, MagicMock
from pygeai.chat.iris import Iris


class TestIris(unittest.TestCase):
    """
    python -m unittest pygeai.tests.chat.test_iris.TestIris
    """
    def setUp(self):
        self.iris = Iris()
        self.mock_client = MagicMock()
        self.iris.client = self.mock_client
        self.messages = [{"role": "user", "content": "Hello"}]
        self.llm_settings = {
            "temperature": 0.6,
            "max_tokens": 800,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.2
        }

    def test_init_sets_client(self):
        self.assertIsNotNone(self.iris.client)

    def test_stream_answer_calls_chat_completion_with_stream_true(self):
        expected_response = {"stream": "data"}
        self.mock_client.chat_completion.return_value = expected_response

        result = self.iris.stream_answer(self.messages)

        self.mock_client.chat_completion.assert_called_once_with(
            model="saia:agent:com.globant.iris",
            messages=self.messages,
            stream=True,
            **self.llm_settings
        )
        self.assertEqual(result, expected_response)

