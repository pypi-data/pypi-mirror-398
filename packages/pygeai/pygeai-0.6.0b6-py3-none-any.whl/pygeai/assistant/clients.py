import json
from json import JSONDecodeError

from pygeai import logger
from pygeai.assistant.endpoints import GET_ASSISTANT_DATA_V1, CREATE_ASSISTANT_V1, UPDATE_ASSISTANT_V1, BEGIN_CONVERSATION_V1, \
    SEND_TEXT_PROMPT_V1, SEND_CHAT_REQUEST_V1, GET_REQUEST_STATUS_V1, CANCEL_REQUEST_V1
from pygeai.assistant.data_analyst.endpoints import GET_DATA_ANALYST_STATUS_V1, EXTEND_DATA_ANALYST_DATASET_V1
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.decorators import handler_server_error
from pygeai.core.common.exceptions import InvalidAPIResponseException


class AssistantClient(BaseClient):

    def get_assistant_data(
            self,
            assistant_id: str,
            detail: str = "summary"
    ) -> dict:
        """
        Retrieves assistant information according to ID provided.

        :param assistant_id: str - Unique identifier of the assistant.
        :param detail: str - Level of detail. Available options are: "summary" and "full". Defaults to "summary". ()
        :return: dict - The API response containing assistant information in JSON format.
        """
        endpoint = GET_ASSISTANT_DATA_V1.format(id=assistant_id)
        response = self.api_service.get(
            endpoint=endpoint,
            params={
                "detail": detail
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get assistant data for ID '{assistant_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get assistant data for ID '{assistant_id}': {response.text}")

    def create_assistant(
            self,
            assistant_type: str,
            name: str,
            prompt: str,
            description: str = None,
            llm_settings: dict = None,
            welcome_data: dict = None
    ) -> dict:
        """
        Creates a new assistant with the specified configuration.

        :param assistant_type: str - The type of assistant. Possible values are "text" and "chat". (Required)
        :param name: str - The name of the assistant. (Required)
        :param prompt: str - The prompt used by the assistant. (Required)
        :param description: str - A brief description of the assistant. (Optional)
        :param llm_settings: dict - A dictionary containing settings for the language model. Example structure:
            {
                "providerName": "string",
                "modelName": "string",
                "temperature": decimal,
                "maxTokens": integer
            } (Optional)
        :param welcome_data: dict - A dictionary containing welcome data for the assistant. Example structure:
            {
                "title": "string",
                "description": "string",
                "features": [
                    {"title": "string", "description": "string"},
                    ...
                ],
                "examplesPrompt": [
                    {"title": "string", "description": "string", "promptText": "string"},
                    ...
                ]
            } (Optional)
        :return: dict - The API response as a JSON object containing details about the created assistant.
        """
        data = {
            "type": assistant_type,
            "name": name,
            "prompt": prompt,
            "description": description,
            "llmSettings": llm_settings,
            "welcomeData": welcome_data
        }
        response = self.api_service.post(
            endpoint=CREATE_ASSISTANT_V1,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to create assistant with name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create assistant with name '{name}': {response.text}")

    def update_assistant(
            self,
            assistant_id: str,
            status: int,
            action: str,
            revision_id: str = None,
            name: str = None,
            prompt: str = None,
            description: str = None,
            llm_settings: dict = None,
            welcome_data: dict = None
    ) -> dict:
        """
        Updates an existing assistant with the specified parameters.

        :param assistant_id: str - The ID of the assistant to be updated. (Required)
        :param status: int - The status of the assistant. Possible values:
            1: Enabled, 2: Disabled. (Required)
        :param action: str - The action to perform. Possible values:
            "save", "saveNewRevision" (default), "savePublishNewRevision". (Required)
        :param revision_id: str - The revision ID of the assistant. Required if the action is "save". (Optional)
        :param name: str - The updated name for the assistant. (Optional)
        :param prompt: str - The updated prompt for the assistant. (Optional)
        :param description: str - The updated description for the assistant. (Optional)
        :param llm_settings: dict - A dictionary containing updated language model settings. Example structure:
            {
                "providerName": "string",
                "modelName": "string",
                "temperature": decimal,
                "maxTokens": integer
            } (Optional)
        :param welcome_data: dict - A dictionary containing updated welcome data for the assistant. Example structure:
            {
                "title": "string",
                "description": "string",
                "features": [
                    {"title": "string", "description": "string"},
                    ...
                ],
                "examplesPrompt": [
                    {"title": "string", "description": "string", "promptText": "string"},
                    ...
                ]
            } (Optional)
        :return: dict - The API response as a JSON object containing details about the updated assistant.
        """
        data = {
                "status": status,
                "action": action,
                "llmSettings": llm_settings,
                "welcomeData": welcome_data
        }

        if revision_id:
            data["revisionId"] = revision_id

        if name:
            data["name"] = name

        if prompt:
            data["prompt"] = name

        if prompt:
            data["description"] = description

        endpoint = UPDATE_ASSISTANT_V1.format(id=assistant_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to update assistant with ID '{assistant_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update assistant with ID '{assistant_id}': {response.text}")

    def delete_assistant(
            self,
            assistant_id: str
    ) -> dict:
        """
        Deletes an existing assistant by its ID.

        :param assistant_id: str - The ID of the assistant to be deleted. (Required)
        :return: dict - The API response as a JSON object indicating the result of the delete operation.
        """
        endpoint = UPDATE_ASSISTANT_V1.format(id=assistant_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete assistant with ID '{assistant_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete assistant with ID '{assistant_id}': {response.text}")

    def send_chat_request(
            self,
            assistant_name: str,
            messages: list[dict],
            revision: str = None,
            revision_name: str = None,
            variables: list[dict] = None
    ) -> dict:
        """
        Sends a chat request to the specified assistant.

        :param assistant_name: str - The name of the assistant to which the chat request is sent. (Required)
        :param messages: list - The chat request data. Must be an array of dictionaries, where each dictionary contains
            "role" and "content" keys. (Required)
        :param revision: int - The revision number of the assistant. (Required)
        :param revision_name: str - The name of the revision to be used for the chat request. (Required)
        :return: dict - The API response as a JSON object with the result of the chat request.
        """
        data = {
            "assistant": assistant_name,
            "messages": messages,
            "revision": revision,
            "revisionName": revision_name,
            "variables": variables
        }

        response = self.api_service.post(
            endpoint=SEND_CHAT_REQUEST_V1,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to send chat request to assistant '{assistant_name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to send chat request to assistant '{assistant_name}': {response.text}")

    def get_request_status(
            self,
            request_id: str
    ) -> dict:
        """
        Retrieves the status of a specific request using its request ID.

        :param request_id: str - The unique identifier of the request. (Required)
        :return: dict - The API response as a JSON object containing the status of the request.
        """
        endpoint = GET_REQUEST_STATUS_V1.format(id=request_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get request status for ID '{request_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get request status for ID '{request_id}': {response.text}")

    def cancel_request(
            self,
            request_id: str
    ) -> dict:
        """
        Cancels a specific request using its request ID.

        :param request_id: str - The unique identifier of the request to be canceled. (Required)
        :return: dict - The API response as a JSON object indicating the outcome of the cancellation request.
        """
        endpoint = CANCEL_REQUEST_V1.format(id=request_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data={
                "requestId": request_id
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to cancel request with ID '{request_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to cancel request with ID '{request_id}': {response.text}")



