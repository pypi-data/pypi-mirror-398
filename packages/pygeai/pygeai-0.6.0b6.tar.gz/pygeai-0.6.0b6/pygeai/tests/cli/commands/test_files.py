import unittest
from unittest.mock import patch, MagicMock
from pygeai.cli.commands.files import (
    show_help,
    upload_file,
    get_file,
    delete_file,
    get_file_content,
    get_file_list
)
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.cli.commands import Option


class TestFiles(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_files.TestFiles
    """

    def test_show_help(self):
        with patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_upload_file_missing_required_parameters(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            upload_file(option_list)
        self.assertEqual(str(cm.exception), "Organization ID, Project ID and File path are mandatory parameters in order to upload a file.")

    def test_upload_file_success(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123"),
            (Option("project", ["--project"], "", True), "proj123"),
            (Option("file_path", ["--file-path"], "", True), "/path/to/file"),
            (Option("file_name", ["--file-name"], "", True), "testfile.txt"),
            (Option("folder", ["--folder"], "", True), "testfolder")
        ]
        with patch('pygeai.cli.commands.files.FileClient') as mock_client, \
             patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.upload_file.return_value = {"id": "file123"}
            upload_file(option_list)
            mock_client_instance.upload_file.assert_called_once_with(
                organization_id="org123",
                project_id="proj123",
                file_path="/path/to/file",
                file_name="testfile.txt",
                folder="testfolder"
            )
            mock_stdout.assert_called_once_with("Uploaded file: \n{'id': 'file123'}")

    def test_get_file_missing_required_parameters(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            get_file(option_list)
        self.assertEqual(str(cm.exception), "Cannot get file without organization, project and file_id.")

    def test_get_file_success(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123"),
            (Option("project", ["--project"], "", True), "proj123"),
            (Option("file_id", ["--file-id"], "", True), "file123")
        ]
        with patch('pygeai.cli.commands.files.FileClient') as mock_client, \
             patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_file.return_value = {"id": "file123", "name": "testfile.txt"}
            get_file(option_list)
            mock_client_instance.get_file.assert_called_once_with(
                organization="org123",
                project="proj123",
                file_id="file123"
            )
            mock_stdout.assert_called_once_with("File: \n{'id': 'file123', 'name': 'testfile.txt'}")

    def test_delete_file_missing_required_parameters(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            delete_file(option_list)
        self.assertEqual(str(cm.exception), "Cannot delete file without organization, project and file_id.")

    def test_delete_file_success(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123"),
            (Option("project", ["--project"], "", True), "proj123"),
            (Option("file_id", ["--file-id"], "", True), "file123")
        ]
        with patch('pygeai.cli.commands.files.FileClient') as mock_client, \
             patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_file.return_value = {"status": "deleted"}
            delete_file(option_list)
            mock_client_instance.delete_file.assert_called_once_with(
                file_id="file123",
                organization="org123",
                project="proj123"
            )
            mock_stdout.assert_called_once_with("Deleted file: \n{'status': 'deleted'}")

    def test_get_file_content_missing_required_parameters(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            get_file_content(option_list)
        self.assertEqual(str(cm.exception), "Cannot get file content without organization, project and file_id.")

    def test_get_file_content_success(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123"),
            (Option("project", ["--project"], "", True), "proj123"),
            (Option("file_id", ["--file-id"], "", True), "file123")
        ]
        with patch('pygeai.cli.commands.files.FileClient') as mock_client, \
             patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_file_content.return_value = "file content data"
            get_file_content(option_list)
            mock_client_instance.get_file_content.assert_called_once_with(
                file_id="file123",
                organization="org123",
                project="proj123"
            )
            mock_stdout.assert_called_once_with("File content: \nfile content data")

    def test_get_file_list_missing_required_parameters(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123")
        ]
        with self.assertRaises(MissingRequirementException) as cm:
            get_file_list(option_list)
        self.assertEqual(str(cm.exception), "Cannot file list without organization and project id.")

    def test_get_file_list_success(self):
        option_list = [
            (Option("organization", ["--organization"], "", True), "org123"),
            (Option("project", ["--project"], "", True), "proj123")
        ]
        with patch('pygeai.cli.commands.files.FileClient') as mock_client, \
             patch('pygeai.cli.commands.files.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_file_list.return_value = [{"id": "file1"}, {"id": "file2"}]
            get_file_list(option_list)
            mock_client_instance.get_file_list.assert_called_once_with(
                organization="org123",
                project="proj123"
            )
            mock_stdout.assert_called_once_with("Files list: \n[{'id': 'file1'}, {'id': 'file2'}]")

