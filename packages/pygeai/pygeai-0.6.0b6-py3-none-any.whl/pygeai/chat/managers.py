from pygeai import logger
from pygeai.core.common.exceptions import APIError
from pygeai.core.handlers import ErrorHandler
from pygeai.core.models import ChatMessageList, \
    ChatVariableList, LlmSettings, ChatToolList, ToolChoice
from pygeai.assistant.mappers import AssistantResponseMapper
from pygeai.chat.clients import ChatClient
from pygeai.core.responses import ChatResponse, ProviderResponse


class ChatManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default"):
        self.__chat_client = ChatClient(api_key, base_url, alias)

    def chat_completion(
            self,
            model: str,
            messages: ChatMessageList,
            llm_settings: LlmSettings,
            thread_id: str = None,
            variables: ChatVariableList = None,
            tool_choice: ToolChoice = None,
            tools: ChatToolList = None,
    ) -> ProviderResponse:
        """
        Generates a chat completion response using the specified language model.

        This method sends a chat completion request to the ChatClient with the provided
        model, messages, and settings. It processes the response by mapping errors if
        present or converting it into an assistant response format.

        :param model: str - The identifier of the language model to use.
        :param messages: ChatMessageList - A list of chat messages to provide context for the completion.
        :param llm_settings: LlmSettings - Configuration settings for the language model,
                             including temperature, max tokens, and penalties.
        :param thread_id: str, optional - An optional identifier for the conversation thread.
        :param variables: ChatVariableList, optional - Additional variables to include in the request.
        :param tool_choice: ToolChoice, optional - Indicates which tool to call.
        :param tools: ChatToolList, optional - Additional tools the model may call
        :return: ProviderResponse - The structured chat response.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__chat_client.chat_completion(
            model=model,
            messages=messages.to_list(),
            stream=False,
            temperature=llm_settings.temperature,
            max_tokens=llm_settings.max_tokens,
            thread_id=thread_id,
            frequency_penalty=llm_settings.frequency_penalty,
            presence_penalty=llm_settings.presence_penalty,
            variables=variables.to_list() if variables else None,
            tool_choice=tool_choice.to_dict() if tool_choice else None,
            tools=tools.to_list() if tools else None
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while chatting while sending chat request: {error}")
            raise APIError(f"Error received while chatting while sending chat request: {error}")

        result = AssistantResponseMapper.map_to_provider_response(response_data)
        return result
