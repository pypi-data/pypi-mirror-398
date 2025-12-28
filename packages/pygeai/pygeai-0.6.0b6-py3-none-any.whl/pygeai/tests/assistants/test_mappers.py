import unittest

from pygeai.assistant.mappers import AssistantResponseMapper
from pygeai.core.responses import NewAssistantResponse, ChatResponse, ProviderResponse, UsageDetails, Choice


class TestAssistantResponseMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.test_mappers.TestAssistantResponseMapper
    """

    def test_map_to_assistant_response(self):
        data = {
            'assistantId': '123',
            'assistantName': 'Test Assistant',
            # Add other fields as necessary
        }
        result = AssistantResponseMapper.map_to_assistant_response(data)

        self.assertEqual(result.id, '123')
        self.assertEqual(result.name, 'Test Assistant')
        # Add more assertions based on your model

    def test_map_to_assistant_created_response_with_assistant(self):
        data = {
            'assistantId': '123',
            'assistantName': 'Test Assistant',
        }
        result = AssistantResponseMapper.map_to_assistant_created_response(data)

        self.assertIsInstance(result, NewAssistantResponse)
        self.assertIsNotNone(result.assistant)
        self.assertEqual(result.assistant.id, '123')

    def test_map_to_assistant_created_response_with_project(self):
        data = {
            'projectId': '456',
            'projectName': 'Test Project',
        }
        result = AssistantResponseMapper.map_to_assistant_created_response(data)

        self.assertIsInstance(result, NewAssistantResponse)
        self.assertIsNotNone(result.project)
        self.assertEqual(result.project.id, '456')

    def test_map_to_chat_request_response(self):
        data = {
            'providerResponse': {
                'created': 1234567890,
                'usage': {
                    'total_tokens': 100,
                    'prompt_tokens': 50,
                    'completion_tokens': 50,
                },
                'model': 'test_model',
                'service_tier': 'basic',
                'id': 'response_id',
                'system_fingerprint': 'fingerprint_value',
                'choices': [
                    {
                        'text': 'Choice text',
                        'index': 0,
                        'logprobs': None,
                        'finish_reason': 'stop',
                    }
                ],
                'object': 'chat.completion.response'
            },
            'progress': 100,
            'providerName': 'Test Provider',
            'requestId': 'req_123',
            'status': 'success',
            'success': True,
            'text': 'Test response',
        }

        result = AssistantResponseMapper.map_to_chat_request_response(data)

        self.assertIsInstance(result, ChatResponse)
        self.assertEqual(result.progress, 100)
        self.assertEqual(result.request_id, 'req_123')
        self.assertTrue(result.success)
        self.assertEqual(result.text, 'Test response')
        self.assertIsInstance(result.provider_response, ProviderResponse)

    def test_parse_provider_response(self):
        provider_response_data = {
            'created': 1740096000,  # '2025-02-21T00:00:00Z'
            'usage': {
                'completion_tokens': 5,
                'prompt_tokens': 3,
                'total_cost': 0.001
            },
            'model': 'test_model',
            'choices': [{'finish_reason': 'stop', 'index': 0, 'message': {'role': 'assistant', 'content': 'Hello!'}}]
        }
        result = AssistantResponseMapper.map_to_provider_response(provider_response_data)

        self.assertIsInstance(result, ProviderResponse)
        self.assertEqual(result.model, 'test_model')
        self.assertIsInstance(result.usage, UsageDetails)

    def test_parse_choices(self):
        choices_data = [
            {'finish_reason': 'stop', 'index': 0, 'message': {'role': 'assistant', 'content': 'Hello!'}}
        ]
        result = AssistantResponseMapper._parse_choices(choices_data)

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Choice)

