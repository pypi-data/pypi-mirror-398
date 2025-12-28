from json import JSONDecodeError
from pathlib import Path

from pygeai import logger
from pygeai.assistant.clients import AssistantClient
from pygeai.assistant.data_analyst.endpoints import GET_DATA_ANALYST_STATUS_V1, EXTEND_DATA_ANALYST_DATASET_V1
from pygeai.core.common.exceptions import InvalidAPIResponseException


class DataAnalystAssistantClient(AssistantClient):

    def get_status(
            self,
            assistant_id: str
    ) -> dict:
        """
        Retrieves the current status of the dataset loading process for the Data Analyst Assistant.

        :param assistant_id: str - The ID of the Data Analyst Assistant.
        :return: dict - API response containing the status or error details.
        :raises ValueError: If assistant_id is empty or invalid.
        """
        if not assistant_id or not isinstance(assistant_id, str):
            raise ValueError("assistant_id must be a non-empty string")

        endpoint = GET_DATA_ANALYST_STATUS_V1.format(id=assistant_id)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers
        )

        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to get status for assistant ID '{assistant_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to get status for assistant ID '{assistant_id}': {response.text}")

    def extend_dataset(
        self,
        assistant_id: str,
        file_paths: list[str]
    ) -> dict:
        """
        Uploads one or more .csv dataset files to the Data Analyst Assistant.

        :param assistant_id: str - The ID of the Data Analyst Assistant.
        :param file_paths: list[str] - List of paths to the .csv files to be uploaded.
        :return: dict - API response indicating success or failure.
        """
        endpoint = EXTEND_DATA_ANALYST_DATASET_V1.format(id=assistant_id)

        files = []
        for file_path in file_paths:
            path = Path(file_path)
            if not path.is_file():
                raise FileNotFoundError(f"File not found: {file_path}")
            if path.suffix.lower() != '.csv':
                raise ValueError(f"File must be a .csv file: {file_path}")
            files.append(("file", path.open("rb")))

        try:
            response = self.api_service.post_files_multipart(
                endpoint=endpoint,
                files=files
            )
            try:
                result = response.json()
                return result
            except JSONDecodeError as e:
                logger.error(f"Unable to extend dataset for assistant ID '{assistant_id}': JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
                raise InvalidAPIResponseException(f"Unable to extend dataset for assistant ID '{assistant_id}': {response.text}")
        finally:
            for _, file_handle in files:
                file_handle.close()


