import unittest
from unittest.mock import patch, MagicMock
from json import JSONDecodeError
from pygeai.assistant.rag.clients import RAGAssistantClient
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestRAGAssistantClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.assistants.rag.test_clients.TestRAGAssistantClient
    """
    def setUp(self):
        with patch('pygeai.core.base.clients.BaseClient.__init__', return_value=None):
            self.client = RAGAssistantClient()
        self.mock_response = MagicMock()
        self.client.api_service = MagicMock()
        self.assistant_name = "test_assistant"
        self.document_id = "doc_123"
        self.file_path = "/path/to/test.pdf"

    def test_get_url_safe_name(self):
        name = "test assistant"
        expected_safe_name = "test+assistant"

        result = self.client.get_url_safe_name(name)

        self.assertEqual(result, expected_safe_name)

    def test_get_assistants_from_project_successful_json_response(self):
        expected_response = {"assistants": []}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_assistants_from_project()

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_assistants_from_project_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Invalid JSON response"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_assistants_from_project()

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to get assistants from project", str(context.exception))

    def test_get_assistant_data_successful_json_response(self):
        expected_response = {"name": self.assistant_name, "details": "test"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_assistant_data(self.assistant_name)

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_assistant_data_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Invalid JSON response"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_assistant_data(self.assistant_name)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to get assistant data", str(context.exception))

    def test_create_assistant_successful_json_response(self):
        name = "new_assistant"
        description = "Test description"
        expected_response = {"id": "new_id", "name": name}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.create_assistant(name, description)

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_create_assistant_json_decode_error(self):
        name = "new_assistant"
        description = "Test description"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Error in response"
        self.mock_response.status_code = 500
        self.client.api_service.post.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_assistant(name, description)

        self.client.api_service.post.assert_called_once()
        self.assertIn("Unable to create assistant", str(context.exception))

    def test_update_assistant_successful_json_response(self):
        name = "test_assistant"
        status = 1
        expected_response = {"name": name, "status": status}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_assistant(name, status)

        self.client.api_service.put.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_update_assistant_json_decode_error(self):
        name = "test_assistant"
        status = 2
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Update failed"
        self.mock_response.status_code = 500
        self.client.api_service.put.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_assistant(name, status)

        self.client.api_service.put.assert_called_once()
        self.assertIn("Unable to update assistant", str(context.exception))

    def test_delete_assistant_successful_json_response(self):
        name = "test_assistant"
        expected_response = {"message": "Assistant deleted"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_assistant(name)

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_delete_assistant_json_decode_error(self):
        name = "test_assistant"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Delete error"
        self.mock_response.status_code = 500
        self.client.api_service.delete.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_assistant(name)

        self.client.api_service.delete.assert_called_once()
        self.assertIn("Unable to delete assistant", str(context.exception))

    def test_get_documents_successful_json_response(self):
        name = "test_assistant"
        skip = 0
        count = 10
        expected_response = {"documents": []}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_documents(name, skip, count)

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_get_documents_json_decode_error(self):
        name = "test_assistant"
        skip = 0
        count = 10
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Documents error"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_documents(name, skip, count)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to get documents", str(context.exception))

    def test_delete_all_documents_successful_json_response(self):
        name = "test_assistant"
        expected_response = {"message": "All documents deleted"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_all_documents(name)

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_delete_all_documents_json_decode_error(self):
        name = "test_assistant"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Delete all error"
        self.mock_response.status_code = 500
        self.client.api_service.delete.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_all_documents(name)

        self.client.api_service.delete.assert_called_once()
        self.assertIn("Unable to delete all documents", str(context.exception))

    def test_retrieve_document_successful_json_response(self):
        name = "test_assistant"
        document_id = "doc_123"
        expected_response = {"id": document_id, "content": "test content"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.retrieve_document(name, document_id)

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_retrieve_document_json_decode_error(self):
        name = "test_assistant"
        document_id = "doc_123"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Retrieve error"
        self.mock_response.status_code = 500
        self.client.api_service.get.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.retrieve_document(name, document_id)

        self.client.api_service.get.assert_called_once()
        self.assertIn("Unable to retrieve document", str(context.exception))

    def test_upload_document_binary_successful_json_response(self):
        name = "test_assistant"
        file_path = "/path/to/test.pdf"
        upload_type = "binary"
        content_type = "application/pdf"
        expected_response = {"id": "uploaded_doc", "status": "success"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post_file_binary.return_value = self.mock_response

        with patch('builtins.open', return_value=MagicMock()):
            result = self.client.upload_document(name, file_path, upload_type, content_type=content_type)

        self.client.api_service.post_file_binary.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_upload_document_multipart_successful_json_response(self):
        name = "test_assistant"
        file_path = "/path/to/test.pdf"
        upload_type = "multipart"
        content_type = "application/pdf"
        metadata = {"key": "value"}
        expected_response = {"id": "uploaded_doc", "status": "success"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post_files_multipart.return_value = self.mock_response

        with patch('builtins.open', return_value=MagicMock()), \
             patch('pathlib.Path.name', return_value="test.pdf"):
            result = self.client.upload_document(name, file_path, upload_type, metadata, content_type)

        self.client.api_service.post_files_multipart.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_upload_document_invalid_upload_type(self):
        name = "test_assistant"
        file_path = "/path/to/test.pdf"
        upload_type = "invalid"

        with self.assertRaises(ValueError) as context:
            self.client.upload_document(name, file_path, upload_type)

        self.assertEqual(str(context.exception), "Invalid upload_type. Use 'binary' or 'multipart'.")

    def test_upload_document_json_decode_error(self):
        name = "test_assistant"
        file_path = "/path/to/test.pdf"
        upload_type = "binary"
        content_type = "application/pdf"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Upload error"
        self.mock_response.status_code = 500
        self.client.api_service.post_file_binary.return_value = self.mock_response

        with patch('builtins.open', return_value=MagicMock()):
            with self.assertRaises(InvalidAPIResponseException) as context:
                self.client.upload_document(name, file_path, upload_type, content_type=content_type)

        self.client.api_service.post_file_binary.assert_called_once()
        self.assertIn("Unable to upload document", str(context.exception))

    def test_delete_document_successful_json_response(self):
        name = "test_assistant"
        document_id = "doc_123"
        expected_response = {"message": "Document deleted"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_document(name, document_id)

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_delete_document_json_decode_error(self):
        name = "test_assistant"
        document_id = "doc_123"
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Delete document error"
        self.mock_response.status_code = 500
        self.client.api_service.delete.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_document(name, document_id)

        self.client.api_service.delete.assert_called_once()
        self.assertIn("Unable to delete document", str(context.exception))

    def test_execute_query_successful_json_response(self):
        query = {"text": "test query"}
        expected_response = {"result": "query response"}
        self.mock_response.json.return_value = expected_response
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.execute_query(query)

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, expected_response)

    def test_execute_query_json_decode_error(self):
        query = {"text": "test query"}
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.mock_response.text = "Query error"
        self.mock_response.status_code = 500
        self.client.api_service.post.return_value = self.mock_response

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.execute_query(query)

        self.client.api_service.post.assert_called_once()
        self.assertIn("Unable to execute query", str(context.exception))
