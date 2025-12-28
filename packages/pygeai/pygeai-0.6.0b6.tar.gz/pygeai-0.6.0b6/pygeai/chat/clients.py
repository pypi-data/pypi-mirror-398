import json
from json import JSONDecodeError
from typing import List, Dict, Optional, Union, Generator

from pygeai import logger
from pygeai.chat.endpoints import CHAT_V1, GENERATE_IMAGE_V1
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class ChatClient(BaseClient):

    def chat(self):
        response = self.api_service.post(
            endpoint=CHAT_V1
        )
        result = response.json()
        return result

    def chat_completion(
            self,
            model: str,
            messages: List[Dict[str, str]],
            stream: bool = False,
            temperature: Optional[float] = None,
            max_tokens: Optional[int] = None,
            thread_id: Optional[str] = None,
            frequency_penalty: Optional[float] = None,
            presence_penalty: Optional[float] = None,
            variables: Optional[List] = None,
            top_p: Optional[float] = None,
            stop: Optional[Union[str, List[str]]] = None,
            response_format: Optional[Dict] = None,
            tools: Optional[List[Dict]] = None,
            tool_choice: Optional[Union[str, Dict]] = None,
            logprobs: Optional[bool] = None,
            top_logprobs: Optional[int] = None,
            seed: Optional[int] = None,
            stream_options: Optional[Dict] = None,
            store: Optional[bool] = None,
            metadata: Optional[Dict] = None,
            user: Optional[str] = None
    ) -> Union[dict, str, Generator[str, None, None]]:
        """
        Generates a chat completion response using the specified model and parameters.

        :param model: str - The model specification in the format
            "saia:<assistant_type>:<assistant_name>|<bot_id>". Determines the assistant type and associated configuration. (Required)
        :param messages: List[Dict[str, str]] - A list of messages to include in the chat completion. Each message should be a dictionary with
            the following structure:
                {
                    "role": "string",  # Possible values: "user", "system", "assistant", or others supported by the model
                    "content": "string"  # The content of the message
                } (Required)
        :param stream: bool - Whether the response should be streamed. Possible values:
            - False: Returns the complete response as a dictionary or string (default).
            - True: Returns a generator yielding content strings as they are received.
        :param temperature: Optional[float] - Controls the randomness of the response. Higher values (e.g., 2.0) produce more random responses,
            while lower values (e.g., 0.2) produce more deterministic responses. (Optional)
        :param max_tokens: Optional[int] - The maximum number of tokens to generate in the response. (Optional)
        :param thread_id: Optional[str] - An optional UUID to identify the conversation thread. (Optional)
        :param frequency_penalty: Optional[float] - A value between -2.0 and 2.0. Positive values decrease the model's likelihood of
            repeating tokens based on their frequency in the text so far. (Optional)
        :param presence_penalty: Optional[float] - A value between -2.0 and 2.0. Positive values increase the model's likelihood of
            discussing new topics by penalizing tokens that have already appeared in the text. (Optional)
        :param variables: Optional[List] - A list of additional variables. These must be defined at the time of creation, otherwise
            their use will throw an error. (Optional)
        :param top_p: Optional[float] - An alternative to temperature, nucleus sampling considers tokens with top_p probability mass. (Optional)
        :param stop: Optional[Union[str, List[str]]] - Up to 4 sequences where the API stops generating further tokens. (Optional)
        :param response_format: Optional[Dict] - Specifies the output format, e.g., JSON schema for structured outputs. (Optional)
        :param tools: Optional[List[Dict]] - A list of tools (e.g., functions) the model may call. (Optional)
        :param tool_choice: Optional[Union[str, Dict]] - Controls which tool is called (e.g., "none", "auto", or specific tool). (Optional)
        :param logprobs: Optional[bool] - Whether to return log probabilities of output tokens. (Optional)
        :param top_logprobs: Optional[int] - Number of most likely tokens to return with log probabilities (0-20). (Optional)
        :param seed: Optional[int] - For deterministic sampling, in Beta. (Optional)
        :param stream_options: Optional[Dict] - Options for streaming, e.g., include_usage. (Optional)
        :param store: Optional[bool] - Whether to store the output for model distillation or evals. (Optional)
        :param metadata: Optional[Dict] - Up to 16 key-value pairs to attach to the object. (Optional)
        :param user: Optional[str] - A unique identifier for the end-user to monitor abuse. (Optional)
        :return: Union[dict, str, Generator[str, None, None]] - For non-streaming (stream=False), returns a dictionary containing the chat completion
            result or a string if JSON decoding fails. For streaming (stream=True), returns a generator yielding content strings extracted from the
            streaming response chunks.
        """
        data = {
            'model': model,
            'messages': messages,
            'stream': stream
        }
        if temperature:
            data['temperature'] = temperature

        if max_tokens:
            data['max_completion_tokens'] = max_tokens

        if thread_id:
            data['threadId'] = thread_id

        if frequency_penalty:
            data['frequency_penalty'] = frequency_penalty

        if presence_penalty:
            data['presence_penalty'] = presence_penalty

        if variables is not None and any(variables):
            data['variables'] = variables

        if top_p is not None:
            data['top_p'] = top_p

        if stop is not None:
            data['stop'] = stop

        if response_format is not None:
            data['response_format'] = response_format

        if tools is not None:
            data['tools'] = tools

        if tool_choice is not None:
            data['tool_choice'] = tool_choice

        if logprobs is not None:
            data['logprobs'] = logprobs

        if top_logprobs is not None:
            data['top_logprobs'] = top_logprobs

        if seed is not None:
            data['seed'] = seed

        if stream_options is not None:
            data['stream_options'] = stream_options

        if store is not None:
            data['store'] = store

        if metadata is not None:
            data['metadata'] = metadata

        if user is not None:
            data['user'] = user

        headers = {}
        if thread_id:
            headers["saia-conversation-id"] = thread_id

        logger.debug(f"Generating chat completion with data: {data}")

        if stream:
            response = self.api_service.stream_post(
                endpoint=CHAT_V1,
                data=data,
                headers=headers
            )
            return self.stream_chat_generator(response)
        else:
            response = self.api_service.post(
                endpoint=CHAT_V1,
                data=data,
                headers=headers
            )
            try:
                result = response.json()
                logger.debug(f"Chat completion result: {result}")
                return result
            except JSONDecodeError as e:
                raise InvalidAPIResponseException(f"Unable to process chat request: {response.text}")

    def stream_chat_generator(self, response) -> Generator[str, None, None]:
        """
        Processes a streaming response and yields content strings.

        :param response: The streaming response from the API.
        :return: Generator[str, None, None] - Yields content strings extracted from streaming chunks.
        """
        try:
            for line in response:
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if chunk == "[DONE]":
                        break
                    try:
                        json_data = json.loads(chunk)
                        if (
                                json_data.get("choices")
                                and len(json_data["choices"]) > 0
                                and "delta" in json_data["choices"][0]
                                and "content" in json_data["choices"][0]["delta"]
                        ):
                            content = json_data["choices"][0]["delta"]["content"]
                            yield content
                    except JSONDecodeError as e:
                        continue
        except Exception as e:
            raise InvalidAPIResponseException(f"Unable to process streaming chat response: {e}")

    def generate_image(
            self,
            model: str,
            prompt: str,
            n: int,
            quality: str,
            size: str,
            aspect_ratio: Optional[str] = None
    ) -> dict:
        """
        Generates an image based on the provided parameters.

        :param model: str - The model specification for image generation, e.g., "openai/gpt-image-1". (Required)
        :param prompt: str - Description of the desired image. (Required)
        :param n: int - Number of images to generate (1-10, depending on the model). (Required)
        :param quality: str - Rendering quality, e.g., "high". (Required)
        :param size: str - Image dimensions, e.g., "1024x1024". (Required)
        :param aspect_ratio: Optional[str] - Relationship between image’s width and height, e.g., "1:1", "9:16", "16:9", "3:4", "4:3". (Optional)
        :return: dict - The API response containing the generated image data.
        :raises InvalidAPIResponseException: If the API response cannot be processed.
        """
        data = {
            'model': model,
            'prompt': prompt,
            'n': n,
            'quality': quality,
            'size': size
        }

        if aspect_ratio:
            data['aspect_ratio'] = aspect_ratio

        logger.debug(f"Generating image with data: {data}")

        response = self.api_service.post(
            endpoint=GENERATE_IMAGE_V1,
            data=data
        )

        try:
            result = response.json()
            logger.debug(f"Image generation result: {result}")
            return result
        except JSONDecodeError as e:
            raise InvalidAPIResponseException(f"Unable to process image generation request: {response.text}")