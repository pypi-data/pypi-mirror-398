import time
from pathlib import Path
from typing import List

from pygeai.assistant.data_analyst.clients import DataAnalystAssistantClient
from pygeai.core.common.exceptions import APIError


def monitor_dataset_extension(
    client: DataAnalystAssistantClient,
    assistant_id: str,
    file_paths: List[str],
    poll_interval: float = 5.0,
    max_attempts: int = 60
) -> dict:
    """
    Uploads dataset files to a Data Analyst Assistant and monitors the processing status.

    :param client: DataAnalystAssistantClient - The client instance to interact with the API.
    :param assistant_id: str - The ID of the Data Analyst Assistant.
    :param file_paths: List[str] - List of paths to .csv files to upload.
    :param poll_interval: float - Time (in seconds) to wait between status checks (default: 5.0).
    :param max_attempts: int - Maximum number of status checks before timing out (default: 60).
    :return: dict - Final status response from the API.
    :raises ValueError: If assistant_id or file_paths are invalid.
    :raises FileNotFoundError: If any file in file_paths does not exist.
    :raises APIError: If the API returns an error during upload or status checking.
    """
    # Validate inputs
    if not assistant_id or not isinstance(assistant_id, str):
        raise ValueError("assistant_id must be a non-empty string")
    if not file_paths or not isinstance(file_paths, list):
        raise ValueError("file_paths must be a non-empty list of file paths")

    # Validate file paths
    for file_path in file_paths:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        if path.suffix.lower() != '.csv':
            raise ValueError(f"File must be a .csv file: {file_path}")

    # Step 1: Upload the dataset files
    print(f"Uploading files: {file_paths}")
    try:
        upload_response = client.extend_dataset(
            assistant_id=assistant_id,
            file_paths=file_paths
        )
        if isinstance(upload_response, dict) and "error" in upload_response:
            raise APIError(f"Failed to upload files: {upload_response.get('error')}")
        print(f"Upload successful: {upload_response}")
    except Exception as e:
        raise APIError(f"Upload failed: {str(e)}")

    # Step 2: Poll the status until no longer 'IN PROGRESS'
    print(f"Monitoring status for assistant ID: {assistant_id}")
    attempts = 0
    while attempts < max_attempts or max_attempts == 0:
        try:
            status_response = client.get_status(assistant_id=assistant_id)
            if not isinstance(status_response, dict):
                raise APIError(f"Invalid status response: {status_response}")

            status = status_response.get("status")
            percentage = status_response.get("percentage", "N/A")
            print(f"Attempt {attempts + 1}/{max_attempts}: Status = {status}, Percentage = {percentage}")

            if status != "IN PROGRESS":
                return status_response

            time.sleep(poll_interval)
            attempts += 1
        except Exception as e:
            print(f"Error checking status: {str(e)}")
            time.sleep(poll_interval)
            attempts += 1

    # Timeout if max_attempts reached
    raise TimeoutError(f"Status check timed out after {max_attempts} attempts")


if __name__ == "__main__":
    try:
        client = DataAnalystAssistantClient()
        assistant_id = "bab64d47-6416-4f26-a0f4-765db7416652"
        file_paths = [
            "./magic_burgers_sales_data.csv",
        ]

        final_status = monitor_dataset_extension(
            client=client,
            assistant_id=assistant_id,
            file_paths=file_paths,
            poll_interval=5.0,
            max_attempts=60
        )
        print(f"Final status: {final_status}")
    except Exception as e:
        print(f"Error: {str(e)}")