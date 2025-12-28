from json import JSONDecodeError
from typing import Optional, List, Dict

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.core.secrets.endpoints import LIST_SECRETS_V1, GET_SECRET_V1, CREATE_SECRET_V1, UPDATE_SECRET_V1, \
    SET_SECRET_ACCESSES_V1, GET_SECRET_ACCESSES_V1


class SecretClient(BaseClient):
    """
    Client for interacting with secret-related endpoints of the API.
    """

    def list_secrets(
        self,
        name: str = None,
        id: str = None,
        start: int = 0,
        count: int = 10
    ) -> dict:
        """
        Retrieves a list of secrets with optional filtering and pagination.

        This method sends a GET request to the LIST_SECRETS_V1 endpoint to fetch a list of secrets.
        Optional query parameters can be used to filter by name or ID and control pagination.

        :param name: str, optional - Filter secrets by name.
        :param id: str, optional - Filter secrets by ID.
        :param start: int, optional - Starting index for pagination, defaults to 0.
        :param count: int, optional - Number of secrets to return, defaults to 10.
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        """
        params = {
            "name": name,
            "id": id,
            "start": start,
            "count": count
        }
        params = {k: v for k, v in params.items() if v is not None}

        response = self.api_service.get(
            endpoint=LIST_SECRETS_V1,
            params=params
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to list secrets with params {params}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list secrets with params {params}: {response.text}")

    def get_secret(self, secret_id: str) -> dict:
        """
        Retrieves a secret by its ID.

        This method sends a GET request to the GET_SECRET_V1 endpoint to fetch details of a specific secret
        identified by its ID.

        :param secret_id: str - The unique identifier of the secret to retrieve.
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        :raises ValueError: If secret_id is not provided or is empty.
        """
        if not secret_id:
            raise ValueError("secret_id must be provided and non-empty.")

        endpoint = GET_SECRET_V1.format(secretID=secret_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get secret with ID '{secret_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get secret with ID '{secret_id}': {response.text}")

    def create_secret(
            self,
            name: str,
            secret_string: str,
            description: Optional[str] = None
    ) -> dict:
        """
        Creates a new secret with the specified details.

        This method sends a POST request to the CREATE_SECRET_V1 endpoint to create a secret
        with the provided name, secret string, and optional description.

        :param name: str - The name of the secret.
        :param secret_string: str - The secret value to store.
        :param description: str, optional - A description of the secret.
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        :raises ValueError: If name or secret_string is not provided or is empty.
        """
        if not name or not secret_string:
            raise ValueError("name and secret_string must be provided and non-empty.")

        secret_definition = {
            "name": name,
            "secretString": secret_string,
            "description": description
        }
        secret_definition = {k: v for k, v in secret_definition.items() if v is not None}

        data = {
            "secretDefinition": secret_definition
        }
        response = self.api_service.post(
            endpoint=CREATE_SECRET_V1,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to create secret with name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create secret with name '{name}': {response.text}")

    def update_secret(
            self,
            secret_id: str,
            name: str,
            secret_string: str,
            description: Optional[str] = None
    ) -> dict:
        """
        Updates an existing secret identified by its ID with the specified details.

        This method sends a PUT request to the UPDATE_SECRET_V1 endpoint to update a secret
        with the provided name, secret string, and optional description.

        :param secret_id: str - The unique identifier of the secret to update.
        :param name: str - The updated name of the secret.
        :param secret_string: str - The updated secret value.
        :param description: str, optional - The updated description of the secret.
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        :raises ValueError: If secret_id, name, or secret_string is not provided or is empty.
        """
        if not secret_id or not name or not secret_string:
            raise ValueError("secret_id, name, and secret_string must be provided and non-empty.")

        secret_definition = {
            "name": name,
            "secretString": secret_string,
            "description": description
        }

        secret_definition = {k: v for k, v in secret_definition.items() if v is not None}

        data = {
            "secretDefinition": secret_definition
        }
        endpoint = UPDATE_SECRET_V1.format(secretID=secret_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to update secret with ID '{secret_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update secret with ID '{secret_id}': {response.text}")

    def set_secret_accesses(
            self,
            secret_id: str,
            access_list: List[Dict[str, str]]
    ) -> dict:
        """
        Sets access configurations for a secret identified by its ID.

        This method sends a POST request to the SET_SECRET_ACCESSES_V1 endpoint to set the access
        configurations for a secret, specifying the access level and principal type for each entry.

        :param secret_id: str - The unique identifier of the secret.
        :param access_list: List[Dict[str, str]] - A list of access configurations, each containing
            'accessLevel' (e.g., 'write') and 'principalType' (e.g., 'service').
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        :raises ValueError: If secret_id is not provided or empty, or if access_list is empty or invalid.
        """
        if not secret_id:
            raise ValueError("secret_id must be provided and non-empty.")
        if not access_list:
            raise ValueError("access_list must be provided and non-empty.")

        for access in access_list:
            if not all(key in access for key in ["accessLevel", "principalType"]):
                raise ValueError("Each access entry must contain 'accessLevel' and 'principalType'.")
            if not all(isinstance(access[key], str) and access[key] for key in ["accessLevel", "principalType"]):
                raise ValueError("'accessLevel' and 'principalType' must be non-empty strings.")

        data = {
            "secretDefinition": {
                "accessList": access_list
            }
        }
        endpoint = SET_SECRET_ACCESSES_V1.format(secretID=secret_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to set accesses for secret with ID '{secret_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set accesses for secret with ID '{secret_id}': {response.text}")

    def get_secret_accesses(self, secret_id: str) -> dict:
        """
        Retrieves access configurations for a secret identified by its ID.

        This method sends a GET request to the GET_SECRET_ACCESSES_V1 endpoint to fetch the access
        configurations for a specific secret.

        :param secret_id: str - The unique identifier of the secret.
        :return: dict - The API response as a dictionary if JSON parsing succeeds, otherwise the raw response text.
        :raises ValueError: If secret_id is not provided or is empty.
        """
        if not secret_id:
            raise ValueError("secret_id must be provided and non-empty.")

        endpoint = GET_SECRET_ACCESSES_V1.format(secretID=secret_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get accesses for secret with ID '{secret_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get accesses for secret with ID '{secret_id}': {response.text}")
