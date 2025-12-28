from pygeai import logger
from pygeai.admin.clients import AdminClient
from pygeai.core.base.mappers import ErrorMapper, ResponseMapper
from pygeai.core.base.responses import EmptyResponse
from pygeai.core.files.clients import FileClient
from pygeai.core.files.models import UploadFile, File, FileList
from pygeai.core.files.mappers import FileResponseMapper
from pygeai.core.files.responses import UploadFileResponse
from pygeai.core.handlers import ErrorHandler
from pygeai.core.common.exceptions import APIError


class FileManager:
    """
    Manages file-related operations such as uploading, retrieving, and deleting files
    within an organization and project.
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = None,
            alias: str = "default",
            organization_id: str = None,
            project_id: str = None
    ):
        self.__client = FileClient(
            api_key,
            base_url,
            alias
        )
        self.organization_id = self.__get_organization_id() if not organization_id else organization_id
        self.project_id = self.__get_project_id() if not project_id else project_id

    def __get_organization_id(self):
        response = None
        try:
            response = AdminClient().validate_api_token()
            return response.get("organizationId")
        except Exception as e:
            logger.error(f"Error retrieving organization_id from GEAI. Response: {response}: {e}")
            raise APIError(f"Error retrieving organization_id from GEAI: {e}")

    def __get_project_id(self):
        response = None
        try:
            response = AdminClient().validate_api_token()
            return response.get("projectId")
        except Exception as e:
            logger.error(f"Error retrieving project_id from GEAI. Response: {response}: {e}")
            raise APIError(f"Error retrieving project_id from GEAI: {e}")

    def upload_file(
            self,
            file: UploadFile
    ) -> UploadFileResponse:
        """
        Uploads a file to the specified organization and project.

        This method sends a request to the file client to upload a file based on the provided
        `UploadFile` object.

        :param file: UploadFile - The file object containing file path, name, and folder details.
        :return: UploadFileResponse - The response object containing the uploaded file details.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.upload_file(
            file_path=file.path,
            organization_id=self.organization_id,
            project_id=self.project_id,
            folder=file.folder,
            file_name=file.name,
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while uploading file: {error}")
            raise APIError(f"Error received while uploading file: {error}")

        result = FileResponseMapper.map_to_upload_file_response(response_data)
        return result

    def get_file_data(
            self,
            file_id: str
    ) -> File:
        """
        Retrieves metadata of a specific file by its ID.

        This method sends a request to the file client to retrieve metadata for a file
        identified by `file_id`.

        :param file_id: str - The unique identifier of the file.
        :return: File - A file object containing metadata about the requested file.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_file(
            organization=self.organization_id,
            project=self.project_id,
            file_id=file_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving file data: {error}")
            raise APIError(f"Error received while retrieving file data: {error}")

        result = FileResponseMapper.map_to_file(response_data)
        return result

    def delete_file(
            self,
            file_id: str
    ) -> EmptyResponse:
        """
        Deletes a file from the specified organization and project.

        This method sends a request to the file client to delete a file identified by `file_id`.

        :param file_id: str - The unique identifier of the file to be deleted.
        :return: EmptyResponse - Response indicating the success of the operation.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.delete_file(
            organization=self.organization_id,
            project=self.project_id,
            file_id=file_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while deleting file: {error}")
            raise APIError(f"Error received while deleting file: {error}")

        result = ResponseMapper.map_to_empty_response(response_data or "File deleted successfully")
        return result

    def get_file_content(
            self,
            file_id: str
    ) -> bytes:
        """
        Retrieves the raw content of a specific file.

        This method sends a request to the file client to retrieve the binary content of a file
        identified by `file_id`.

        :param file_id: str - The unique identifier of the file.
        :return: bytes - The binary content of the file.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_file_content(
            organization=self.organization_id,
            project=self.project_id,
            file_id=file_id
        )
        if isinstance(response_data, dict) and "errors" in response_data:
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving file content: {error}")
            raise APIError(f"Error received while retrieving file content: {error}")

        result = response_data
        return result

    def get_file_list(self) -> FileList:
        """
        Retrieves a list of all files associated with a given organization and project.

        This method queries the file client to fetch a list of files for the specified
        organization and project.

        :return: FileList - A list of file objects associated with the organization and project.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.get_file_list(
            organization=self.organization_id,
            project=self.project_id
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving file list: {error}")
            raise APIError(f"Error received while retrieving file list: {error}")

        result = FileResponseMapper.map_to_file_list_response(response_data)
        return result
