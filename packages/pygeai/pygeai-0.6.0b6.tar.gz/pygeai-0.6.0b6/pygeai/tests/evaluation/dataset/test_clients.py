import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
from pathlib import Path

from pygeai.evaluation.dataset.clients import EvaluationDatasetClient


class TestEvaluationDatasetClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.evaluation.dataset.test_clients.TestEvaluationDatasetClient
    """

    def setUp(self):
        self.client = EvaluationDatasetClient()
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"id": "dataset-123", "status": "success"}

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_datasets(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_datasets()
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_dataset_minimal(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.create_dataset(
            dataset_name="Test Dataset",
            dataset_description="Test Description",
            dataset_type="T"
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['dataSetName'], "Test Dataset")
        self.assertEqual(call_args[1]['data']['dataSetDescription'], "Test Description")
        self.assertEqual(call_args[1]['data']['dataSetType'], "T")
        self.assertTrue(call_args[1]['data']['dataSetActive'])

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_dataset_with_rows(self, mock_post):
        mock_post.return_value = self.mock_response
        rows = [{"dataSetRowInput": "input1", "dataSetRowExpectedAnswer": "answer1"}]
        result = self.client.create_dataset(
            dataset_name="Test Dataset",
            dataset_description="Test Description",
            dataset_type="T",
            dataset_active=False,
            rows=rows
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data']['rows'], rows)
        self.assertFalse(call_args[1]['data']['dataSetActive'])

    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.open')
    @patch('pygeai.core.services.rest.ApiService.post_file_binary')
    def test_create_dataset_from_file_success(self, mock_post, mock_open_file, mock_is_file):
        mock_is_file.return_value = True
        mock_file = MagicMock()
        mock_open_file.return_value = mock_file
        mock_post.return_value = self.mock_response

        result = self.client.create_dataset_from_file("/path/to/dataset.json")
        
        mock_is_file.assert_called_once()
        mock_open_file.assert_called_once_with("rb")
        mock_post.assert_called_once()
        mock_file.close.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pathlib.Path.is_file')
    def test_create_dataset_from_file_not_found(self, mock_is_file):
        mock_is_file.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.client.create_dataset_from_file("/path/to/nonexistent.json")

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_dataset(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_dataset("dataset-123")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_dataset(self, mock_put):
        mock_put.return_value = self.mock_response
        rows = [{"dataSetRowInput": "updated"}]
        result = self.client.update_dataset(
            dataset_id="dataset-123",
            dataset_name="Updated Dataset",
            dataset_description="Updated Description",
            dataset_type="E",
            dataset_active=False,
            rows=rows
        )
        mock_put.assert_called_once()
        call_args = mock_put.call_args
        self.assertEqual(call_args[1]['data']['dataSetName'], "Updated Dataset")
        self.assertEqual(call_args[1]['data']['rows'], rows)

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_dataset(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_dataset("dataset-123")
        mock_delete.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_dataset_row(self, mock_post):
        mock_post.return_value = self.mock_response
        row = {
            "dataSetRowInput": "input",
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context"
        }
        result = self.client.create_dataset_row("dataset-123", row)
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]['data'], row)

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_dataset_rows(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_dataset_rows("dataset-123")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_dataset_row(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_dataset_row("dataset-123", "row-456")
        mock_get.assert_called_once()
        self.assertEqual(result, {"id": "dataset-123", "status": "success"})

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_dataset_row(self, mock_put):
        mock_put.return_value = self.mock_response
        row = {"dataSetRowInput": "updated input"}
        result = self.client.update_dataset_row("dataset-123", "row-456", row)
        mock_put.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_dataset_row(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_dataset_row("dataset-123", "row-456")
        mock_delete.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_dataset_row_expected_source(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.create_expected_source(
            dataset_id="dataset-123",
            dataset_row_id="row-456",
            expected_source_name="source1",
            expected_source_value="value1",
            expected_source_extension="txt"
        )
        mock_post.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_dataset_row_expected_sources(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_expected_sources("dataset-123", "row-456")
        mock_get.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_expected_source(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_expected_source("dataset-123", "row-456", "source-789")
        mock_get.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_expected_source(self, mock_put):
        mock_put.return_value = self.mock_response
        result = self.client.update_expected_source(
            dataset_id="dataset-123",
            dataset_row_id="row-456",
            expected_source_id="source-789",
            expected_source_name="updated source",
            expected_source_value="updated value",
            expected_source_extension="pdf"
        )
        mock_put.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_expected_source(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_expected_source("dataset-123", "row-456", "source-789")
        mock_delete.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.post')
    def test_create_dataset_row_filter_variable(self, mock_post):
        mock_post.return_value = self.mock_response
        result = self.client.create_filter_variable(
            dataset_id="dataset-123",
            dataset_row_id="row-456",
            metadata_type="type1",
            filter_variable_key="key1",
            filter_variable_value="value1",
            filter_variable_operator="eq"
        )
        mock_post.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_list_dataset_row_filter_variables(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.list_filter_variables("dataset-123", "row-456")
        mock_get.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.get')
    def test_get_filter_variable(self, mock_get):
        mock_get.return_value = self.mock_response
        result = self.client.get_filter_variable("dataset-123", "row-456", "var-789")
        mock_get.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.put')
    def test_update_filter_variable(self, mock_put):
        mock_put.return_value = self.mock_response
        result = self.client.update_filter_variable(
            dataset_id="dataset-123",
            dataset_row_id="row-456",
            filter_variable_id="var-789",
            metadata_type="type2",
            filter_variable_key="updated key",
            filter_variable_value="updated value",
            filter_variable_operator="ne"
        )
        mock_put.assert_called_once()

    @patch('pygeai.core.services.rest.ApiService.delete')
    def test_delete_filter_variable(self, mock_delete):
        mock_delete.return_value = self.mock_response
        result = self.client.delete_filter_variable("dataset-123", "row-456", "var-789")
        mock_delete.assert_called_once()

    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.open')
    @patch('pygeai.core.services.rest.ApiService.post_file_binary')
    def test_upload_dataset_rows_file_success(self, mock_post, mock_open_file, mock_is_file):
        mock_is_file.return_value = True
        mock_file = MagicMock()
        mock_open_file.return_value = mock_file
        mock_post.return_value = self.mock_response

        result = self.client.upload_dataset_rows_file("dataset-123", "/path/to/rows.json")
        
        mock_is_file.assert_called_once()
        mock_open_file.assert_called_once_with("rb")
        mock_post.assert_called_once()
        mock_file.close.assert_called_once()

    @patch('pathlib.Path.is_file')
    def test_upload_dataset_rows_file_not_found(self, mock_is_file):
        mock_is_file.return_value = False
        with self.assertRaises(FileNotFoundError):
            self.client.upload_dataset_rows_file("dataset-123", "/path/to/nonexistent.json")


if __name__ == '__main__':
    unittest.main()
