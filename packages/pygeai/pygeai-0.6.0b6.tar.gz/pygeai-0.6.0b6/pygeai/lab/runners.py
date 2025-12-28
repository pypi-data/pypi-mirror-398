import asyncio
from typing import Union

from pygeai.chat.managers import ChatManager
from pygeai.core.common.exceptions import WrongArgumentError
from pygeai.core.models import ChatMessage, ChatMessageList, LlmSettings
from pygeai.core.responses import ProviderResponse
from pygeai.lab.models import Agent


class Runner:

    @classmethod
    async def run(
            cls,
            agent: Agent,
            user_input: Union[str | ChatMessage | ChatMessageList],
            llm_settings: Union[dict | LlmSettings] = None
    ) -> ProviderResponse:
        """
        Asynchronously executes a chat completion request for the specified agent with the provided user input and LLM settings.

        :param agent: Agent - The agent configuration to use for the chat completion.
        :param user_input: Union[str, ChatMessage, ChatMessageList] - The user input, which can be a string, a single ChatMessage, or a ChatMessageList.
        :param llm_settings: Union[dict, LlmSettings] - Optional LLM configuration settings. If None, default settings are used.
        :return: ProviderResponse - The ProviderResponse from the chat completion request.
        :raises WrongArgumentError: If the user_input type is not str, ChatMessage, or ChatMessageList.
        """
        messages = cls._get_messages(user_input)
        llm_settings = cls._get_llm_settings(llm_settings)

        chat_manager = ChatManager()
        response = await asyncio.to_thread(
            chat_manager.chat_completion,
            model=f"saia:agent:{agent.name}",
            messages=messages,
            llm_settings=llm_settings
        )
        return response

    @classmethod
    def _get_messages(cls, user_input: Union[str | ChatMessage | ChatMessageList]):
        """
        Converts the user input into a ChatMessageList for use in chat completion.

        :param user_input: Union[str, ChatMessage, ChatMessageList] - The user input to process.
        :return: ChatMessageList - A ChatMessageList containing the processed user input.
        :raises WrongArgumentError: If the user_input type is not str, ChatMessage, or ChatMessageList.
        """
        if isinstance(user_input, str):
            new_message = {
                "role": "user",
                "content": user_input
            }
            messages = ChatMessageList(messages=[new_message])
        elif isinstance(user_input, ChatMessage):
            messages = ChatMessageList(messages=[user_input])
        elif isinstance(user_input, ChatMessageList):
            messages = user_input
        else:
            raise WrongArgumentError("message must be either of string, ChatMessage or ChatMessageList type")

        return messages

    @classmethod
    def _get_llm_settings(cls, llm_settings: Union[dict | LlmSettings]):
        """
        Processes the LLM settings into a dictionary format for chat completion.

        :param llm_settings: Union[dict, LlmSettings] - The LLM settings to process. If None, default settings are applied.
        :return: LlmSettings - A LlmSettings object containing the LLM configuration settings.
        """
        if not llm_settings:
            llm_settings = LlmSettings.model_validate({
                "temperature": 0.6,
                "max_tokens": 800,
                "frequency_penalty": 0.1,
                "presence_penalty": 0.2
            })
        elif isinstance(llm_settings, dict):
            llm_settings = LlmSettings(
                provider_name=llm_settings.get("providerName") or llm_settings.get("provider") or llm_settings.get("provider_name"),
                model_name=llm_settings.get("modelName") or llm_settings.get("model") or llm_settings.get("model_name"),
                temperature=llm_settings.get("temperature"),
                max_tokens=llm_settings.get("maxTokens") or llm_settings.get("max_tokens"),
                frequency_penalty=llm_settings.get("frequency_penalty") or llm_settings.get("frequencyPenalty"),
                presence_penalty=llm_settings.get("presence_penalty") or llm_settings.get("presencePenalty"),
            )

        return llm_settings
