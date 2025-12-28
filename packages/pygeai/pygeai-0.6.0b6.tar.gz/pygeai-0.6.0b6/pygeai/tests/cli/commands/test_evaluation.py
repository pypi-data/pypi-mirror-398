import unittest
from unittest.mock import patch, Mock, MagicMock
import json

from pygeai.cli.commands.evaluation import (
    show_help,
    list_datasets,
    create_dataset,
    get_dataset,
    update_dataset,
    delete_dataset,
    create_dataset_row,
    list_dataset_rows,
    get_dataset_row,
    update_dataset_row,
    delete_dataset_row,
    create_dataset_row_expected_source,
    list_dataset_row_expected_sources,
    get_dataset_row_expected_source,
    update_dataset_row_expected_source,
    delete_dataset_row_expected_source,
    create_dataset_row_filter_variable,
    list_dataset_row_filter_variables,
    get_dataset_row_filter_variable,
    update_dataset_row_filter_variable,
    delete_dataset_row_filter_variable,
    update_dataset_rows_file,
    list_evaluation_plans,
    create_evaluation_plan,
    get_evaluation_plan,
    update_evaluation_plan,
    delete_evaluation_plan,
    list_evaluation_plan_system_metrics,
    add_evaluation_plan_system_metric,
    get_evaluation_plan_system_metric,
    update_evaluation_plan_system_metric,
    delete_evaluation_plan_system_metric,
    list_system_metrics,
    get_system_metric,
    execute_evaluation_plan,
    list_evaluation_results,
    get_evaluation_result
)
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError


class TestEvaluationCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_evaluation.TestEvaluationCommands
    """

    def test_show_help(self):
        with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    # Dataset Commands Tests
    def test_list_datasets(self):
        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.list_datasets', return_value="Datasets list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_datasets()
                mock_list.assert_called_once()
                mock_stdout.assert_called_once_with("Feedback detail: \nDatasets list")

    def test_create_dataset_with_name(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_name"), "Test Dataset"),
            (Mock(spec=['name'], name="dataset_description"), "Test Description"),
            (Mock(spec=['name'], name="dataset_type"), "T"),
            (Mock(spec=['name'], name="dataset_active"), "1")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_dataset', return_value="Created dataset") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset(option_list)
                mock_create.assert_called_once()
                mock_stdout.assert_called_once_with("New dataset detail: \nCreated dataset")

    def test_create_dataset_with_file(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_file"), "/path/to/file.json")
        ]
        option_list[0][0].name = "dataset_file"

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_dataset_from_file', return_value="Created from file") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset(option_list)
                mock_create.assert_called_once_with(file_path="/path/to/file.json")
                mock_stdout.assert_called_once_with("New dataset detail: \nCreated from file")

    def test_create_dataset_with_rows_dict(self):
        row_data = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input"
        }
        option_list = [
            (Mock(spec=['name'], name="dataset_name"), "Test Dataset"),
            (Mock(spec=['name'], name="row"), json.dumps(row_data))
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_dataset', return_value="Created dataset") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset(option_list)
                mock_create.assert_called_once()

    def test_create_dataset_with_rows_list(self):
        row_data = [
            {
                "dataSetRowExpectedAnswer": "answer",
                "dataSetRowContextDocument": "context",
                "dataSetRowInput": "input"
            }
        ]
        option_list = [
            (Mock(spec=['name'], name="dataset_name"), "Test Dataset"),
            (Mock(spec=['name'], name="row"), json.dumps(row_data))
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_dataset', return_value="Created dataset") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset(option_list)
                mock_create.assert_called_once()

    def test_create_dataset_invalid_row_json(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_name"), "Test Dataset"),
            (Mock(spec=['name'], name="row"), "invalid json")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with self.assertRaises(WrongArgumentError):
            create_dataset(option_list)

    def test_create_dataset_missing_name(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            create_dataset(option_list)
        self.assertEqual(str(context.exception), "Cannot create dataset without specifying dataset name")

    def test_get_dataset_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123")
        ]
        option_list[0][0].name = "dataset_id"

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.get_dataset', return_value="Dataset detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_dataset(option_list)
                mock_get.assert_called_once_with(dataset_id="dataset-123")
                mock_stdout.assert_called_once_with("Dataset detail: \nDataset detail")

    def test_get_dataset_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_dataset(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve dataset without specifying id.")

    def test_update_dataset_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="dataset_name"), "Updated Name"),
            (Mock(spec=['name'], name="dataset_description"), "Updated Description")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.update_dataset', return_value="Updated dataset") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_dataset(option_list)
                mock_update.assert_called_once()
                mock_stdout.assert_called_once_with("Updated dataset detail: \nUpdated dataset")

    def test_update_dataset_missing_id(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_name"), "Updated Name")
        ]
        option_list[0][0].name = "dataset_name"

        with self.assertRaises(MissingRequirementException) as context:
            update_dataset(option_list)
        self.assertEqual(str(context.exception), "Cannot update dataset without specifying id.")

    def test_delete_dataset_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123")
        ]
        option_list[0][0].name = "dataset_id"

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.delete_dataset', return_value="Deleted") as mock_delete:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                delete_dataset(option_list)
                mock_delete.assert_called_once_with(dataset_id="dataset-123")
                mock_stdout.assert_called_once_with("Deleted dataset detail: \nDeleted")

    def test_delete_dataset_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            delete_dataset(option_list)
        self.assertEqual(str(context.exception), "Cannot delete dataset without specifying id.")

    # Dataset Row Commands Tests
    def test_create_dataset_row_success(self):
        row_data = {
            "dataSetRowExpectedAnswer": "answer",
            "dataSetRowContextDocument": "context",
            "dataSetRowInput": "input"
        }
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row"), json.dumps(row_data))
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_dataset_row', return_value="Created row") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset_row(option_list)
                mock_create.assert_called_once()

    def test_create_dataset_row_invalid_json(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row"), "invalid json")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with self.assertRaises(WrongArgumentError):
            create_dataset_row(option_list)

    def test_create_dataset_row_missing_id(self):
        row_data = {"dataSetRowExpectedAnswer": "answer"}
        option_list = [
            (Mock(spec=['name'], name="row"), json.dumps(row_data))
        ]
        option_list[0][0].name = "row"

        with self.assertRaises(MissingRequirementException) as context:
            create_dataset_row(option_list)
        self.assertEqual(str(context.exception), "Cannot create dataset row without specifying id.")

    def test_list_dataset_rows_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123")
        ]
        option_list[0][0].name = "dataset_id"

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.list_dataset_rows', return_value="Rows list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_dataset_rows(option_list)
                mock_list.assert_called_once_with(dataset_id="dataset-123")

    def test_list_dataset_rows_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            list_dataset_rows(option_list)
        self.assertEqual(str(context.exception), "Cannot list dataset rows without specifying id.")

    def test_get_dataset_row_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.get_dataset_row', return_value="Row detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_dataset_row(option_list)
                mock_get.assert_called_once_with(dataset_id="dataset-123", dataset_row_id="row-456")

    def test_get_dataset_row_missing_dataset_id(self):
        option_list = [
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        option_list[0][0].name = "row_id"

        with self.assertRaises(MissingRequirementException) as context:
            get_dataset_row(option_list)
        self.assertEqual(str(context.exception), "Cannot get dataset row without specifying id of dataset and row.")

    def test_get_dataset_row_missing_row_id(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123")
        ]
        option_list[0][0].name = "dataset_id"

        with self.assertRaises(MissingRequirementException) as context:
            get_dataset_row(option_list)
        self.assertEqual(str(context.exception), "Cannot get dataset row without specifying id of dataset and row.")

    def test_update_dataset_row_success(self):
        row_data = {
            "dataSetRowExpectedAnswer": "updated answer",
            "dataSetRowContextDocument": "updated context",
            "dataSetRowInput": "updated input"
        }
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row_id"), "row-456"),
            (Mock(spec=['name'], name="row"), json.dumps(row_data))
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.update_dataset_row', return_value="Updated row") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_dataset_row(option_list)
                mock_update.assert_called_once()

    def test_update_dataset_row_missing_dataset_id(self):
        option_list = [
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        option_list[0][0].name = "row_id"

        with self.assertRaises(MissingRequirementException) as context:
            update_dataset_row(option_list)
        self.assertEqual(str(context.exception), "Cannot update dataset row without specifying id of dataset and row.")

    def test_delete_dataset_row_success(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.delete_dataset_row', return_value="Deleted row") as mock_delete:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                delete_dataset_row(option_list)
                mock_delete.assert_called_once_with(dataset_id="dataset-123", dataset_row_id="row-456")

    def test_delete_dataset_row_missing_dataset_id(self):
        option_list = [
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        option_list[0][0].name = "row_id"

        with self.assertRaises(MissingRequirementException) as context:
            delete_dataset_row(option_list)
        self.assertEqual(str(context.exception), "Cannot delete dataset row without specifying id of dataset and row.")

    # Dataset Row Expected Source Tests
    def test_create_dataset_row_expected_source(self):
        source_data = {
            "dataSetExpectedSourceName": "source1",
            "dataSetExpectedSourceValue": "value1"
        }
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row_id"), "row-456"),
            (Mock(spec=['name'], name="expected_source"), json.dumps(source_data))
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.create_expected_source', return_value="Created source") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_dataset_row_expected_source(option_list)
                mock_create.assert_called_once()

    def test_list_dataset_row_expected_sources(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="row_id"), "row-456")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.list_expected_sources', return_value="Sources list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_dataset_row_expected_sources(option_list)
                mock_list.assert_called_once()

    def test_update_dataset_rows_file(self):
        option_list = [
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="dataset_rows_file"), "/path/to/rows.json")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.dataset.clients.EvaluationDatasetClient.upload_dataset_rows_file', return_value="Updated rows") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_dataset_rows_file(option_list)
                mock_update.assert_called_once()

    # Evaluation Plan Commands Tests
    def test_list_evaluation_plans(self):
        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.list_evaluation_plans', return_value="Plans list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_evaluation_plans()
                mock_list.assert_called_once()

    def test_create_evaluation_plan_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_name"), "Test Plan"),
            (Mock(spec=['name'], name="evaluation_plan_type"), "Test Description"),
            (Mock(spec=['name'], name="evaluation_plan_assistant_id"), "1")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.create_evaluation_plan', return_value="Created plan") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_evaluation_plan(option_list)
                mock_create.assert_called_once()

    def test_create_evaluation_plan_missing_name(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            create_evaluation_plan(option_list)
        self.assertEqual(str(context.exception), "Cannot create evaluation plan without specifying evaluation plan name and type")

    def test_get_evaluation_plan_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123")
        ]
        option_list[0][0].name = "evaluation_plan_id"

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.get_evaluation_plan', return_value="Plan detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_evaluation_plan(option_list)
                mock_get.assert_called_once_with(evaluation_plan_id="plan-123")

    def test_get_evaluation_plan_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_evaluation_plan(option_list)
        self.assertEqual(str(context.exception), "Cannot get evaluation plan without specifying id")

    def test_update_evaluation_plan_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="evaluation_plan_name"), "Updated Plan")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.update_evaluation_plan', return_value="Updated plan") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_evaluation_plan(option_list)
                mock_update.assert_called_once()

    def test_update_evaluation_plan_missing_id(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_name"), "Updated Plan")
        ]
        option_list[0][0].name = "plan_name"

        with self.assertRaises(MissingRequirementException) as context:
            update_evaluation_plan(option_list)
        self.assertEqual(str(context.exception), "Cannot update evaluation plan without specifying id")

    def test_delete_evaluation_plan_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123")
        ]
        option_list[0][0].name = "evaluation_plan_id"

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.delete_evaluation_plan', return_value="Deleted") as mock_delete:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                delete_evaluation_plan(option_list)
                mock_delete.assert_called_once_with(evaluation_plan_id="plan-123")

    def test_delete_evaluation_plan_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            delete_evaluation_plan(option_list)
        self.assertEqual(str(context.exception), "Cannot delete evaluation plan without specifying id")

    # Evaluation Plan System Metric Tests
    def test_list_evaluation_plan_system_metrics_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123")
        ]
        option_list[0][0].name = "evaluation_plan_id"

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.list_evaluation_plan_system_metrics', return_value="Metrics list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_evaluation_plan_system_metrics(option_list)
                mock_list.assert_called_once_with(evaluation_plan_id="plan-123")

    def test_list_evaluation_plan_system_metrics_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            list_evaluation_plan_system_metrics(option_list)
        self.assertEqual(str(context.exception), "Cannot list evaluation plan's system metrics without specifying id")

    def test_add_evaluation_plan_system_metric_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="system_metric_id"), "metric-456"),
            (Mock(spec=['name'], name="system_metric_weight"), "1.0")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.add_evaluation_plan_system_metric', return_value="Added metric") as mock_add:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                add_evaluation_plan_system_metric(option_list)
                mock_add.assert_called_once()

    def test_add_evaluation_plan_system_metric_missing_plan_id(self):
        option_list = [
            (Mock(spec=['name'], name="system_metric_id"), "metric-456")
        ]
        option_list[0][0].name = "system_metric_id"

        with self.assertRaises(MissingRequirementException) as context:
            add_evaluation_plan_system_metric(option_list)
        self.assertEqual(str(context.exception), "Cannot add evaluation plan's system metrics without specifying id")

    def test_get_evaluation_plan_system_metric_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="system_metric_id"), "metric-456")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.get_evaluation_plan_system_metric', return_value="Metric detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_evaluation_plan_system_metric(option_list)
                mock_get.assert_called_once_with(evaluation_plan_id="plan-123", system_metric_id="metric-456")

    def test_get_evaluation_plan_system_metric_missing_plan_id(self):
        option_list = [
            (Mock(spec=['name'], name="system_metric_id"), "metric-456")
        ]
        option_list[0][0].name = "system_metric_id"

        with self.assertRaises(MissingRequirementException) as context:
            get_evaluation_plan_system_metric(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve evaluation plan's system metric without specifying both ids")

    def test_update_evaluation_plan_system_metric_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="system_metric_id"), "metric-456"),
            (Mock(spec=['name'], name="system_metric_weight"), "2.0")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.update_evaluation_plan_system_metric', return_value="Updated metric") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_evaluation_plan_system_metric(option_list)
                mock_update.assert_called_once()

    def test_delete_evaluation_plan_system_metric_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="system_metric_id"), "metric-456")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.delete_evaluation_plan_system_metric', return_value="Deleted metric") as mock_delete:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                delete_evaluation_plan_system_metric(option_list)
                mock_delete.assert_called_once_with(evaluation_plan_id="plan-123", system_metric_id="metric-456")

    # System Metrics Tests
    def test_list_system_metrics(self):
        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.list_system_metrics', return_value="System metrics list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_system_metrics()
                mock_list.assert_called_once()

    def test_get_system_metric_success(self):
        option_list = [
            (Mock(spec=['name'], name="system_metric_id"), "metric-456")
        ]
        option_list[0][0].name = "system_metric_id"

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.get_system_metric', return_value="System metric detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_system_metric(option_list)
                mock_get.assert_called_once_with(system_metric_id="metric-456")

    def test_get_system_metric_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_system_metric(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve system metric without specifying id")

    # Execution Tests
    def test_execute_evaluation_plan_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123"),
            (Mock(spec=['name'], name="dataset_id"), "dataset-123"),
            (Mock(spec=['name'], name="assistant_id"), "assistant-123")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.evaluation.plan.clients.EvaluationPlanClient.execute_evaluation_plan', return_value="Execution result") as mock_execute:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                execute_evaluation_plan(option_list)
                mock_execute.assert_called_once()

    def test_execute_evaluation_plan_missing_plan_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            execute_evaluation_plan(option_list)
        self.assertEqual(str(context.exception), "Cannot execute evaluation plan without specifying id")

    # Result Tests
    def test_list_evaluation_results(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_plan_id"), "plan-123")
        ]
        option_list[0][0].name = "evaluation_plan_id"

        with patch('pygeai.evaluation.result.clients.EvaluationResultClient.list_evaluation_results', return_value="Results list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_evaluation_results(option_list)
                mock_list.assert_called_once()

    def test_get_evaluation_result_success(self):
        option_list = [
            (Mock(spec=['name'], name="evaluation_result_id"), "result-123")
        ]
        option_list[0][0].name = "evaluation_result_id"

        with patch('pygeai.evaluation.result.clients.EvaluationResultClient.get_evaluation_result', return_value="Result detail") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_evaluation_result(option_list)
                mock_get.assert_called_once_with(evaluation_result_id="result-123")

    def test_get_evaluation_result_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_evaluation_result(option_list)
        self.assertEqual(str(context.exception), "Cannot get evaluation results without specifying id")


if __name__ == '__main__':
    unittest.main()
