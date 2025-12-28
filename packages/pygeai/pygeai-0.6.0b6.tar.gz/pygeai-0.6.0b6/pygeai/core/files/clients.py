import json
from json import JSONDecodeError
from pathlib import Path

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.core.files.endpoints import UPLOAD_FILE_V1, GET_FILE_V1, DELETE_FILE_V1, GET_FILE_CONTENT_V1, \
    GET_ALL_FILES_V1


class FileClient(BaseClient):

    def upload_file(
        self,
        file_path: str,
        organization_id: str,
        project_id: str,
        folder: str = None,
        file_name: str = None
    ) -> dict:
        """
        Uploads a file to the system.

        :param file_path: str - Path to the file to be uploaded.
        :param organization_id: str - The organization ID.
        :param project_id: str - The project ID.
        :param folder: str, optional - Destination folder (default is None, which means temporary storage).
        :param file_name: str, optional - Custom file name (defaults to the uploaded file's name).

        :return: dict - API response containing file ID and URL.
        """
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        headers = {
            "organizationId": organization_id,
            "projectId": project_id,
        }
        if file_name:
            headers["fileName"] = file_name
        if folder:
            headers["folder"] = folder

        files = {"file": file_path.open("rb")}

        logger.debug(f"Uploading file {file_name}")

        try:
            response = self.api_service.post_files_multipart(
                endpoint=UPLOAD_FILE_V1,
                headers=headers,
                files=files
            )
            try:
                result = response.json()
                return result
            except JSONDecodeError as e:
                logger.error(
                    f"Unable to upload file {file_name} in project {project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
                raise InvalidAPIResponseException(f"Unable to upload file {file_name}: {response.text}")

        finally:
            files["file"].close()

    def get_file(self, organization: str, project: str, file_id: str) -> dict:
        """
        Retrieves details of a specific file by its ID.

        :param organization: str - The ID of the organization that owns the file.
        :param project: str - The ID of the project associated with the file.
        :param file_id: str - The unique identifier of the file.
        :return: dict - The file metadata as a dictionary.
        """
        endpoint = GET_FILE_V1.format(fileId=file_id)
        response = self.api_service.get(
            endpoint=endpoint,
            params={
                "organization": organization,
                "project": project
            }
        )
        logger.debug(f"Retrieving file details for id {file_id}")
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve file details for id {file_id} in project {project}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve file details for id {file_id}: {response.text}")

    def delete_file(self, organization: str, project: str, file_id: str) -> dict:
        """
        Deletes a file by its ID.

        :param organization: str - The ID of the organization that owns the file.
        :param project: str - The ID of the project associated with the file.
        :param file_id: str - The unique identifier of the file.
        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_FILE_V1.format(fileId=file_id)
        headers = {
            "Accept": "application/json",
        }

        logger.debug(f"Deleting file with id {file_id}")

        response = self.api_service.delete(
            endpoint=endpoint,
            headers=headers,
            data={
                "organization": organization,
                "project": project
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to delete file with id {file_id} in project {project}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete file with id {file_id}: {response.text}")

    def get_file_content(self, organization: str, project: str, file_id: str) -> bytes:
        """
        Retrieves the raw content of a file by its ID.

        :param organization: str - The ID of the organization that owns the file.
        :param project: str - The ID of the project associated with the file.
        :param file_id: str - The unique identifier of the file.
        :return: bytes - The file content in binary format.
        """
        endpoint = GET_FILE_CONTENT_V1.format(fileId=file_id)

        logger.debug(f"Retrieving raw content of file with id {file_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            params={
                "organization": organization,
                "project": project
            }
        )
        return response.content

    def get_file_list(
            self,
            organization: str,
            project: str
    ) -> dict:
        """
        Retrieves a list of all files associated with a given organization and project.

        :param organization: str - The ID of the organization.
        :param project: str - The ID of the project.
        :return: dict - A dictionary containing the list of files.
        """
        logger.debug(f"Retrieving file list for project {project}")

        response = self.api_service.get(
            endpoint=GET_ALL_FILES_V1,
            params={
                "organization": organization,
                "project": project
            }
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve file list for project {project}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve file list for project {project}: {response.text}")
