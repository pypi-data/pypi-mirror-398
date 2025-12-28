import json
from typing import Dict, Any, Optional, List

from pygeai.core.responses import NewAssistantResponse, ChatResponse, ProviderResponse, \
    UsageDetails, TokenDetails, Choice, ChatMessage
from pygeai.core.base.mappers import ModelMapper
from pygeai.core.models import Assistant


class AssistantResponseMapper:

    @classmethod
    def map_to_assistant_response(cls, data: dict) -> Assistant:
        assistant = ModelMapper.map_to_assistant(data)

        return assistant

    @classmethod
    def map_to_assistant_created_response(cls, data: dict) -> NewAssistantResponse:
        response = NewAssistantResponse()
        if 'assistantId' in data:
            response.assistant = ModelMapper.map_to_assistant(data)
        else:
            response.project = ModelMapper.map_to_project(data)

        return response

    @classmethod
    def map_to_chat_request_response(cls, data: Dict[str, Any]) -> ChatResponse:
        """
        Maps a dictionary to a `ChatResponse` object.

        :param data: dict - The dictionary containing chat response details.
        :return: ChatResponse - The mapped `ChatResponse` object.
        """
        provider_response = data.get("providerResponse")
        return ChatResponse(
            progress=data.get("progress"),
            provider_name=data.get("providerName"),
            provider_response=cls.map_to_provider_response(provider_response) if provider_response else None,
            request_id=data.get("requestId"),
            status=data.get("status"),
            success=data.get("success"),
            text=data.get("text")
        )

    @classmethod
    def map_to_provider_response(cls, provider_response: Any) -> ProviderResponse:
        """
        Parses the provider response, which may be a JSON string.

        :param provider_response: Any - The raw provider response.
        :return: ProviderResponse - The parsed `ProviderResponse` object.
        """
        if isinstance(provider_response, str):
            provider_response = json.loads(provider_response)

        choices = provider_response.get("choices")
        usage_data = provider_response.get("usage")
        return ProviderResponse(
            created=provider_response.get("created"),
            usage=cls._parse_usage(usage_data) if usage_data else None,
            model=provider_response.get("model"),
            service_tier=provider_response.get("service_tier"),
            id=provider_response.get("id"),
            system_fingerprint=provider_response.get("system_fingerprint"),
            choices=cls._parse_choices(choices) if choices else [],
            object=provider_response.get("object")
        )

    @classmethod
    def _parse_usage(cls, usage_data: Dict[str, Any]) -> UsageDetails:
        """
        Parses usage details from a dictionary.

        :param usage_data: dict - The usage details data.
        :return: UsageDetails - The parsed `UsageDetails` object.
        """
        completion_tokens_details_data = usage_data.get("completion_tokens_details")
        prompt_tokens_details_data = usage_data.get("prompt_tokens_details")
        return UsageDetails(
            completion_tokens=usage_data.get("completion_tokens", 0),
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            total_cost=usage_data.get("total_cost", 0.0),
            completion_tokens_details=cls._parse_completion_tokens_details(completion_tokens_details_data) if completion_tokens_details_data else None,
            prompt_tokens_details=cls._parse_prompt_tokens_details(prompt_tokens_details_data) if prompt_tokens_details_data else None,
            total_tokens=usage_data.get("total_tokens", 0),
            currency=usage_data.get("currency", "USD"),
            completion_cost=usage_data.get("completion_cost", 0.0),
            prompt_cost=usage_data.get("prompt_cost", 0.0)
        )

    @classmethod
    def _parse_completion_tokens_details(cls, details: Dict[str, Any]) -> Optional[TokenDetails]:
        """
        Parses completion tokens details.

        :param details: dict - The completion tokens details.
        :return: CompletionTokensDetails - The parsed details object.
        """
        if not details:
            return None
        return TokenDetails(
            reasoning_tokens=details.get("reasoning_tokens")
        )

    @classmethod
    def _parse_prompt_tokens_details(cls, details: Dict[str, Any]) -> Optional[TokenDetails]:
        """
        Parses prompt tokens details.

        :param details: dict - The prompt tokens details.
        :return: PromptTokensDetails - The parsed details object.
        """
        if not details:
            return None
        return TokenDetails(
            cached_tokens=details.get("cached_tokens")
        )

    @classmethod
    def _parse_choices(cls, choices: list) -> List[Choice]:
        """
        Parses choices from a list.

        :param choices: list - The choices data.
        :return: List[Choice] - A list of parsed `Choice` objects.
        """
        return [
            Choice(
                finish_reason=choice.get("finish_reason"),
                index=choice.get("index"),
                message=cls._parse_message(choice.get("message")) if 'message' in choice else None
            )
            for choice in choices
        ]

    @classmethod
    def _parse_message(cls, message_data: Dict[str, Any]) -> ChatMessage:
        """
        Parses a chat message.

        :param message_data: dict - The chat message data.
        :return: ChatMessage - The parsed `ChatMessage` object.
        """
        return ChatMessage(
            role=message_data.get("role"),
            function_call=message_data.get("function_call"),
            refusal=message_data.get("refusal"),
            tool_calls=message_data.get("tool_calls"),
            content=message_data.get("content")
        )

