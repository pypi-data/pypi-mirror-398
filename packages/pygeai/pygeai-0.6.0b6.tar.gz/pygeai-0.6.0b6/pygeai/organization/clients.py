import json
from json import JSONDecodeError

from pygeai import logger
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.organization.endpoints import GET_ASSISTANT_LIST_V1, GET_PROJECT_LIST_V1, GET_PROJECT_V1, \
    CREATE_PROJECT_V1, UPDATE_PROJECT_V1, DELETE_PROJECT_V1, GET_PROJECT_TOKENS_V1, GET_REQUEST_DATA_V1
from pygeai.core.base.clients import BaseClient


class OrganizationClient(BaseClient):

    def get_assistant_list(
            self,
            detail: str = "summary"
    ) -> dict:
        """
        Retrieves a list of assistants with the specified level of detail.

        :param detail: str - The level of detail to include in the response. Possible values:
            - "summary": Provides a summarized list of assistants. (Default)
            - "full": Provides a detailed list of assistants. (Optional)
        :return: AssistantListResponse - The API response containing the list of assistants and the project.
        """
        response = self.api_service.get(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": detail})
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get assistant list: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get assistant list: {response.text}")

    def get_project_list(
            self,
            detail: str = "summary",
            name: str = None
    ) -> dict:
        """
        Retrieves a list of projects based on the specified level of detail and optional project name.

        :param detail: str - The level of detail to include in the response. Possible values:
            - "summary": Provides a summarized list of projects. (Default)
            - "full": Provides a detailed list of projects. (Optional)
        :param name: str - (Optional) Filters the project list by an exact project name match.
        :return: dict - The API response containing the list of projects in JSON format.
        """
        if detail and name:
            response = self.api_service.get(
                endpoint=GET_PROJECT_LIST_V1,
                params={
                    "detail": detail,
                    "name": name
                }
            )
        else:
            response = self.api_service.get(
                endpoint=GET_PROJECT_LIST_V1,
                params={
                    "detail": detail
                }
            )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get project list: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get project list: {response.text}")

    def get_project_data(
            self,
            project_id: str
    ) -> dict:
        """
        Retrieves detailed information about a specific project based on its unique project ID.

        :param project_id: str - The GUID of the project (required).
        :return: dict - The API response containing the project details in JSON format.
        """
        endpoint = GET_PROJECT_V1.format(id=project_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get project data for ID '{project_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get project data for ID '{project_id}': {response.text}")

    def create_project(
            self,
            name: str,
            email: str,
            description: str = None,
            usage_limit: dict = None
    ) -> dict:
        """
        Creates a new project with the provided details. Optionally, a usage limit can be specified.

        :param name: str - The name of the new project (required).
        :param email: str - The email address of the project administrator (required).
        :param description: str - A description of the new project (optional).
        :param usage_limit: dict - A dictionary specifying the usage limits for the project. If provided, it must include usage type and thresholds (optional).
        :return: dict - The API response with details of the created project in JSON format.
        """
        if usage_limit and any(usage_limit):
            response = self.api_service.post(
                endpoint=CREATE_PROJECT_V1,
                data={
                    "name": name,
                    "administratorUserEmail": email,
                    "description": description,
                    "usageLimit": usage_limit
                }
            )
        else:
            response = self.api_service.post(
                endpoint=CREATE_PROJECT_V1,
                data={
                    "name": name,
                    "administratorUserEmail": email,
                    "description": description
                }
            )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to create project with name '{name}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create project with name '{name}': {response.text}")

    def update_project(
            self,
            project_id: str,
            name: str,
            description: str = None
    ) -> dict:
        """
        Updates an existing project with the provided details.

        :param project_id: str - The unique identifier (GUID) of the project to update (required).
        :param name: str - The new name for the project (required).
        :param description: str - A new description for the project (optional).
        :return: dict - The API response containing the updated project details in JSON format.
        """
        endpoint = UPDATE_PROJECT_V1.format(id=project_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "name": name,
                "description": description
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to update project with ID '{project_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update project with ID '{project_id}': {response.text}")

    def delete_project(
            self,
            project_id
    ) -> dict:
        """
        Deletes an existing project using its unique identifier.

        :param project_id: str - The unique identifier (GUID) of the project to delete (required).
        :return: dict - The API response confirming the deletion of the project, in JSON format.
        """
        endpoint = DELETE_PROJECT_V1.format(id=project_id)
        response = self.api_service.delete(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete project with ID '{project_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete project with ID '{project_id}': {response.text}")

    def get_project_tokens(
            self,
            project_id
    ) -> dict:
        """
        Retrieves the tokens associated with a specific project using its unique identifier.

        :param project_id: str - The unique identifier (GUID) of the project (required).
        :return: dict - The API response containing the tokens associated with the project, in JSON format.
        """
        endpoint = GET_PROJECT_TOKENS_V1.format(id=project_id)
        response = self.api_service.get(endpoint=endpoint)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get tokens for project with ID '{project_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get tokens for project with ID '{project_id}': {response.text}")

    def export_request_data(
            self,
            assistant_name: str = None,
            status: str = None,
            skip: int = 0,
            count: int = 0
    ) -> dict:
        """
        Exports request data based on the specified filters such as assistant name, status, and pagination parameters.

        :param assistant_name: str - The name of the assistant to filter the request data by (optional).
        :param status: str - The status to filter the request data by (optional).
        :param skip: int - The number of entries to skip in the response (default is 0).
        :param count: int - The number of entries to retrieve in the response (default is 0).
        :return: dict - The API response containing the requested data, in JSON format.
        """
        response = self.api_service.get(
            endpoint=GET_REQUEST_DATA_V1,
            params={
                "assistantName": assistant_name,
                "status": status,
                "skip": skip,
                "count": count
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to export request data: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to export request data: {response.text}")
