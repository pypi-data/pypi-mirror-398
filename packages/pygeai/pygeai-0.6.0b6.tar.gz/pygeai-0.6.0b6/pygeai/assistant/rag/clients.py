import json
import logging
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from pygeai import logger
from pygeai.assistant.rag.endpoints import GET_ASSISTANTS_FROM_PROJECT_V1, GET_ASSISTANT_V1, CREATE_ASSISTANT_V1, \
    UPDATE_ASSISTANT_V1, DELETE_ASSISTANT_V1, GET_DOCUMENTS_V1, DELETE_ALL_DOCUMENTS_V1, RETRIEVE_DOCUMENT_V1, \
    UPLOAD_DOCUMENT_V1, DELETE_DOCUMENT_V1, EXECUTE_QUERY_V1
from pygeai.core.base.clients import BaseClient
import urllib.parse

from pygeai.core.common.exceptions import InvalidAPIResponseException


class RAGAssistantClient(BaseClient):

    def get_url_safe_name(self, name: str) -> str:
        return urllib.parse.quote_plus(name)

    def get_assistants_from_project(self) -> dict:
        response = self.api_service.get(endpoint=GET_ASSISTANTS_FROM_PROJECT_V1)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get assistants from project: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get assistants from project: {response.text}")

    def get_assistant_data(self, name: str) -> dict:
        endpoint = GET_ASSISTANT_V1.format(name=name)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get assistant data for name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get assistant data for name '{name}': {response.text}")

    def create_assistant(
            self,
            name: str,
            description: str = None,
            template: str = None,
            search_options: dict = None,
            index_options: dict = None,
            welcome_data: dict = None
    ) -> dict:
        """
        Creates a RAG Assistant with configurable options for search, indexing, and welcome data.

        :param name: str - The name of the RAG assistant (required).
        :param description: str, optional - A description of the RAG assistant's purpose or functionality.
        :param template: str, optional - Name of an existing RAG template to base the configuration on. Defaults to None.
        :param search_options: dict, optional - A dictionary containing search configuration options.
            - "history_count": int - Number of historical interactions to include in the search context.
            - "llm": A dictionary with LLM configuration:
                - "cache": bool - Whether to enable caching for the LLM.
                - "frequencyPenalty": float - Frequency penalty parameter for LLM responses.
                - "maxTokens": int - Maximum number of tokens for LLM responses.
                - "modelName": str - Name of the LLM model.
                - "n": int - Number of completions to generate per prompt.
                - "presencePenalty": float - Presence penalty parameter for LLM responses.
                - "provider": str - LLM provider.
                - "stream": bool - Whether to enable streaming for LLM responses.
                - "temperature": float - Sampling temperature for LLM responses.
                - "topP": float - Top-p sampling value.
                - "type": str - LLM type, such as "json_object".
                - "verbose": bool - Whether to enable verbose output.
            - "search": A dictionary with search configuration:
                - "k": int - Number of documents to retrieve.
                - "type": str - Search type, e.g., "similarity" or "mmr".
                - "fetchK": int - Number of documents to fetch when using MMR.
                - "lambda": float - Lambda parameter for MMR.
                - "prompt": str - Custom prompt for search.
                - "returnSourceDocuments": bool - Whether to return source documents.
                - "scoreThreshold": float - Minimum score threshold for retrieved documents.
                - "template": str - Template for search.
            - "retriever": A dictionary with retriever configuration:
                - "type": str - Retriever type, e.g., "vectorStore".
                - "searchType": str - Specific search type for retrievers.
                - "step": str - Retrieval step, e.g., "all" or "documents".
                - "prompt": str - Custom retriever prompt.
        :param index_options: dict, optional - A dictionary containing index configuration options.
            - "chunks": Configuration for document chunking:
                - "chunkOverlap": int - Overlap size between chunks in the main document.
                - "chunk_size": int - Size of each chunk in the main document.
            - "useParentDocument": bool - Whether to enable parent-child relationships.
            - "child_document": Configuration for child documents:
                - "childK": float - Parameter for child document processing.
                - "chunk_size": float - Chunk size for child documents.
                - "chunkOverlap": float - Overlap size between child document chunks.
        :param welcome_data: dict, optional - A dictionary containing welcome data for the assistant.
            - "title": str - Title of the welcome message.
            - "description": str - Description of the welcome message.
            - "features": A list of features:
                - "title": str - Title of the feature.
                - "description": str - Description of the feature.
            - "examplesPrompt": A list of example prompts:
                - "title": str - Title of the example prompt.
                - "description": str - Description of the example prompt.
                - "promptText": str - Text of the example prompt.

        :return: dict - The API response containing details of the created RAG assistant.
    """
        data = {
            "name": name,
            "description": description,
            "template": template,
            "searchOptions": search_options,
            "indexOptions": index_options,
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
            name: str,
            status: int,
            description: str = None,
            template: str = None,
            search_options: dict = None,
            welcome_data: dict = None
    ) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = UPDATE_ASSISTANT_V1.format(name=name)

        data = {
            "status": status,
        }
        if description:
            data["description"] = description

        if template:
            data["template"] = template

        if search_options:
            data["searchOptions"] = search_options

        if welcome_data:
            data["welcomeData"] = welcome_data

        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to update assistant with name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update assistant with name '{name}': {response.text}")

    def delete_assistant(self, name: str) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = DELETE_ASSISTANT_V1.format(name=safe_name)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete assistant with name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete assistant with name '{name}': {response.text}")

    def get_documents(
            self,
            name: str,
            skip: int = 0,
            count: int = 10
    ) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = GET_DOCUMENTS_V1.format(name=safe_name)
        response = self.api_service.get(
            endpoint=endpoint,
            params={
                "skip": skip,
                "count": count
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get documents for assistant '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get documents for assistant '{name}': {response.text}")

    def delete_all_documents(self, name: str) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = DELETE_ALL_DOCUMENTS_V1.format(name=safe_name)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete all documents for assistant '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete all documents for assistant '{name}': {response.text}")

    def retrieve_document(self, name: str, document_id: str) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = RETRIEVE_DOCUMENT_V1.format(name=safe_name, id=document_id)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve document with ID '{document_id}' for assistant '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve document with ID '{document_id}' for assistant '{name}': {response.text}")

    def upload_document(
            self,
            name: str,
            file_path: str,
            upload_type: str = "multipart",
            metadata: dict = None,
            content_type: str = "application/pdf"
    ) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = UPLOAD_DOCUMENT_V1.format(name=safe_name)

        if upload_type == "binary":
            response = self._upload_binary_document(endpoint, file_path, content_type)
        elif upload_type == "multipart":
            response = self._upload_multipart_document(endpoint, file_path, content_type, metadata)
        else:
            raise ValueError("Invalid upload_type. Use 'binary' or 'multipart'.")

        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to upload document for assistant '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to upload document for assistant '{name}': {response.text}")

    def _upload_binary_document(self, endpoint: str, file_path: str, content_type: str):
        """
        Uploads a binary file to the specified API endpoint.

        :param endpoint: str - The API endpoint where the file will be uploaded.
        :param file_path: str - The path to the file to be uploaded.
        :param content_type: str - The MIME type of the file (e.g., "application/pdf", "text/plain").
        :return: Response object from the API request.
        """
        headers = dict()
        headers["filename"] = Path(file_path).name
        headers["Content-Type"] = content_type

        with open(file_path, "rb") as file:
            response = self.api_service.post_file_binary(
                endpoint=endpoint,
                headers=headers,
                file=file
            )
        return response

    def _upload_multipart_document(self, endpoint: str, file_path: str, content_type: str, metadata: Any):
        """
        Uploads a file using multipart/form-data encoding, optionally including metadata.

        :param endpoint: str - The API endpoint where the file will be uploaded.
        :param file_path: str - The path to the file to be uploaded.
        :param content_type: str - The MIME type of the file (e.g., "application/pdf", "text/plain").
        :param metadata: Any - Metadata to be included in the request. Can be a dictionary (sent as JSON) or a file path.

        :raises ValueError: If metadata is neither a dictionary nor a valid file path.
        :return: Response object from the API request, or None if an error occurs.
        """
        files_payload = []
        file_name = Path(file_path).name
        file_obj = open(file_path, "rb")
        files_payload.append(
            ("file", (file_name, file_obj, content_type))
        )
        if metadata:
            if isinstance(metadata, dict):
                files_payload.append(
                    ("metadata", (None, json.dumps(metadata), "application/json"))
                )
            elif isinstance(metadata, str) and Path(metadata).is_file():
                metadata_path = Path(metadata)
                files_payload.append(
                    ("metadata", metadata_path.open("rb"))
                )
            else:
                raise ValueError("Metadata should be a dictionary or a valid file path.")
        try:
            response = self.api_service.post_files_multipart(
                endpoint=endpoint,
                files=files_payload
            )
        except Exception as e:
            logging.error(f"Unable to receive answer from POST request: {e}")
        else:
            return response
        finally:
            for _, (file_name, file_obj, _) in files_payload:
                if hasattr(file_obj, "close"):
                    file_obj.close()

    def delete_document(self, name: str, document_id: str) -> dict:
        safe_name = self.get_url_safe_name(name)
        endpoint = DELETE_DOCUMENT_V1.format(name=safe_name, id=document_id)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete document with ID '{document_id}' for assistant '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete document with ID '{document_id}' for assistant '{name}': {response.text}")

    def execute_query(self, query: dict) -> dict:
        response = self.api_service.post(
            endpoint=EXECUTE_QUERY_V1,
            data=query
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to execute query: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to execute query: {response.text}")

