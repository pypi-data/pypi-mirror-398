import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from pygeai.core.files.clients import FileClient


class TestFileClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.files.test_clients.TestFileClient
    """
    def setUp(self):
        self.file_client = FileClient()
        self.organization_id = "org123"
        self.project_id = "proj123"
        self.file_id = "file456"
        self.file_path = Path("test_file.txt")
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"id": self.file_id, "status": "success"}
        self.mock_response.text = json.dumps({"id": self.file_id, "status": "success"})
        self.mock_response.content = b"file content"
        self.mock_file = MagicMock()
        self.mock_file.close = MagicMock()

    @patch('pygeai.core.services.rest.ApiService.post_files_multipart')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.open')
    def test_upload_file_success(self, mock_open, mock_is_file, mock_post):
        mock_is_file.return_value = True
        mock_open.return_value = self.mock_file
        mock_post.return_value = self.mock_response

        result = self.file_client.upload_file(
            file_path=str(self.file_path),
            organization_id=self.organization_id,
            project_id=self.project_id,
            folder="test_folder",
            file_name="custom_name.txt"
        )

        mock_post.assert_called_once()
        mock_is_file.assert_called_once()
        mock_open.assert_called_once_with("rb")
        self.mock_file.close.assert_called_once()
        self.assertEqual(result, {"id": self.file_id, "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post_files_multipart')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.open')
    def test_upload_file_without_optional_params(self, mock_open, mock_is_file, mock_post):
        mock_is_file.return_value = True
        mock_open.return_value = self.mock_file
        mock_post.return_value = self.mock_response

        result = self.file_client.upload_file(
            file_path=str(self.file_path),
            organization_id=self.organization_id,
            project_id=self.project_id
        )

        mock_post.assert_called_once()
        mock_is_file.assert_called_once()
        mock_open.assert_called_once_with("rb")
        self.mock_file.close.assert_called_once()
        self.assertEqual(result, {"id": self.file_id, "status": "success"})

    def test_upload_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.file_client.upload_file(
                file_path="nonexistent_file.txt",
                organization_id=self.organization_id,
                project_id=self.project_id
            )

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_file_success(self, mock_get):
        mock_get.return_value = self.mock_response

        result = self.file_client.get_file(
            organization=self.organization_id,
            project=self.project_id,
            file_id=self.file_id
        )

        mock_get.assert_called_once()
        self.assertEqual(result, {"id": self.file_id, "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_file_success(self, mock_delete):
        mock_delete.return_value = self.mock_response

        result = self.file_client.delete_file(
            organization=self.organization_id,
            project=self.project_id,
            file_id=self.file_id
        )

        mock_delete.assert_called_once()
        self.assertEqual(result, {"id": self.file_id, "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_file_content_success(self, mock_get):
        mock_get.return_value = self.mock_response

        result = self.file_client.get_file_content(
            organization=self.organization_id,
            project=self.project_id,
            file_id=self.file_id
        )

        mock_get.assert_called_once()
        self.assertEqual(result, b"file content")

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_file_list_success(self, mock_get):
        mock_get.return_value = self.mock_response

        result = self.file_client.get_file_list(
            organization=self.organization_id,
            project=self.project_id
        )

        mock_get.assert_called_once()
        self.assertEqual(result, {"id": self.file_id, "status": "success"})


