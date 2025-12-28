import unittest
from unittest.mock import patch, MagicMock
import json
from pygeai.chat.clients import ChatClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestChatClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.chat.test_clients.TestChatClient
    """
    def setUp(self):
        self.chat_client = ChatClient(api_key="test_key", base_url="test_url", alias="test_alias")
        self.mock_api_service = MagicMock()
        self.chat_client.api_service = self.mock_api_service

    def test_chat_success(self):
        expected_response = {"message": "Hello, how can I help?"}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.post.return_value = mock_response

        result = self.chat_client.chat()

        self.assertEqual(result, expected_response)
        self.mock_api_service.post.assert_called_once()

    def test_chat_completion_non_stream_success(self):
        model = "saia:assistant:test-assistant|123"
        messages = [{"role": "user", "content": "Hello"}]
        expected_response = {"choices": [{"message": {"content": "Hi there!"}}]}
        mock_response = MagicMock()
        mock_response.json.return_value = expected_response
        self.mock_api_service.post.return_value = mock_response

        result = self.chat_client.chat_completion(model=model, messages=messages, stream=False)

        self.assertEqual(result, expected_response)
        self.mock_api_service.post.assert_called_once()
        call_args = self.mock_api_service.post.call_args
        self.assertEqual(call_args[1]['data']['model'], model)
        self.assertEqual(call_args[1]['data']['messages'], messages)
        self.assertEqual(call_args[1]['data']['stream'], False)

    def test_chat_completion_non_stream_json_decode_error(self):
        model = "saia:assistant:test-assistant|123"
        messages = [{"role": "user", "content": "Hello"}]
        expected_text = "Raw response text"
        mock_response = MagicMock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = expected_text
        self.mock_api_service.post.return_value = mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.chat_client.chat_completion(model=model, messages=messages, stream=False)

        self.assertIn("Unable to process chat request", str(context.exception))
        self.mock_api_service.post.assert_called_once()

    def test_chat_completion_stream_success(self):
        model = "saia:assistant:test-assistant|123"
        messages = [{"role": "user", "content": "Hello"}]
        mock_response = MagicMock()
        self.mock_api_service.stream_post.return_value = mock_response

        result = self.chat_client.chat_completion(model=model, messages=messages, stream=True)

        self.assertTrue(hasattr(result, '__iter__'))  # Check if result is a generator
        self.mock_api_service.stream_post.assert_called_once()
        call_args = self.mock_api_service.stream_post.call_args
        self.assertEqual(call_args[1]['data']['model'], model)
        self.assertEqual(call_args[1]['data']['messages'], messages)
        self.assertEqual(call_args[1]['data']['stream'], True)

    def test_chat_completion_with_optional_parameters(self):
        model = "saia:assistant:test-assistant|123"
        messages = [{"role": "user", "content": "Hello"}]
        temperature = 0.7
        max_tokens = 100
        thread_id = "thread-123"
        frequency_penalty = 0.5
        presence_penalty = 0.3
        variables = ["var1", "var2"]
        top_p = 0.9
        stop = ["stop_word"]
        response_format = {"type": "json"}
        tools = [{"type": "function", "name": "tool1"}]
        tool_choice = "auto"
        logprobs = True
        top_logprobs = 5
        seed = 42
        stream_options = {"include_usage": True}
        store = True
        metadata = {"key": "value"}
        user = "user-123"
        mock_response = MagicMock()
        mock_response.json.return_value = {"choices": [{"message": {"content": "Hi!"}}]}
        self.mock_api_service.post.return_value = mock_response

        result = self.chat_client.chat_completion(
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            thread_id=thread_id,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            variables=variables,
            top_p=top_p,
            stop=stop,
            response_format=response_format,
            tools=tools,
            tool_choice=tool_choice,
            logprobs=logprobs,
            top_logprobs=top_logprobs,
            seed=seed,
            stream_options=stream_options,
            store=store,
            metadata=metadata,
            user=user
        )

        self.assertIsNotNone(result)
        self.mock_api_service.post.assert_called_once()
        call_args = self.mock_api_service.post.call_args
        data = call_args[1]['data']
        self.assertEqual(data['temperature'], temperature)
        self.assertEqual(data['max_completion_tokens'], max_tokens)
        self.assertEqual(data['threadId'], thread_id)
        self.assertEqual(data['frequency_penalty'], frequency_penalty)
        self.assertEqual(data['presence_penalty'], presence_penalty)
        self.assertEqual(data['variables'], variables)
        self.assertEqual(data['top_p'], top_p)
        self.assertEqual(data['stop'], stop)
        self.assertEqual(data['response_format'], response_format)
        self.assertEqual(data['tools'], tools)
        self.assertEqual(data['tool_choice'], tool_choice)
        self.assertEqual(data['logprobs'], logprobs)
        self.assertEqual(data['top_logprobs'], top_logprobs)
        self.assertEqual(data['seed'], seed)
        self.assertEqual(data['stream_options'], stream_options)
        self.assertEqual(data['store'], store)
        self.assertEqual(data['metadata'], metadata)
        self.assertEqual(data['user'], user)

    def test_stream_chat_generator_success(self):
        mock_response = [
            "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}\n",
            "data: {\"choices\": [{\"delta\": {\"content\": \" World\"}}]}\n",
            "data: [DONE]\n"
        ]
        result = list(self.chat_client.stream_chat_generator(mock_response))

        self.assertEqual(result, ["Hello", " World"])

    def test_stream_chat_generator_invalid_json(self):
        mock_response = [
            "data: invalid_json\n",
            "data: {\"choices\": [{\"delta\": {\"content\": \"Hello\"}}]}\n",
            "data: [DONE]\n"
        ]
        result = list(self.chat_client.stream_chat_generator(mock_response))

        self.assertEqual(result, ["Hello"])

    def test_stream_chat_generator_no_content(self):
        mock_response = [
            "data: {\"choices\": [{\"delta\": {}}]}\n",
            "data: [DONE]\n"
        ]
        result = list(self.chat_client.stream_chat_generator(mock_response))

        self.assertEqual(result, [])

    def test_stream_chat_generator_exception(self):
        mock_response = MagicMock()
        mock_response.__iter__.side_effect = Exception("Streaming error")

        with self.assertRaises(InvalidAPIResponseException) as context:
            list(self.chat_client.stream_chat_generator(mock_response))

        self.assertIn("Unable to process streaming chat response", str(context.exception))
