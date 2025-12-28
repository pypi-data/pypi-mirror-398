from json import JSONDecodeError

from pygeai import logger
from pygeai.auth.endpoints import GET_USER_PROFILE_INFO, GET_OAUTH2_ACCESS_TOKEN
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class AuthClient(BaseClient):

    def get_oauth2_access_token(
            self,
            client_id: str,
            username: str,
            password: str,
            scope: str = "gam_user_data gam_user_roles"
    ) -> dict:
        """
        Retrieves the list of projects that the user is authorized to access within a specific organization.

        :param client_id: str - The client identifier provided by Globant
        :param username: str - Username for authentication
        :param password: str - Password for authentication
        :param scope: str - Space-separated list of requested scopes
        :return: dict - The API response containing the list of authorized projects in JSON format.
        """
        response = self.api_service.get(
            endpoint=GET_OAUTH2_ACCESS_TOKEN,
            params={
                "client_id": client_id,
                "scope": scope,
                "username": username,
                "password": password
            }
        )
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to obtain Oauth2 access token: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to  obtain Oauth2 access token: {response.text}")

    def get_user_profile_information(self, access_token: str) -> dict:
        """
        Get user profile information

        :param access_token: str - Token obtained in the POST to /oauth/access_token
        :return: dict - The API response containing the user profile information
        """
        self.api_service.token = access_token
        response = self.api_service.get(endpoint=GET_USER_PROFILE_INFO)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve user profile information: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve user profile information: {response.text}")
