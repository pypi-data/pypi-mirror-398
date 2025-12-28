import json
from typing import Optional, List, Dict
import requests as req
from pygeai import logger
from pygeai.core.common.exceptions import InvalidResponseException
from pygeai.core.services.response import ResponseMock

FAILED_REQUEST_RESPONSE = ResponseMock(
    status_code=0,
    content=json.dumps({"error": "Unknown error occurred"}),
    url=None,
    reason="Unknown Error"
)


class ApiService:
    """
    Generic service for interacting with RESTful APIs.

    :param base_url: str - The base URL of the API.
    :param username: str - Username for basic authentication (optional).
    :param password: str - Password for basic authentication (optional).
    :param token: str - Bearer token for authentication (optional).
    """

    def __init__(self, base_url, username: str = None, password: str = None, token: str = None):
        self._base_url = base_url
        self._username = username
        self._password = password
        self._token = token

    @property
    def base_url(self):
        return self._base_url

    @property
    def username(self):
        return self._username

    @property
    def password(self):
        return self._password

    @property
    def token(self):
        return self._token

    def get(self, endpoint: str, params: dict = None, headers: dict = None, verify: bool = True):
        """
        Sends a GET request to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a GET request
        using the provided query parameters and headers. Authentication is applied if username/password or token
        is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param params: dict, optional - Query parameters to include in the request.
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :return: Response - The response object from the GET request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                response = session.get(
                    url=url,
                    params=params,
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Error sending GET request: {e}")
            raise InvalidResponseException(f"Error sending GET request: {e}")
        else:
            logger.debug(f"GET request to URL: {response.url}")

        return response

    def post(self, endpoint: str, data: dict, headers: dict = None, verify: bool = True, form: bool = False):
        """
        Sends a POST request to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a POST request
        with the provided data, either as JSON or form data. Authentication is applied if username/password or token
        is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param data: dict - The payload to include in the POST request.
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :param form: bool - Whether to send data as form data instead of JSON (default: False).
        :return: Response - The response object from the POST request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                if form:
                    response = session.post(
                        url=url,
                        data=data,
                        headers=headers
                    )
                else:
                    response = session.post(
                        url=url,
                        json=data,
                        headers=headers
                    )
        except Exception as e:
            logger.error(f"Error sending POST request: {e}")
            raise InvalidResponseException(f"Error sending POST request: {e}")
        else:
            logger.debug(f"POST request to URL: {response.url}")

        return response

    def stream_post(
            self,
            endpoint: str,
            data: dict,
            headers: dict = None,
            verify: bool = True,
            form: bool = False
    ):
        """
        Sends a streaming POST request to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a streaming POST
        request with the provided data, either as JSON or form data. It yields chunks of the response as they are
        received. Authentication is applied if username/password or token is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param data: dict - The payload to include in the POST request.
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :param form: bool - Whether to send data as form data instead of JSON (default: False).
        :return: Generator[str] - Yields chunks of the streaming response as strings.
        :raises InvalidResponseException: If an error occurs during the request execution or streaming.
        """
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (self.username, self.password)
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                if form:
                    response = session.post(
                        url=url,
                        data=data,
                        headers=headers,
                        stream=True
                    )
                else:
                    response = session.post(
                        url=url,
                        json=data,
                        headers=headers,
                        stream=True
                    )

                response.raise_for_status()
                logger.debug(f"Streaming POST request to URL {response.url}")
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        yield line

        except Exception as e:
            logger.error(f"Error sending streaming POST request: {e}")
            raise InvalidResponseException(f"Error sending streaming POST request: {e}")

    def post_file_binary(
            self,
            endpoint: str,
            headers: dict = None,
            verify: bool = True,
            file=None
    ):
        """
        Sends a POST request with a binary file to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a POST request
        with the provided binary file data. Authentication is applied if username/password or token is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :param file: Binary file data to include in the request.
        :return: Response - The response object from the POST request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                response = session.post(
                    url=url,
                    headers=headers,
                    data=file
                )
        except Exception as e:
            logger.error(f"Error sending POST request with binary file: {e}")
            raise InvalidResponseException(f"Error sending POST request with binary file: {e}")
        else:
            logger.debug(f"POST request with binary file to URL: {response.url}")

        return response

    def post_files_multipart(
            self,
            endpoint: str,
            data: Optional[dict] = None,
            headers: Optional[dict] = None,
            verify: bool = True,
            files: Optional[Dict[str, str]] = None,
    ):
        """
        Sends a POST request with multipart files to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a POST request
        with multipart form data, including files and optional additional data. Authentication is applied if
        username/password or token is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param data: dict, optional - Additional form data to include in the request.
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :param files: Dict[str, str], optional - Dictionary of file names and their corresponding file paths or file-like objects.
        :return: Response - The response object from the POST request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                # headers["Content-Type"] = "multipart/form-data"

                response = session.post(
                    url=url,
                    headers=headers,
                    data=data,
                    files=files
                )
        except Exception as e:
            logger.error(f"Error sending POST request with files multipart: {e}")
            raise InvalidResponseException(f"Error sending POST request with files multipart request: {e}")
        else:
            logger.debug(f"POST request with multipart files to URL: {response.url}")

        return response

    def put(self, endpoint: str, data: dict, headers: dict = None, verify: bool = True):
        """
        Sends a PUT request to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a PUT request
        with the provided JSON data. Authentication is applied if username/password or token is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param data: dict - The payload to include in the PUT request (sent as JSON).
        :param headers: dict, optional - Additional headers to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :return: Response - The response object from the PUT request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                headers["Content-Type"] = "application/json"

                response = session.put(
                    url=url,
                    json=data,
                    headers=headers
                )
        except Exception as e:
            logger.error(f"Error sending PUT request: {e}")
            raise InvalidResponseException(f"Error sending PUT request: {e}")
        else:
            logger.debug(f"PUT request to URL: {response.url}")

        return response

    def delete(self, endpoint: str, headers: dict = None, data: dict = None, verify: bool = True):
        """
        Sends a DELETE request to the specified API endpoint.

        This method constructs the full URL by appending the endpoint to the base URL and sends a DELETE request
        with optional query parameters and headers. Authentication is applied if username/password or token is provided.

        :param endpoint: str - The API endpoint to send the request to (relative to the base URL).
        :param headers: dict, optional - Additional headers to include in the request.
        :param data: dict, optional - Query parameters to include in the request.
        :param verify: bool - Whether to verify SSL certificates (default: True).
        :return: Response - The response object from the DELETE request.
        :raises InvalidResponseException: If an error occurs during the request execution.
        """
        response = FAILED_REQUEST_RESPONSE
        try:
            url = self._add_endpoint_to_url(endpoint)

            with req.Session() as session:
                if self.username and self.password:
                    session.auth = (
                        self.username,
                        self.password
                    )
                elif self.token:
                    headers = self._add_token_to_headers(headers)

                session.verify = verify

                response = session.delete(
                    url=url,
                    headers=headers,
                    params=data
                )
        except Exception as e:
            logger.error(f"Error sending DELETE request: {e}")
            raise InvalidResponseException(f"Error sending DELETE request: {e}")
        else:
            logger.debug(f"DELETE request to URL: {response.url}")

        return response

    def _add_endpoint_to_url(self, endpoint: str):
        clean_base_url = self.base_url.rstrip('/')
        url = f"{clean_base_url}/{endpoint}" if self._has_valid_protocol(clean_base_url) else f"https://{clean_base_url}/{endpoint}"
        return url

    def _has_valid_protocol(self, url: str):
        return url.startswith(('http://', 'https://'))

    def _add_token_to_headers(self, headers: dict = None):
        if not headers:
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
        else:
            if "Authorization" not in headers:
                headers["Authorization"] = f"Bearer {self.token}"

        return headers
