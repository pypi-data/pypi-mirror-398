from json import JSONDecodeError

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.health.endpoints import STATUS_CHECK_V1


class HealthClient(BaseClient):

    def check_api_status(self) -> dict:
        """
        Checks the status of the API.

        :return: dict - The API response as a JSON object containing details about the API status.
        If the response cannot be parsed as JSON, returns the raw response text.
        """
        endpoint = STATUS_CHECK_V1
        response = self.api_service.get(
            endpoint=endpoint
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to check API status: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to check API status: {response.text}")
