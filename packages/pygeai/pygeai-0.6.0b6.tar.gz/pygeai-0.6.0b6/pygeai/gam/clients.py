from json import JSONDecodeError

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import MissingRequirementException, InvalidAPIResponseException
from pygeai.gam.endpoints import GET_ACCESS_TOKEN_V2, GET_USER_INFO_V2, IDP_SIGNIN_V1


class GAMClient(BaseClient):

    def generate_signing_url(
            self,
            client_id: str = None,
            redirect_uri: str = None,
            scope: str = "gam_user_data",
            state: str = None,
            response_type: str = "code"
    ):
        """
        Generates the URL for the GAM OAuth 2.0 signin endpoint to initiate user authentication.
        This method does not perform the signin itself but provides the URL for redirection in a browser-based flow.

        :param client_id: str - Client ID of the application. Required.
        :param redirect_uri: str - Callback URL configured in the application. Required.
        :param scope: str - Scope of the user account to access (e.g., "gam_user_data").
            Defaults to "gam_user_data".
        :param state: str - Random string to store the status before the request. Required.
        :param response_type: str - Response type for the signin request. Defaults to "code".
        :return: str - The URL to redirect to for user authentication in a browser.
        :raises MissingRequirementException: If required parameters are missing.
        """
        if not all([client_id, redirect_uri, state]):
            raise MissingRequirementException("client_id, redirect_uri, and state are required.")

        params = {
            "response_type": response_type,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state
        }
        if scope:
            params["scope"] = scope

        endpoint = f"{self.api_service.base_url}{IDP_SIGNIN_V1}"
        redirect_url = f"{endpoint}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        return redirect_url

    def get_access_token(
            self,
            client_id: str = None,
            client_secret: str = None,
            grant_type: str = "password",
            authentication_type_name: str = "local",
            scope: str = "gam_user_data",
            username: str = None,
            password: str = None,
            initial_properties: dict = None,
            repository: str = None,
            request_token_type: str = "OAuth"
    ):
        """
        Retrieves an access token by sending a POST request to the GAM OAuth 2.0 access token endpoint.

        :param client_id: str - Application Client ID. Required.
        :param client_secret: str - Application Client Secret. Required.
        :param grant_type: str - Grant type for authentication. Must be "password". Defaults to "password".
        :param authentication_type_name: str - Authentication type name. Defaults to "local".
        :param scope: str - Scope of the user account to access (e.g., "gam_user_data+gam_user_roles").
            Defaults to "gam_user_data".
        :param username: str - Username of the user to be authenticated. Required.
        :param password: str - Password of the user to be authenticated. Required.
        :param initial_properties: dict - User custom properties array (e.g., [{"Id":"Company","Value":"GeneXus"}]). Optional.
        :param repository: str - Repository identifier, used only if IDP is multitenant. Optional.
        :param request_token_type: str - Determines the token type to return and security policy.
            Options are "OAuth" or "Web". Defaults to "OAuth".
        :return: dict or str - Access token response containing access_token, token_type, expires_in,
            refresh_token, scope, and user_guid; returns raw text if JSON parsing fails.
        """
        data = {
            "grant_type": grant_type,
            "authentication_type_name": authentication_type_name,
            "scope": scope,
            "request_token_type": request_token_type
        }
        if client_id is not None:
            data["client_id"] = client_id
        if client_secret is not None:
            data["client_secret"] = client_secret
        if username is not None:
            data["username"] = username
        if password is not None:
            data["password"] = password
        if initial_properties is not None:
            data["initial_properties"] = initial_properties
        if repository is not None:
            data["repository"] = repository

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.api_service.post(
            endpoint=GET_ACCESS_TOKEN_V2,
            data=data,
            headers=headers,
            form=True
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get access token: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get access token: {response.text}")

    def get_user_info(
            self,
            access_token: str
    ):
        """
        Retrieves user information by sending a GET request to the GAM OAuth 2.0 userinfo endpoint.

        :param access_token: str - Access token obtained from the access_token endpoint. Required.
        :return: dict or str - User information response containing guid, username, email, and other user
            details based on requested scopes; returns raw text if JSON parsing fails.
        """
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.api_service.get(
            endpoint=GET_USER_INFO_V2,
            headers=headers
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get user info: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get user info: {response.text}")

    def refresh_access_token(
            self,
            client_id: str = None,
            client_secret: str = None,
            grant_type: str = "refresh_token",
            refresh_token: str = None
    ):
        """
        Refreshes an access token by sending a GET request to the GAM OAuth 2.0 access token endpoint.

        :param client_id: str - Application Client ID. Required.
        :param client_secret: str - Application Client Secret. Required.
        :param grant_type: str - Grant type for authentication. Must be "refresh_token". Defaults to "refresh_token".
        :param refresh_token: str - Refresh token obtained from a previous access token response. Required.
        :return: dict or str - New access token response containing access_token, token_type, expires_in,
            refresh_token, scope, and user_guid; returns raw text if JSON parsing fails.
        """
        data = {
            "grant_type": grant_type,
        }
        if client_id is not None:
            data["client_id"] = client_id
        if client_secret is not None:
            data["client_secret"] = client_secret
        if refresh_token is not None:
            data["refresh_token"] = refresh_token

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = self.api_service.post(
            endpoint=GET_ACCESS_TOKEN_V2,
            data=data,
            headers=headers,
            form=True
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to refresh access token: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to refresh access token: {response.text}")

    def get_authentication_types(self):
        response = self.api_service.get(
            endpoint=GET_ACCESS_TOKEN_V2,
            params={},
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get authentication types: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get authentication types: {response.text}")
