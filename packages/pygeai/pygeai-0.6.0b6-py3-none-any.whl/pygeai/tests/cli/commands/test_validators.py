import unittest
from pathlib import Path
import tempfile
import os

from pygeai.cli.commands.validators import validate_dataset_file, validate_row_structure, validate_system_metric
from pygeai.core.common.exceptions import WrongArgumentError


class TestValidators(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_validators.TestValidators
    """

    def test_validate_dataset_file_not_found(self):
        with self.assertRaises(FileNotFoundError) as cm:
            validate_dataset_file("nonexistent_file.txt")
        self.assertEqual(str(cm.exception), "Dataset file not found: nonexistent_file.txt")

    def test_validate_dataset_file_not_a_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError) as cm:
                validate_dataset_file(temp_dir)
            self.assertEqual(str(cm.exception), f"Dataset path is not a file: {temp_dir}")

    def test_validate_dataset_file_valid(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name

        try:
            validate_dataset_file(temp_file_path)
        finally:
            os.unlink(temp_file_path)

    def test_validate_row_structure_missing_required_field(self):
        row = {
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input"
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), 'Missing or invalid value for required field "dataSetRowExpectedAnswer". It must be a non-empty string.')

    def test_validate_row_structure_invalid_required_field_type(self):
        row = {
            "dataSetRowExpectedAnswer": 123,
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input"
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), 'Missing or invalid value for required field "dataSetRowExpectedAnswer". It must be a non-empty string.')

    def test_validate_row_structure_invalid_expected_sources_type(self):
        row = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input",
            "expectedSources": "not a list"
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), '"expectedSources" must be a list of objects, even if empty.')

    def test_validate_row_structure_invalid_expected_source_structure(self):
        row = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input",
            "expectedSources": [{"invalid_key": "value"}]
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), 'Each item in "expectedSources" must be a dictionary containing the following string fields: "dataSetExpectedSourceId", "dataSetExpectedSourceName", "dataSetExpectedSourceValue", and "dataSetExpectedSourceExtension".')

    def test_validate_row_structure_invalid_filter_variables_type(self):
        row = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input",
            "expectedSources": [],
            "filterVariables": "not a list"
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), '"filterVariables" must be a list of objects, even if empty.')

    def test_validate_row_structure_invalid_filter_variable_structure(self):
        row = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input",
            "expectedSources": [],
            "filterVariables": [{"invalid_key": "value"}]
        }
        with self.assertRaises(WrongArgumentError) as cm:
            validate_row_structure(row)
        self.assertEqual(str(cm.exception), 'Each item in "filterVariables" must be a dictionary containing the following string fields: "dataSetMetadataType", "dataSetRowFilterKey", "dataSetRowFilterOperator", "dataSetRowFilterValue", and "dataSetRowFilterVarId".')

    def test_validate_row_structure_valid(self):
        row = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input",
            "expectedSources": [{
                "dataSetExpectedSourceId": "id",
                "dataSetExpectedSourceName": "name",
                "dataSetExpectedSourceValue": "value",
                "dataSetExpectedSourceExtension": "ext"
            }],
            "filterVariables": [{
                "dataSetMetadataType": "type",
                "dataSetRowFilterKey": "key",
                "dataSetRowFilterOperator": "op",
                "dataSetRowFilterValue": "val",
                "dataSetRowFilterVarId": "var_id"
            }]
        }
        validate_row_structure(row)

    def test_validate_system_metric_not_dict(self):
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric("not a dict")
        self.assertEqual(str(cm.exception), "Each system metric must be a dictionary.")

    def test_validate_system_metric_missing_required_field(self):
        metric = {"systemMetricWeight": 0.5}
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric(metric)
        self.assertEqual(str(cm.exception), 'Missing required field "systemMetricId" in system metric.')

    def test_validate_system_metric_invalid_id_type(self):
        metric = {"systemMetricId": 123, "systemMetricWeight": 0.5}
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric(metric)
        self.assertEqual(str(cm.exception), '"systemMetricId" must be a non-empty string.')

    def test_validate_system_metric_empty_id(self):
        metric = {"systemMetricId": "", "systemMetricWeight": 0.5}
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric(metric)
        self.assertEqual(str(cm.exception), '"systemMetricId" must be a non-empty string.')

    def test_validate_system_metric_invalid_weight_type(self):
        metric = {"systemMetricId": "id", "systemMetricWeight": "invalid"}
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric(metric)
        self.assertEqual(str(cm.exception), '"systemMetricWeight" must be a number between 0 and 1 (inclusive).')

    def test_validate_system_metric_weight_out_of_range(self):
        metric = {"systemMetricId": "id", "systemMetricWeight": 1.5}
        with self.assertRaises(WrongArgumentError) as cm:
            validate_system_metric(metric)
        self.assertEqual(str(cm.exception), '"systemMetricWeight" must be a number between 0 and 1 (inclusive).')

    def test_validate_system_metric_valid(self):
        metric = {"systemMetricId": "valid_id", "systemMetricWeight": 0.75}
        validate_system_metric(metric)

