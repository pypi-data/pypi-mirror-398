import unittest
from unittest import TestCase

from pygeai.core.files.models import BaseFile, File, FileList, UploadFile
from pygeai.core.files.responses import UploadFileResponse


class TestFileResponses(TestCase):
    """
    python -m unittest pygeai.tests.core.files.test_responses.TestFileResponses
    """

    def test_base_file_model_validate(self):
        base_file_data = {
            "id": "file123",
            "name": "testfile.txt"
        }
        base_file = BaseFile.model_validate(base_file_data)
        self.assertEqual(base_file.id, base_file_data["id"])
        self.assertEqual(base_file.name, base_file_data["name"])
        self.assertEqual(base_file.model_dump(), base_file_data)

    def test_base_file_model_empty(self):
        base_file_data = {}
        base_file = BaseFile.model_validate(base_file_data)
        self.assertIsNone(base_file.id)
        self.assertIsNone(base_file.name)
        self.assertEqual(base_file.model_dump(exclude_none=True), {})

    def test_upload_file_model_validate(self):
        upload_file_data = {
            "id": "file123",
            "name": "testfile.txt",
            "path": "/uploads/testfile.txt",
            "folder": "uploads"
        }
        upload_file = UploadFile.model_validate(upload_file_data)
        self.assertEqual(upload_file.id, upload_file_data["id"])
        self.assertEqual(upload_file.name, upload_file_data["name"])
        self.assertEqual(upload_file.path, upload_file_data["path"])
        self.assertEqual(upload_file.folder, upload_file_data["folder"])
        self.assertEqual(upload_file.model_dump(), upload_file_data)

    def test_upload_file_model_minimal(self):
        upload_file_data = {
            "path": "/uploads/testfile.txt"
        }
        upload_file = UploadFile.model_validate(upload_file_data)
        self.assertIsNone(upload_file.id)
        self.assertIsNone(upload_file.name)
        self.assertEqual(upload_file.path, upload_file_data["path"])
        self.assertIsNone(upload_file.folder)
        self.assertEqual(upload_file.model_dump(exclude_none=True), upload_file_data)

    def test_file_model_validate(self):
        file_data = {
            "id": "file123",
            "name": "testfile.txt",
            "extension": "txt",
            "purpose": "test",
            "size": 1024,
            "url": "https://example.com/files/testfile.txt"
        }
        file_obj = File.model_validate(file_data)
        self.assertEqual(file_obj.id, file_data["id"])
        self.assertEqual(file_obj.name, file_data["name"])
        self.assertEqual(file_obj.extension, file_data["extension"])
        self.assertEqual(file_obj.purpose, file_data["purpose"])
        self.assertEqual(file_obj.size, file_data["size"])
        self.assertEqual(file_obj.url, file_data["url"])
        self.assertEqual(file_obj.model_dump(), file_data)

    def test_file_model_empty(self):
        file_data = {}
        file_obj = File.model_validate(file_data)
        self.assertIsNone(file_obj.id)
        self.assertIsNone(file_obj.name)
        self.assertIsNone(file_obj.extension)
        self.assertIsNone(file_obj.purpose)
        self.assertEqual(file_obj.size, 0)
        self.assertIsNone(file_obj.url)
        self.assertEqual(file_obj.model_dump(exclude_none=True), {"size": 0})

    def test_file_list_model_validate(self):
        file_list_data = {
            "files": [
                {"id": "file1", "name": "file1.txt", "size": 512},
                {"id": "file2", "name": "file2.pdf", "size": 2048, "url": "https://example.com/files/file2.pdf"}
            ]
        }
        file_list = FileList.model_validate(file_list_data)
        self.assertEqual(len(file_list.files), 2)
        self.assertEqual(file_list.files[0].id, file_list_data["files"][0]["id"])
        self.assertEqual(file_list.files[0].name, file_list_data["files"][0]["name"])
        self.assertEqual(file_list.files[1].url, file_list_data["files"][1]["url"])
        self.assertEqual(file_list.model_dump(exclude_none=True), file_list_data)

    def test_file_list_model_empty(self):
        file_list_data = {
            "files": []
        }
        file_list = FileList.model_validate(file_list_data)
        self.assertEqual(len(file_list.files), 0)
        self.assertEqual(file_list.model_dump(exclude_none=True), file_list_data)

    def test_upload_file_response_model_validate(self):
        upload_response_data = {
            "id": "file123",
            "url": "https://example.com/uploaded/file123",
            "success": True
        }
        upload_response = UploadFileResponse.model_validate(upload_response_data)
        self.assertEqual(upload_response.id, upload_response_data["id"])
        self.assertEqual(upload_response.url, upload_response_data["url"])
        self.assertEqual(upload_response.success, upload_response_data["success"])
        expected_dict = {
            "dataFileId": upload_response_data["id"],
            "dataFileUrl": upload_response_data["url"],
            "success": upload_response_data["success"]
        }
        self.assertEqual(upload_response.to_dict(), expected_dict)
        self.assertEqual(str(upload_response), str(expected_dict))