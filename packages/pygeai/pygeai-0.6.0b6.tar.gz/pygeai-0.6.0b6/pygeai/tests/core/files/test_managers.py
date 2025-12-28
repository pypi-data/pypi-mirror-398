import unittest
from unittest.mock import MagicMock, patch
from pygeai.core.files.managers import FileManager
from pygeai.core.files.models import UploadFile, File, FileList
from pygeai.core.files.responses import UploadFileResponse
from pygeai.core.base.responses import EmptyResponse
from pygeai.core.common.exceptions import APIError


class TestFileManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.files.test_managers.TestFileManager
    """
    def setUp(self):
        self.api_key = "dummy_api_key"
        self.base_url = "https://dummyapi.com"
        self.organization_id = "org123"
        self.project_id = "proj123"
        self.file_manager = FileManager(
            api_key=self.api_key,
            base_url=self.base_url,
            organization_id=self.organization_id,
            project_id=self.project_id
        )
        self.file_client_mock = MagicMock()
        self.file_manager._FileManager__client = self.file_client_mock

    def test_upload_file_success(self):
        file = UploadFile(path="dummy_path", name="test.txt", folder="folder1")
        mock_response = {
            'dataFileId': '30120d96-6d3b-40ae-887d-8a7485f8ba02',
            'dataFileUrl': 'filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt',
            'success': True
        }
        self.file_client_mock.upload_file.return_value = mock_response
        with patch('pygeai.core.files.managers.FileResponseMapper.map_to_upload_file_response') as mock_mapper:
            mock_mapper.return_value = UploadFileResponse(
                id="30120d96-6d3b-40ae-887d-8a7485f8ba02",
                url="filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt",
                success=True
            )

            result = self.file_manager.upload_file(file)

            self.assertIsInstance(result, UploadFileResponse)
            self.assertEqual(result.id, "30120d96-6d3b-40ae-887d-8a7485f8ba02")
            self.assertEqual(result.url,
                             'filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt')
            self.file_client_mock.upload_file.assert_called_once_with(
                file_path=file.path,
                organization_id=self.organization_id,
                project_id=self.project_id,
                folder=file.folder,
                file_name=file.name
            )
            mock_mapper.assert_called_once_with(mock_response)

    def test_get_file_data_success(self):
        file_id = "9984b837-fe88-4014-ad14-91e1596c8ead"
        mock_response = {
            'dataFileExtension': 'txt',
            'dataFileId': '9984b837-fe88-4014-ad14-91e1596c8ead',
            'dataFileName': 'TestyFile',
            'dataFilePurpose': 'Assistant',
            'dataFileSize': 19,
            'dataFileUrl': 'filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt',
            'organizationId': '4aa15b61-d3c7-4a5c-99b8-052d18a04ff2',
            'projectId': '1956c032-3c66-4435-acb8-6a06e52f819f',
            'success': True
        }
        self.file_client_mock.get_file.return_value = mock_response
        with patch('pygeai.core.files.managers.FileResponseMapper.map_to_file') as mock_mapper:
            mock_mapper.return_value = File(
                id="9984b837-fe88-4014-ad14-91e1596c8ead",
                name="TestyFile",
                extension="txt",
                purpose="Assistant",
                size=19,
                url="filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt"
            )

            result = self.file_manager.get_file_data(file_id)

            self.assertIsInstance(result, File)
            self.assertEqual(result.id, "9984b837-fe88-4014-ad14-91e1596c8ead")
            self.assertEqual(result.name, "TestyFile")
            self.assertEqual(result.extension, "txt")
            self.assertEqual(result.purpose, "Assistant")
            self.assertEqual(result.size, 19)
            self.assertEqual(result.url, "filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt")
            self.file_client_mock.get_file.assert_called_once_with(
                organization=self.organization_id,
                project=self.project_id,
                file_id=file_id
            )
            mock_mapper.assert_called_once_with(mock_response)

    def test_delete_file_success(self):
        file_id = "file123"
        mock_response = {}
        self.file_client_mock.delete_file.return_value = mock_response
        with patch('pygeai.core.files.managers.ResponseMapper.map_to_empty_response') as mock_mapper:
            mock_mapper.return_value = EmptyResponse()

            result = self.file_manager.delete_file(file_id)

            self.assertIsInstance(result, EmptyResponse)
            self.file_client_mock.delete_file.assert_called_once_with(
                organization=self.organization_id,
                project=self.project_id,
                file_id=file_id
            )
            mock_mapper.assert_called_once_with(mock_response or "File deleted successfully")

    def test_get_file_content_success(self):
        file_id = "file123"
        mock_response = b"file content"
        self.file_client_mock.get_file_content.return_value = mock_response

        result = self.file_manager.get_file_content(file_id)

        self.assertEqual(result, b"file content")
        self.file_client_mock.get_file_content.assert_called_once_with(
            organization=self.organization_id,
            project=self.project_id,
            file_id=file_id
        )

    def test_get_file_list_success(self):
        mock_response = {
            'dataFiles': [
                {
                    "DataFileId": "30120d96-6d3b-40ae-887d-8a7485f8ba02",
                    "DataFileName": "TestyFile",
                    "DataFileExtension": "txt",
                    "DataFileSize": 19,
                    "DataFileUrl": "filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt"
                },
                {
                    "DataFileId": "7433c276-81e8-405e-9990-82158326f839",
                    "DataFileName": "TestyFile",
                    "DataFileExtension": "txt",
                    "DataFileSize": 19,
                    "DataFileUrl": "filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt"
                }
            ]
        }
        self.file_client_mock.get_file_list.return_value = mock_response
        with patch('pygeai.core.files.managers.FileResponseMapper.map_to_file_list_response') as mock_mapper:
            mock_mapper.return_value = FileList(files=[
                File(
                    id="30120d96-6d3b-40ae-887d-8a7485f8ba02",
                    name="TestyFile",
                    extension="txt",
                    size=19,
                    url="filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt"
                ),
                File(
                    id="7433c276-81e8-405e-9990-82158326f839",
                    name="TestyFile",
                    extension="txt",
                    size=19,
                    url="filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt"
                )
            ])

            result = self.file_manager.get_file_list()

            self.assertIsInstance(result, FileList)
            self.assertEqual(len(result.files), 2)
            self.assertEqual(result.files[0].id, "30120d96-6d3b-40ae-887d-8a7485f8ba02")
            self.assertEqual(result.files[0].name, "TestyFile")
            self.assertEqual(result.files[0].extension, "txt")
            self.assertEqual(result.files[0].size, 19)
            self.assertEqual(result.files[0].url, "filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt")
            self.assertEqual(result.files[1].id, "7433c276-81e8-405e-9990-82158326f839")
            self.assertEqual(result.files[1].name, "TestyFile")
            self.assertEqual(result.files[1].extension, "txt")
            self.assertEqual(result.files[1].size, 19)
            self.assertEqual(result.files[1].url, "filesAssistants/4aa15b61-d3c7-4a5c-99b8-052d18a04ff2/1956c032-3c66-4435-acb8-6a06e52f819f/files/TestyTestTemp/TestyFile.txt")
            self.file_client_mock.get_file_list.assert_called_once_with(
                organization=self.organization_id,
                project=self.project_id
            )
            mock_mapper.assert_called_once_with(mock_response)

    def test_upload_file_error(self):
        file = UploadFile(path="dummy_path", name="test.txt", folder="folder1")
        mock_response = {"errors": [{"id": 1, "description": "Upload failed"}]}
        self.file_client_mock.upload_file.return_value = mock_response
        with patch('pygeai.core.files.managers.ErrorHandler.has_errors', return_value=True):
            with patch('pygeai.core.files.managers.ErrorHandler.extract_error', return_value="Upload failed"):
                with self.assertRaises(APIError) as context:
                    self.file_manager.upload_file(file)

                self.assertIn("Error received while uploading file: Upload failed", str(context.exception))
                self.file_client_mock.upload_file.assert_called_once_with(
                    file_path=file.path,
                    organization_id=self.organization_id,
                    project_id=self.project_id,
                    folder=file.folder,
                    file_name=file.name
                )

    def test_get_file_content_error(self):
        file_id = "file123"
        mock_response = {"errors": [{"id": 1, "description": "Content retrieval failed"}]}
        self.file_client_mock.get_file_content.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.file_manager.get_file_content(file_id)

        self.assertIn("Error received while retrieving file content", str(context.exception))
        self.file_client_mock.get_file_content.assert_called_once_with(
            organization=self.organization_id,
            project=self.project_id,
            file_id=file_id
        )

