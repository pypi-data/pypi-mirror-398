import json
from json import JSONDecodeError

from pygeai import logger
from pygeai.admin.endpoints import GET_API_TOKEN_VALIDATION_V1, GET_AUTHORIZED_ORGANIZATIONS_V1, \
    GET_AUTHORIZED_PROJECTS_V1, GET_PROJECT_VISIBILITY_V1, GET_PROJECT_API_TOKEN_V1
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class AdminClient(BaseClient):

    def validate_api_token(self) -> dict:
        """
        Validates the API token and retrieves associated organization and project information.

        :return: dict - The API response containing organization and project information in JSON format.
        """
        response = self.api_service.get(endpoint=GET_API_TOKEN_VALIDATION_V1)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to validate API token: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to validate API token: {response.text}")

    def get_authorized_organizations(self) -> dict:
        """
        Retrieves the list of organizations that the user is authorized to access.

        :return: dict - The API response containing the list of authorized organizations in JSON format.
        """
        response = self.api_service.get(endpoint=GET_AUTHORIZED_ORGANIZATIONS_V1)
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve authorized organizations: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve authorized organizations: {response.text}")

    def get_authorized_projects_by_organization(
            self,
            organization: str
    ) -> dict:
        """
        Retrieves the list of projects that the user is authorized to access within a specific organization.

        :param organization: str - The name or unique identifier of the organization.
        :return: dict - The API response containing the list of authorized projects in JSON format.
        """
        response = self.api_service.get(
            endpoint=GET_AUTHORIZED_PROJECTS_V1,
            params={
                "organization": organization
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve authorized projects for organization '{organization}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve authorized projects for organization {organization}: {response.text}")

    def get_project_visibility(
            self,
            organization: str,
            project: str,
            access_token: str
    ) -> dict:
        """
       Determines if a GAM user has visibility for a given organization-project combination.

       :param organization: str - The unique identifier of the organization. (required)
       :param project: str - The unique identifier of the project. (required)
       :param access_token: str - The GAM access token. (required)
       :return: dict - The API response. An empty JSON object (`{}`) if the user has visibility,
                or an error response if visibility is denied or the request parameters are invalid.
       :raises:
           - 403 Forbidden: Access token is valid, but the user lacks visibility for the organization-project.
           - 403 Forbidden: Project is inactive.
           - 403 Forbidden: Organization or project IDs are invalid (no match in the system).
           - 400 Bad Request: Missing required parameters (`organization`, `project`, or `accessToken`).
           - 401 Unauthorized: Invalid or expired access token.
       """
        response = self.api_service.get(
            endpoint=GET_PROJECT_VISIBILITY_V1,
            params={
                "organization": organization,
                "project": project,
                "accessToken": access_token
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve project visibility for organization '{organization}' and project '{project}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve project visibility for organization {organization} and project {project}: {response.text}")

    def get_project_api_token(
            self,
            organization: str,
            project: str,
            access_token: str
    ) -> dict:
        """
        Retrieves an active API token for a project based on the provided organization-project combination and GAM access token.

        :param organization: str - The unique identifier of the organization. (required)
        :param project: str - The unique identifier of the project. (required)
        :param access_token: str - The GAM access token. (required)
        :return: dict - The API response containing the project API token in the following format:
                 {"apiToken": "string"}
        :raises:
            - 403 Forbidden: Access token is valid, but the user lacks access to the organization-project.
            - 403 Forbidden: Project is inactive.
            - 403 Forbidden: Organization or project IDs are invalid (no match in the system).
            - 400 Bad Request: Missing required parameters (`organization`, `project`, or `accessToken`).
            - 401 Unauthorized: Invalid or expired access token.
            - 401 Unauthorized: No active API token found for the project.
        """
        response = self.api_service.get(
            endpoint=GET_PROJECT_API_TOKEN_V1,
            params = {
                "organization": organization,
                "project": project,
                "accessToken": access_token
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve project API token for organization '{organization}' and project '{project}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve project API token for organization {organization} and project {project}: {response.text}")
