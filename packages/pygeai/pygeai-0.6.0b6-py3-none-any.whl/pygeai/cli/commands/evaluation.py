import json

from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.common import get_boolean_value
from pygeai.cli.commands.validators import validate_row_structure, validate_system_metric
from pygeai.cli.texts.help import EVALUATION_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console
from pygeai.evaluation.dataset.clients import EvaluationDatasetClient
from pygeai.evaluation.plan.clients import EvaluationPlanClient
from pygeai.evaluation.result.clients import EvaluationResultClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(evaluation_commands, EVALUATION_HELP_TEXT)
    Console.write_stdout(help_text)


"""
    DATASETS COMMANDS
"""


def list_datasets():
    client = EvaluationDatasetClient()
    result = client.list_datasets()
    Console.write_stdout(f"Feedback detail: \n{result}")


def create_dataset(option_list: list):
    dataset_file = None
    dataset_name = None
    dataset_description = None
    dataset_type = None
    dataset_active = True
    rows = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_file":
            dataset_file = option_arg
        if option_flag.name == "dataset_name":
            dataset_name = option_arg
        if option_flag.name == "dataset_description":
            dataset_description = option_arg
        if option_flag.name == "dataset_type":
            dataset_type = option_arg
        if option_flag.name == "dataset_type":
            dataset_type = option_arg
        if option_flag.name == "dataset_active":
            dataset_active = get_boolean_value(option_arg)
        if option_flag.name == "row":
            try:
                row_json = json.loads(option_arg)
                if isinstance(row_json, dict):
                    rows.append(row_json)
                elif isinstance(row_json, list):
                    rows = row_json
            except Exception:
                raise WrongArgumentError(
                    'Each dataset row must be in JSON format: '
                    '\'{"dataSetRowExpectedAnswer": "string", "dataSetRowContextDocument": "string", '
                    '"dataSetRowInput": "string", "expectedSources": [ {...} ], "filterVariables": [ {...} ]}\' '
                    'It must be a dictionary containing dataSetRowExpectedAnswer, dataSetRowContextDocument, '
                    'and dataSetRowInput as strings. The expectedSources array, if present, must contain dictionaries with '
                    'dataSetExpectedSourceId, dataSetExpectedSourceName, dataSetExpectedSourceValue, and dataSetExpectedSourceExtension as strings. '
                    'The filterVariables array, if present, must contain dictionaries with dataSetMetadataType, dataSetRowFilterKey, '
                    'dataSetRowFilterOperator, dataSetRowFilterValue, and dataSetRowFilterVarId as strings.'
                )

    client = EvaluationDatasetClient()

    if dataset_file:
        result = client.create_dataset_from_file(
            file_path=dataset_file
        )
    elif not dataset_name:
        raise MissingRequirementException("Cannot create dataset without specifying dataset name")
    else:
        for row in rows:
            validate_row_structure(row)

        result = client.create_dataset(
            dataset_name=dataset_name,
            dataset_description=dataset_description,
            dataset_type=dataset_type,
            dataset_active=dataset_active,
            rows=rows
        )

    Console.write_stdout(f"New dataset detail: \n{result}")


create_dataset_options = [
    Option(
        "dataset_name",
        ["--dataset-name", "--dn"],
        "dataSetName: string",
        True
    ),
    Option(
        "dataset_description",
        ["--dataset-description", "--dd"],
        "dataSetDescription: string",
        True
    ),
    Option(
        "dataset_type",
        ["--dataset-type", "--dt"],
        "dataSetType: string //e.g., 'T' for test, 'E' for evaluation, etc.",
        True
    ),
    Option(
        "dataset_active",
        ["--dataset-active", "--da"],
        "dataSetActive: boolean. 0: False; 1: True",
        True
    ),
    Option(
        "row",
        ["--row", "-r"],
        "JSON object containing row data",
        True
    ),
    Option(
        "dataset_file",
        ["--dataset-file", "--df"],
        "dataSetActive: Creates a new dataset from a JSON file. The file must contain the complete "
        "dataset structure, including header information and rows.",
        True
    ),
]


def get_dataset(option_list: list):
    dataset_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg

    if not dataset_id:
        raise MissingRequirementException("Cannot retrieve dataset without specifying id.")

    client = EvaluationDatasetClient()
    result = client.get_dataset(
        dataset_id=dataset_id
    )
    Console.write_stdout(f"Dataset detail: \n{result}")


get_dataset_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
]


def update_dataset(option_list: list):
    dataset_id = None
    dataset_name = None
    dataset_description = None
    dataset_type = None
    dataset_active = True
    rows = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "dataset_name":
            dataset_name = option_arg
        if option_flag.name == "dataset_description":
            dataset_description = option_arg
        if option_flag.name == "dataset_type":
            dataset_type = option_arg
        if option_flag.name == "dataset_type":
            dataset_type = option_arg
        if option_flag.name == "dataset_active":
            dataset_active = get_boolean_value(option_arg)
        if option_flag.name == "row":
            try:
                row_json = json.loads(option_arg)
                if isinstance(row_json, dict):
                    rows.append(row_json)
                elif isinstance(row_json, list):
                    rows = row_json
            except Exception:
                raise WrongArgumentError(
                    'Each dataset row must be in JSON format: '
                    '\'{"dataSetRowExpectedAnswer": "string", "dataSetRowContextDocument": "string", '
                    '"dataSetRowInput": "string", "expectedSources": [ {...} ], "filterVariables": [ {...} ]}\' '
                    'It must be a dictionary containing dataSetRowExpectedAnswer, dataSetRowContextDocument, '
                    'and dataSetRowInput as strings. The expectedSources array, if present, must contain dictionaries with '
                    'dataSetExpectedSourceId, dataSetExpectedSourceName, dataSetExpectedSourceValue, and dataSetExpectedSourceExtension as strings. '
                    'The filterVariables array, if present, must contain dictionaries with dataSetMetadataType, dataSetRowFilterKey, '
                    'dataSetRowFilterOperator, dataSetRowFilterValue, and dataSetRowFilterVarId as strings.'
                )

    if not dataset_id:
        raise MissingRequirementException("Cannot update dataset without specifying id.")

    for row in rows:
        validate_row_structure(row)

    client = EvaluationDatasetClient()
    result = client.update_dataset(
        dataset_id=dataset_id,
        dataset_name=dataset_name,
        dataset_description=dataset_description,
        dataset_type=dataset_type,
        dataset_active=dataset_active,
        rows=rows,
    )
    Console.write_stdout(f"Updated dataset detail: \n{result}")


update_dataset_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "dataset_name",
        ["--dataset-name", "--dn"],
        "dataSetName: string",
        True
    ),
    Option(
        "dataset_description",
        ["--dataset-description", "--dd"],
        "dataSetDescription: string",
        True
    ),
    Option(
        "dataset_type",
        ["--dataset-type", "--dt"],
        "dataSetType: string //e.g., 'T' for test, 'E' for evaluation, etc.",
        True
    ),
    Option(
        "dataset_active",
        ["--dataset-active", "--da"],
        "dataSetActive: boolean. 0: False; 1: True",
        True
    ),
    Option(
        "row",
        ["--row", "-r"],
        "JSON object containing row data",
        True
    ),
]


def delete_dataset(option_list: list):
    dataset_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg

    if not dataset_id:
        raise MissingRequirementException("Cannot delete dataset without specifying id.")

    client = EvaluationDatasetClient()
    result = client.delete_dataset(
        dataset_id=dataset_id
    )
    Console.write_stdout(f"Deleted dataset detail: \n{result}")


delete_dataset_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
]


def create_dataset_row(option_list: list):
    dataset_id = None
    row = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row":
            try:
                row_json = json.loads(option_arg)
                if not isinstance(row_json, dict):
                    raise ValueError

                row = row_json
            except Exception:
                raise WrongArgumentError(
                    'Each dataset row must be in JSON format: '
                    '\'{"dataSetRowExpectedAnswer": "string", "dataSetRowContextDocument": "string", '
                    '"dataSetRowInput": "string", "expectedSources": [ {...} ], "filterVariables": [ {...} ]}\' '
                    'It must be a dictionary containing dataSetRowExpectedAnswer, dataSetRowContextDocument, '
                    'and dataSetRowInput as strings. The expectedSources array, if present, must contain dictionaries with '
                    'dataSetExpectedSourceId, dataSetExpectedSourceName, dataSetExpectedSourceValue, and dataSetExpectedSourceExtension as strings. '
                    'The filterVariables array, if present, must contain dictionaries with dataSetMetadataType, dataSetRowFilterKey, '
                    'dataSetRowFilterOperator, dataSetRowFilterValue, and dataSetRowFilterVarId as strings.'
                )

    if not dataset_id:
        raise MissingRequirementException("Cannot create dataset row without specifying id.")

    validate_row_structure(row)

    client = EvaluationDatasetClient()
    result = client.create_dataset_row(
        dataset_id=dataset_id,
        row=row
    )
    Console.write_stdout(f"Deleted dataset detail: \n{result}")


create_dataset_row_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row",
        ["--row", "-r"],
        "JSON object containing row data",
        True
    ),
]


def list_dataset_rows(option_list: list):
    dataset_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg

    if not dataset_id:
        raise MissingRequirementException("Cannot list dataset rows without specifying id.")

    client = EvaluationDatasetClient()
    result = client.list_dataset_rows(
        dataset_id=dataset_id
    )
    Console.write_stdout(f"Dataset rows: \n{result}")


list_dataset_rows_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
]


def get_dataset_row(option_list: list):
    dataset_id = None
    row_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot get dataset row without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.get_dataset_row(
        dataset_id=dataset_id,
        dataset_row_id=row_id
    )
    Console.write_stdout(f"Row detail: \n{result}")


get_dataset_row_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
]


def update_dataset_row(option_list: list):
    dataset_id = None
    row_id = None
    row = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "row":
            try:
                row_json = json.loads(option_arg)
                if not isinstance(row_json, dict):
                    raise ValueError

                row = row_json
            except Exception:
                raise WrongArgumentError(
                    'Each dataset row must be in JSON format: '
                    '\'{"dataSetRowExpectedAnswer": "string", "dataSetRowContextDocument": "string", '
                    '"dataSetRowInput": "string", "expectedSources": [ {...} ], "filterVariables": [ {...} ]}\' '
                    'It must be a dictionary containing dataSetRowExpectedAnswer, dataSetRowContextDocument, '
                    'and dataSetRowInput as strings. The expectedSources array, if present, must contain dictionaries with '
                    'dataSetExpectedSourceId, dataSetExpectedSourceName, dataSetExpectedSourceValue, and dataSetExpectedSourceExtension as strings. '
                    'The filterVariables array, if present, must contain dictionaries with dataSetMetadataType, dataSetRowFilterKey, '
                    'dataSetRowFilterOperator, dataSetRowFilterValue, and dataSetRowFilterVarId as strings.'
                )

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot update dataset row without specifying id of dataset and row.")

    validate_row_structure(row)

    client = EvaluationDatasetClient()
    result = client.update_dataset_row(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        row=row
    )
    Console.write_stdout(f"Row detail: \n{result}")


update_dataset_row_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "row",
        ["--row", "-r"],
        "JSON object containing row data",
        True
    ),
]


def delete_dataset_row(option_list: list):
    dataset_id = None
    row_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot delete dataset row without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.delete_dataset_row(
        dataset_id=dataset_id,
        dataset_row_id=row_id
    )
    Console.write_stdout(f"Deleted row detail: \n{result}")


delete_dataset_row_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
]


def create_dataset_row_expected_source(option_list: list):
    dataset_id = None
    row_id = None
    name = None
    value = None
    extension = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "value":
            value = option_arg
        if option_flag.name == "extension":
            extension = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot create dataset row expected source without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.create_expected_source(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        expected_source_name=name,
        expected_source_value=value,
        expected_source_extension=extension,
    )
    Console.write_stdout(f"Extended source detail: \n{result}")


create_dataset_row_expected_source_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "dataset_expected_source_name",
        ["--name", "-n"],
        "dataSetExpectedSourceName: string",
        True
    ),
    Option(
        "dataset_expected_source_value",
        ["--value", "-v"],
        "dataSetExpectedSourceValue: string",
        True
    ),
    Option(
        "dataset_expected_source_extension",
        ["--extension", "-e"],
        "dataSetExpectedSourceExtension: string //e.g., 'txt', 'pdf', 'json'",
        True
    ),
]


def list_dataset_row_expected_sources(option_list: list):
    dataset_id = None
    row_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot list dataset row expected sources without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.list_expected_sources(
        dataset_id=dataset_id,
        dataset_row_id=row_id
    )
    Console.write_stdout(f"Expected sources: \n{result}")


list_dataset_row_expected_sources_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
]


def get_dataset_row_expected_source(option_list: list):
    dataset_id = None
    row_id = None
    expected_source_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "expected_source_id":
            expected_source_id = option_arg

    if not (dataset_id and row_id and expected_source_id):
        raise MissingRequirementException("Cannot get expected sources without specifying id of dataset, row and expected source.")

    client = EvaluationDatasetClient()
    result = client.get_expected_source(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        expected_source_id=expected_source_id
    )
    Console.write_stdout(f"Expected source detail: \n{result}")


get_dataset_row_expected_source_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "expected_source_id",
        ["--expected-source-id", "--esid"],
        "UUID representing the expected source to retrieve",
        True
    ),
]


def update_dataset_row_expected_source(option_list: list):
    dataset_id = None
    row_id = None
    expected_source_id = None
    name = None
    value = None
    extension = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "expected_source_id":
            expected_source_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "value":
            value = option_arg
        if option_flag.name == "extension":
            extension = option_arg

    if not (dataset_id and row_id and expected_source_id):
        raise MissingRequirementException("Cannot update expected sources without specifying id of dataset, row and expected source.")

    client = EvaluationDatasetClient()
    result = client.update_expected_source(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        expected_source_id=expected_source_id,
        expected_source_name=name,
        expected_source_value=value,
        expected_source_extension=extension,

    )
    Console.write_stdout(f"Updated expected source detail: \n{result}")


update_dataset_row_expected_source_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "expected_source_id",
        ["--expected-source-id", "--esid"],
        "UUID representing the expected source to retrieve",
        True
    ),
    Option(
        "dataset_expected_source_name",
        ["--name", "-n"],
        "dataSetExpectedSourceName: string",
        True
    ),
    Option(
        "dataset_expected_source_value",
        ["--value", "-v"],
        "dataSetExpectedSourceValue: string",
        True
    ),
    Option(
        "dataset_expected_source_extension",
        ["--extension", "-e"],
        "dataSetExpectedSourceExtension: string //e.g., 'txt', 'pdf', 'json'",
        True
    ),
]


def delete_dataset_row_expected_source(option_list: list):
    dataset_id = None
    row_id = None
    expected_source_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "expected_source_id":
            expected_source_id = option_arg

    if not (dataset_id and row_id and expected_source_id):
        raise MissingRequirementException("Cannot delete expected sources without specifying id of dataset, row and expected source.")

    client = EvaluationDatasetClient()
    result = client.delete_expected_source(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        expected_source_id=expected_source_id
    )
    Console.write_stdout(f"Deleted expected source detail: \n{result}")


delete_dataset_row_expected_source_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "expected_source_id",
        ["--expected-source-id", "--esid"],
        "UUID representing the expected source to retrieve",
        True
    ),
]


def create_dataset_row_filter_variable(option_list: list):
    dataset_id = None
    row_id = None
    metadata_type = None
    key = None
    value = None
    operator = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "metadata_type":
            metadata_type = option_arg
        if option_flag.name == "key":
            key = option_arg
        if option_flag.name == "value":
            value = option_arg
        if option_flag.name == "operator":
            operator = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot create dataset row filter variable without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.create_filter_variable(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        metadata_type=metadata_type,
        filter_variable_key=key,
        filter_variable_value=value,
        filter_variable_operator=operator,
    )
    Console.write_stdout(f"Filter variable detail: \n{result}")


create_dataset_row_filter_variable_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "dataset_metadata_type",
        ["--metadata-type", "--mt"],
        "dataSetMetadataType: string //e.g., 'V' for variable, 'F' for flag, etc.",
        True
    ),
    Option(
        "dataset_filter_variable_key",
        ["--key", "-k"],
        "dataSetRowFilterKey: string. The name of the filter key",
        True
    ),
    Option(
        "dataset_filter_variable_value",
        ["--value", "-v"],
        "dataSetRowFilterValue: string. The value to filter by",
        True
    ),
    Option(
        "dataset_filter_variable_operator",
        ["--operator", "-o"],
        "dataSetRowFilterOperator: string ///e.g., '=', '!=', '>', '<', 'contains', etc.",
        True
    ),
]


def list_dataset_row_filter_variables(option_list: list):
    dataset_id = None
    row_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg

    if not (dataset_id and row_id):
        raise MissingRequirementException("Cannot list dataset row filter variables without specifying id of dataset and row.")

    client = EvaluationDatasetClient()
    result = client.list_filter_variables(
        dataset_id=dataset_id,
        dataset_row_id=row_id
    )
    Console.write_stdout(f"Filter variables: \n{result}")


list_dataset_row_filter_variables_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
]


def get_dataset_row_filter_variable(option_list: list):
    dataset_id = None
    row_id = None
    filter_variable_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "filter_variable_id":
            filter_variable_id = option_arg

    if not (dataset_id and row_id and filter_variable_id):
        raise MissingRequirementException("Cannot get filter variables without specifying id of dataset, row and filter variable.")

    client = EvaluationDatasetClient()
    result = client.get_filter_variable(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        filter_variable_id=filter_variable_id
    )
    Console.write_stdout(f"Filter variable detail: \n{result}")


get_dataset_row_filter_variable_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "filter_variable_id",
        ["--filter-variable-id", "--fvid"],
        "UUID representing the filter variable to retrieve",
        True
    ),
]


def update_dataset_row_filter_variable(option_list: list):
    dataset_id = None
    row_id = None
    filter_variable_id = None
    metadata_type = None
    key = None
    value = None
    operator = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "filter_variable_id":
            filter_variable_id = option_arg
        if option_flag.name == "metadata_type":
            metadata_type = option_arg
        if option_flag.name == "key":
            key = option_arg
        if option_flag.name == "value":
            value = option_arg
        if option_flag.name == "operator":
            operator = option_arg

    if not (dataset_id and row_id and filter_variable_id):
        raise MissingRequirementException("Cannot update filter variables without specifying id of dataset, row and filter variable.")

    client = EvaluationDatasetClient()
    result = client.update_filter_variable(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        filter_variable_id=filter_variable_id,
        metadata_type=metadata_type,
        filter_variable_key=key,
        filter_variable_value=value,
        filter_variable_operator=operator,
    )
    Console.write_stdout(f"Updated filter variable detail: \n{result}")


update_dataset_row_filter_variable_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "filter_variable_id",
        ["--filter-variable-id", "--fvid"],
        "UUID representing the filter variable to retrieve",
        True
    ),
    Option(
        "dataset_metadata_type",
        ["--metadata-type", "--mt"],
        "dataSetMetadataType: string //e.g., 'V' for variable, 'F' for flag, etc.",
        True
    ),
    Option(
        "dataset_filter_variable_key",
        ["--key", "-k"],
        "dataSetRowFilterKey: string. The name of the filter key",
        True
    ),
    Option(
        "dataset_filter_variable_value",
        ["--value", "-v"],
        "dataSetRowFilterValue: string. The value to filter by",
        True
    ),
    Option(
        "dataset_filter_variable_operator",
        ["--operator", "-o"],
        "dataSetRowFilterOperator: string ///e.g., '=', '!=', '>', '<', 'contains', etc.",
        True
    ),
]


def delete_dataset_row_filter_variable(option_list: list):
    dataset_id = None
    row_id = None
    filter_variable_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "row_id":
            row_id = option_arg
        if option_flag.name == "filter_variable_id":
            filter_variable_id = option_arg

    if not (dataset_id and row_id and filter_variable_id):
        raise MissingRequirementException("Cannot delete filter variables without specifying id of dataset, row and filter variable.")

    client = EvaluationDatasetClient()
    result = client.delete_filter_variable(
        dataset_id=dataset_id,
        dataset_row_id=row_id,
        filter_variable_id=filter_variable_id
    )
    Console.write_stdout(f"Deleted filter variable detail: \n{result}")


delete_dataset_row_filter_variable_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "row_id",
        ["--row-id", "--rid"],
        "UUID representing the row dataset to retrieve",
        True
    ),
    Option(
        "filter_variable_id",
        ["--filter-variable-id", "--fvid"],
        "UUID representing the filter variable to retrieve",
        True
    ),
]


def update_dataset_rows_file(option_list: list):
    dataset_id = None
    dataset_rows_file = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "dataset_rows_file":
            dataset_rows_file = option_arg

    if not (dataset_id and dataset_rows_file):
        raise MissingRequirementException("Cannot upload dataset rows file without specifying id of dataset, rows file")

    client = EvaluationDatasetClient()
    result = client.upload_dataset_rows_file(
        dataset_id=dataset_id,
        file_path=dataset_rows_file
    )
    Console.write_stdout(f"Dataset rows file detail: \n{result}")


update_dataset_rows_file_options = [
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "UUID representing the dataset to retrieve",
        True
    ),
    Option(
        "dataset_rows_file",
        ["--rows-file", "--rf"],
        "The JSON file should contain an array of DatasetRow objects",
        True
    ),
]


"""
    EVALUATION PLANS COMMANDS
"""


def list_evaluation_plans():
    client = EvaluationPlanClient()
    result = client.list_evaluation_plans()
    Console.write_stdout(f"Evaluation plans: \n{result}")


def create_evaluation_plan(option_list: list):
    evaluation_plan_name = None
    evaluation_plan_type = None
    evaluation_plan_assistant_id = None
    evaluation_plan_assistant_name = None
    evaluation_plan_assistant_revision = None
    evaluation_plan_profile_name = None
    dataset_id = None
    system_metrics = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_name":
            evaluation_plan_name = option_arg
        if option_flag.name == "evaluation_plan_type":
            evaluation_plan_type = option_arg
        if option_flag.name == "evaluation_plan_assistant_id":
            evaluation_plan_assistant_id = option_arg
        if option_flag.name == "evaluation_plan_assistant_name":
            evaluation_plan_assistant_name = option_arg
        if option_flag.name == "evaluation_plan_assistant_revision":
            evaluation_plan_assistant_revision = option_arg
        if option_flag.name == "evaluation_plan_profile_name":
            evaluation_plan_profile_name = option_arg
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "system_metrics":
            try:
                metrics_json = json.loads(option_arg)
                if isinstance(metrics_json, dict):
                    system_metrics.append(metrics_json)
                elif isinstance(metrics_json, list):
                    system_metrics = metrics_json
            except Exception:
                raise WrongArgumentError(
                    'Each system metric must be in JSON format: '
                    '\'{"systemMetricId": "string", "systemMetricWeight": 0.0}\' '
                    'It must be a dictionary containing systemMetricId as a string and systemMetricWeight as a float between 0 and 1.'
                )

    if not (evaluation_plan_name and evaluation_plan_type):
        # TODO -> Review required fields
        raise MissingRequirementException("Cannot create evaluation plan without specifying evaluation plan name and type")

    for metric in system_metrics:
        validate_system_metric(metric)

    client = EvaluationPlanClient()
    result = client.create_evaluation_plan(
        name=evaluation_plan_name,
        type=evaluation_plan_type,
        assistant_id=evaluation_plan_assistant_id,
        assistant_name=evaluation_plan_assistant_name,
        assistant_revision=evaluation_plan_assistant_revision,
        profile_name=evaluation_plan_profile_name,
        dataset_id=dataset_id,
        system_metrics=system_metrics,
    )
    Console.write_stdout(f"New evaluation plan detail: \n{result}")


create_evaluation_plan_options = [
    Option(
        "evaluation_plan_name",
        ["--name", "--epn"],
        "Name of the evaluation plan",
        True
    ),
    Option(
        "evaluation_plan_type",
        ["--assistant-type", "--epat"],
        "Type of assistant (e.g., 'TextPromptAssistant', 'RAG Assistant')",
        True
    ),
    Option(
        "evaluation_plan_assistant_id",
        ["--assistant-id", "--epai"],
        "UUID of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_assistant_name",
        ["--assistant-name", "--epan"],
        "Name of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_assistant_revision",
        ["--assistant-revision", "--epar"],
        "Revision of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_profile_name",
        ["--profile-name", "--eppn"],
        "Name of the RAG profile (optional, required for RAG Assistant)",
        True
    ),
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "ID of the dataset (optional)",
        True
    ),
    Option(
        "system_metrics",
        ["--system-metrics", "--sm"],
        "Array of system metrics (each with 'systemMetricId' and 'systemMetricWeight')"
        "Alternatively, multiple instances of --sm can be passes as arguments for a single list.",
        True
    )
]


def get_evaluation_plan(option_list: list):
    evaluation_plan_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot get evaluation plan without specifying id")

    client = EvaluationPlanClient()
    result = client.get_evaluation_plan(
        evaluation_plan_id=evaluation_plan_id
    )
    Console.write_stdout(f"Evaluation plan detail: \n{result}")


get_evaluation_plan_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
]


def update_evaluation_plan(option_list: list):
    evaluation_plan_id = None
    evaluation_plan_name = None
    evaluation_plan_type = None
    evaluation_plan_assistant_id = None
    evaluation_plan_assistant_name = None
    evaluation_plan_assistant_revision = None
    evaluation_plan_profile_name = None
    dataset_id = None
    system_metrics = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg
        if option_flag.name == "evaluation_plan_name":
            evaluation_plan_name = option_arg
        if option_flag.name == "evaluation_plan_type":
            evaluation_plan_type = option_arg
        if option_flag.name == "evaluation_plan_assistant_id":
            evaluation_plan_assistant_id = option_arg
        if option_flag.name == "evaluation_plan_assistant_name":
            evaluation_plan_assistant_name = option_arg
        if option_flag.name == "evaluation_plan_assistant_revision":
            evaluation_plan_assistant_revision = option_arg
        if option_flag.name == "evaluation_plan_profile_name":
            evaluation_plan_profile_name = option_arg
        if option_flag.name == "dataset_id":
            dataset_id = option_arg
        if option_flag.name == "system_metrics":
            try:
                metrics_json = json.loads(option_arg)
                if isinstance(metrics_json, dict):
                    system_metrics.append(metrics_json)
                elif isinstance(metrics_json, list):
                    system_metrics = metrics_json
            except Exception:
                raise WrongArgumentError(
                    'Each system metric must be in JSON format: '
                    '\'{"systemMetricId": "string", "systemMetricWeight": 0.0}\' '
                    'It must be a dictionary containing systemMetricId as a string and systemMetricWeight as a float between 0 and 1.'
                )

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot update evaluation plan without specifying id")

    for metric in system_metrics:
        validate_system_metric(metric)

    client = EvaluationPlanClient()
    result = client.update_evaluation_plan(
        evaluation_plan_id=evaluation_plan_id,
        name=evaluation_plan_name,
        type=evaluation_plan_type,
        assistant_id=evaluation_plan_assistant_id,
        assistant_name=evaluation_plan_assistant_name,
        assistant_revision=evaluation_plan_assistant_revision,
        profile_name=evaluation_plan_profile_name,
        dataset_id=dataset_id,
        system_metrics=system_metrics,
    )
    Console.write_stdout(f"Updated evaluation plan: \n{result}")


update_evaluation_plan_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
    Option(
        "evaluation_plan_name",
        ["--name", "--epn"],
        "Name of the evaluation plan",
        True
    ),
    Option(
        "evaluation_plan_type",
        ["--assistant-type", "--epat"],
        "Type of assistant (e.g., 'TextPromptAssistant', 'RAG Assistant')",
        True
    ),
    Option(
        "evaluation_plan_assistant_id",
        ["--assistant-id", "--epai"],
        "UUID of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_assistant_name",
        ["--assistant-name", "--epan"],
        "Name of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_assistant_revision",
        ["--assistant-revision", "--epar"],
        "Revision of the assistant (optional, required for TextPromptAssistant)",
        True
    ),
    Option(
        "evaluation_plan_profile_name",
        ["--profile-name", "--eppn"],
        "Name of the RAG profile (optional, required for RAG Assistant)",
        True
    ),
    Option(
        "dataset_id",
        ["--dataset-id", "--did"],
        "ID of the dataset (optional)",
        True
    ),
    Option(
        "system_metrics",
        ["--system-metrics", "--sm"],
        "Array of system metrics (each with 'systemMetricId' and 'systemMetricWeight')"
        "Alternatively, multiple instances of --sm can be passes as arguments for a single list.",
        True
    )
]


def delete_evaluation_plan(option_list: list):
    evaluation_plan_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot delete evaluation plan without specifying id")

    client = EvaluationPlanClient()
    result = client.delete_evaluation_plan(
        evaluation_plan_id=evaluation_plan_id
    )
    Console.write_stdout(f"Deleted evaluation plan: \n{result}")


delete_evaluation_plan_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
]


def list_evaluation_plan_system_metrics(option_list: list):
    evaluation_plan_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot list evaluation plan's system metrics without specifying id")

    client = EvaluationPlanClient()
    result = client.list_evaluation_plan_system_metrics(
        evaluation_plan_id=evaluation_plan_id
    )
    Console.write_stdout(f"Evaluation plan's system metrics: \n{result}")


list_evaluation_plan_system_metrics_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
]


def add_evaluation_plan_system_metric(option_list: list):
    evaluation_plan_id = None
    system_metric_id = None
    system_metric_weight = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg
        if option_flag.name == "system_metric_id":
            system_metric_id = option_arg
        if option_flag.name == "system_metric_weight":
            system_metric_weight = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot add evaluation plan's system metrics without specifying id")

    client = EvaluationPlanClient()
    result = client.add_evaluation_plan_system_metric(
        evaluation_plan_id=evaluation_plan_id,
        system_metric_id=system_metric_id,
        system_metric_weight=system_metric_weight

    )
    Console.write_stdout(f"Evaluation plan's system metrics: \n{result}")


add_evaluation_plan_system_metric_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
    Option(
        "system_metric_id",
        ["--system-metric-id", "--smid"],
        "systemMetricId: string. ID of the system metric",
        True
    ),
    Option(
        "system_metric_weight",
        ["--system-metric-weight", "--smw"],
        "systemMetricWeight: number. Weight of the system metric (between 0 and 1)",
        True
    ),
]


def get_evaluation_plan_system_metric(option_list: list):
    evaluation_plan_id = None
    system_metric_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg
        if option_flag.name == "system_metric_id":
            system_metric_id = option_arg

    if not (evaluation_plan_id and system_metric_id):
        raise MissingRequirementException("Cannot retrieve evaluation plan's system metric without specifying both ids")

    client = EvaluationPlanClient()
    result = client.get_evaluation_plan_system_metric(
        evaluation_plan_id=evaluation_plan_id,
        system_metric_id=system_metric_id
    )
    Console.write_stdout(f"Evaluation plan's system metric: \n{result}")


get_evaluation_plan_system_metric_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
    Option(
        "system_metric_id",
        ["--system-metric-id", "--smid"],
        "ID of the system metric",
        True
    ),
]


def update_evaluation_plan_system_metric(option_list: list):
    evaluation_plan_id = None
    system_metric_id = None
    system_metric_weight = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg
        if option_flag.name == "system_metric_id":
            system_metric_id = option_arg
        if option_flag.name == "system_metric_weight":
            system_metric_weight = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot update evaluation plan's system metrics without specifying both ids and weight")

    client = EvaluationPlanClient()
    result = client.update_evaluation_plan_system_metric(
        evaluation_plan_id=evaluation_plan_id,
        system_metric_id=system_metric_id,
        system_metric_weight=system_metric_weight

    )
    Console.write_stdout(f"Evaluation plan's system metrics: \n{result}")


update_evaluation_plan_system_metric_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
    Option(
        "system_metric_id",
        ["--system-metric-id", "--smid"],
        "systemMetricId: string. ID of the system metric",
        True
    ),
    Option(
        "system_metric_weight",
        ["--system-metric-weight", "--smw"],
        "systemMetricWeight: number. Weight of the system metric (between 0 and 1)",
        True
    ),
]


def delete_evaluation_plan_system_metric(option_list: list):
    evaluation_plan_id = None
    system_metric_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg
        if option_flag.name == "system_metric_id":
            system_metric_id = option_arg

    if not (evaluation_plan_id and system_metric_id):
        raise MissingRequirementException("Cannot delete evaluation plan's system metric without specifying both ids")

    client = EvaluationPlanClient()
    result = client.delete_evaluation_plan_system_metric(
        evaluation_plan_id=evaluation_plan_id,
        system_metric_id=system_metric_id
    )
    Console.write_stdout(f"Evaluation plan's system metric: \n{result}")


delete_evaluation_plan_system_metric_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
    Option(
        "system_metric_id",
        ["--system-metric-id", "--smid"],
        "ID of the system metric",
        True
    ),
]


def list_system_metrics():
    client = EvaluationPlanClient()
    result = client.list_system_metrics()
    Console.write_stdout(f"Available system metrics: \n{result}")


def get_system_metric(option_list: list):
    system_metric_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "system_metric_id":
            system_metric_id = option_arg

    if not system_metric_id:
        raise MissingRequirementException("Cannot retrieve system metric without specifying id")

    client = EvaluationPlanClient()
    result = client.get_system_metric(
        system_metric_id=system_metric_id
    )
    Console.write_stdout(f"System metric: \n{result}")


get_system_metric_options = [
    Option(
        "system_metric_id",
        ["--system-metric-id", "--smid"],
        "ID of the system metric",
        True
    ),
]


def execute_evaluation_plan(option_list: list):
    evaluation_plan_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot execute evaluation plan without specifying id")

    client = EvaluationPlanClient()
    result = client.execute_evaluation_plan(
        evaluation_plan_id=evaluation_plan_id,
    )
    Console.write_stdout(f"Evaluation plan execution: \n{result}")


execute_evaluation_plan_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
]

"""
    DATASETS COMMANDS
"""


def list_evaluation_results(option_list: list):
    evaluation_plan_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_plan_id":
            evaluation_plan_id = option_arg

    if not evaluation_plan_id:
        raise MissingRequirementException("Cannot list evaluation results without specifying id")

    client = EvaluationResultClient()
    result = client.list_evaluation_results(
        evaluation_plan_id=evaluation_plan_id,
    )
    Console.write_stdout(f"Evaluation results: \n{result}")


list_evaluation_results_options = [
    Option(
        "evaluation_plan_id",
        ["--evaluation-plan-id", "--epid"],
        "UUID representing the evaluation plan to retrieve",
        True
    ),
]


def get_evaluation_result(option_list: list):
    evaluation_result_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "evaluation_result_id":
            evaluation_result_id = option_arg

    if not evaluation_result_id:
        raise MissingRequirementException("Cannot get evaluation results without specifying id")

    client = EvaluationResultClient()
    result = client.get_evaluation_result(
        evaluation_result_id=evaluation_result_id,
    )
    Console.write_stdout(f"Evaluation result: \n{result}")


get_evaluation_result_options = [
    Option(
        "evaluation_result_id",
        ["--evaluation-result-id", "--erid"],
        "UUID representing the evaluation result to retrieve",
        True
    ),
]


evaluation_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "list_datasets",
        ["list-datasets", "ld"],
        "List all datasets",
        list_datasets,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "create_dataset",
        ["create-dataset", "cd"],
        "Create dataset",
        create_dataset,
        ArgumentsEnum.REQUIRED,
        [],
        create_dataset_options
    ),
    Command(
        "get_dataset",
        ["get-dataset", "gd"],
        "Get dataset by ID",
        get_dataset,
        ArgumentsEnum.REQUIRED,
        [],
        get_dataset_options
    ),
    Command(
        "update_dataset",
        ["update-dataset", "ud"],
        "Update dataset by ID",
        update_dataset,
        ArgumentsEnum.REQUIRED,
        [],
        update_dataset_options
    ),
    Command(
        "delete_dataset",
        ["delete-dataset", "dd"],
        "Delete dataset by ID",
        delete_dataset,
        ArgumentsEnum.REQUIRED,
        [],
        delete_dataset_options
    ),
    Command(
        "create_dataset_row",
        ["create-dataset-row", "cdr"],
        "Create dataset row",
        create_dataset_row,
        ArgumentsEnum.REQUIRED,
        [],
        create_dataset_row_options
    ),
    Command(
        "list_dataset_rows",
        ["list-dataset-rows", "ldr"],
        "List dataset rows",
        list_dataset_rows,
        ArgumentsEnum.REQUIRED,
        [],
        list_dataset_rows_options
    ),
    Command(
        "get_dataset_row",
        ["get-dataset-row", "gdr"],
        "Get dataset row",
        get_dataset_row,
        ArgumentsEnum.REQUIRED,
        [],
        get_dataset_row_options
    ),
    Command(
        "update_dataset_row",
        ["update-dataset-row", "udr"],
        "Update dataset row",
        update_dataset_row,
        ArgumentsEnum.REQUIRED,
        [],
        update_dataset_row_options
    ),
    Command(
        "delete_dataset_row",
        ["delete-dataset-row", "ddr"],
        "Delete dataset row",
        delete_dataset_row,
        ArgumentsEnum.REQUIRED,
        [],
        delete_dataset_row_options
    ),
    Command(
        "create_dataset_row_expected_source",
        ["create-expected-source", "ces"],
        "Create dataset row expected source",
        create_dataset_row_expected_source,
        ArgumentsEnum.REQUIRED,
        [],
        create_dataset_row_expected_source_options
    ),
    Command(
        "list_dataset_row_expected_sources",
        ["list-expected-sources", "les"],
        "List dataset row expected sources",
        list_dataset_row_expected_sources,
        ArgumentsEnum.REQUIRED,
        [],
        list_dataset_row_expected_sources_options
    ),
    Command(
        "get_dataset_row_expected_source",
        ["get-expected-source", "ges"],
        "Get dataset row expected source",
        get_dataset_row_expected_source,
        ArgumentsEnum.REQUIRED,
        [],
        get_dataset_row_expected_source_options
    ),
    Command(
        "update_dataset_row_expected_source",
        ["update-expected-source", "ues"],
        "Update dataset row expected source",
        update_dataset_row_expected_source,
        ArgumentsEnum.REQUIRED,
        [],
        update_dataset_row_expected_source_options
    ),
    Command(
        "delete_dataset_row_expected_source",
        ["delete-expected-source", "des"],
        "Delete dataset row expected source",
        delete_dataset_row_expected_source,
        ArgumentsEnum.REQUIRED,
        [],
        delete_dataset_row_expected_source_options
    ),
    Command(
        "create_dataset_row_filter_variable",
        ["create-filter-variable", "cfv"],
        "Create dataset row filter variable",
        create_dataset_row_filter_variable,
        ArgumentsEnum.REQUIRED,
        [],
        create_dataset_row_filter_variable_options
    ),
    Command(
        "list_dataset_row_filter_variables",
        ["list-filter-variables", "lfv"],
        "List dataset row filter variables",
        list_dataset_row_filter_variables,
        ArgumentsEnum.REQUIRED,
        [],
        list_dataset_row_filter_variables_options
    ),
    Command(
        "get_dataset_row_filter_variable",
        ["get-filter-variable", "gfv"],
        "Get dataset row filter variable",
        get_dataset_row_filter_variable,
        ArgumentsEnum.REQUIRED,
        [],
        get_dataset_row_filter_variable_options
    ),
    Command(
        "update_dataset_row_filter_variable",
        ["update-filter-variable", "ufv"],
        "Update dataset row filter variable",
        update_dataset_row_filter_variable,
        ArgumentsEnum.REQUIRED,
        [],
        update_dataset_row_filter_variable_options
    ),
    Command(
        "delete_dataset_row_filter_variable",
        ["delete-filter-variable", "dfv"],
        "Delete dataset row filter variable",
        delete_dataset_row_filter_variable,
        ArgumentsEnum.REQUIRED,
        [],
        delete_dataset_row_filter_variable_options
    ),
    Command(
        "update_dataset_rows_file",
        ["upload-dataset-rows", "udrf"],
        "Upload dataset rows file",
        update_dataset_rows_file,
        ArgumentsEnum.REQUIRED,
        [],
        update_dataset_rows_file_options
    ),
    Command(
        "list_evaluation_plans",
        ["list-evaluation-plans", "lep"],
        "Retrieves a list of all evaluation plans.",
        list_evaluation_plans,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "create_evaluation_plan",
        ["create-evaluation-plan", "cep"],
        "Creates a new evaluation plan.",
        create_evaluation_plan,
        ArgumentsEnum.REQUIRED,
        [],
        create_evaluation_plan_options
    ),
    Command(
        "get_evaluation_plan",
        ["get-evaluation-plan", "gep"],
        "Retrieve evaluation plan by ID.",
        get_evaluation_plan,
        ArgumentsEnum.REQUIRED,
        [],
        get_evaluation_plan_options
    ),
    Command(
        "update_evaluation_plan",
        ["update-evaluation-plan", "uep"],
        "Update evaluation plan by ID.",
        update_evaluation_plan,
        ArgumentsEnum.REQUIRED,
        [],
        update_evaluation_plan_options
    ),
    Command(
        "delete_evaluation_plan",
        ["delete-evaluation-plan", "dep"],
        "Delete evaluation plan by ID.",
        delete_evaluation_plan,
        ArgumentsEnum.REQUIRED,
        [],
        delete_evaluation_plan_options
    ),
    Command(
        "list_evaluation_plan_system_metrics",
        ["list-evaluation-plan-system-metrics", "lepsm"],
        "List system metrics for evaluation plan by ID.",
        list_evaluation_plan_system_metrics,
        ArgumentsEnum.REQUIRED,
        [],
        list_evaluation_plan_system_metrics_options
    ),
    Command(
        "add_evaluation_plan_system_metric",
        ["add-evaluation-plan-system-metric", "aepsm"],
        "Adds a new system metric to an existing evaluation plan.",
        add_evaluation_plan_system_metric,
        ArgumentsEnum.REQUIRED,
        [],
        add_evaluation_plan_system_metric_options
    ),
    Command(
        "get_evaluation_plan_system_metric",
        ["get-evaluation-plan-system-metric", "gepsm"],
        "Retrieves a specific system metric from a given evaluation plan.",
        get_evaluation_plan_system_metric,
        ArgumentsEnum.REQUIRED,
        [],
        get_evaluation_plan_system_metric_options
    ),
    Command(
        "update_evaluation_plan_system_metric",
        ["update-evaluation-plan-system-metric", "uepsm"],
        "Updates a specific system metric within an existing evaluation plan.",
        update_evaluation_plan_system_metric,
        ArgumentsEnum.REQUIRED,
        [],
        update_evaluation_plan_system_metric_options
    ),
    Command(
        "delete_evaluation_plan_system_metric",
        ["delete-evaluation-plan-system-metric", "depsm"],
        "Delete a specific system metric within an existing evaluation plan.",
        delete_evaluation_plan_system_metric,
        ArgumentsEnum.REQUIRED,
        [],
        delete_evaluation_plan_system_metric_options
    ),
    Command(
        "list_system_metrics",
        ["list-available-system-metrics", "lsm"],
        "Retrieves a list of all available system metrics that can be used in evaluation plans",
        list_system_metrics,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "get_system_metric",
        ["get-system-metrics", "gsm"],
        "Retrieves a specific system metric using its ID.",
        get_system_metric,
        ArgumentsEnum.REQUIRED,
        [],
        get_system_metric_options
    ),
    Command(
        "execute_evaluation_plan",
        ["execute-evaluation-plan", "xep"],
        "Initiates the execution of a previously defined evaluation plan. The evaluation plan's configuration "
        "(assistant, dataset, metrics, and weights) determines how the assessment is performed.",
        execute_evaluation_plan,
        ArgumentsEnum.REQUIRED,
        [],
        execute_evaluation_plan_options
    ),
    Command(
        "list_evaluation_results",
        ["list-evaluation-results", "ler"],
        "Retrieves a list of evaluation results associated with a specific evaluation plan.",
        list_evaluation_results,
        ArgumentsEnum.REQUIRED,
        [],
        list_evaluation_results_options
    ),
    Command(
        "get_evaluation_result",
        ["get-evaluation-result", "ger"],
        "Retrieves a specific evaluation result by its ID.",
        get_evaluation_result,
        ArgumentsEnum.REQUIRED,
        [],
        get_evaluation_result_options
    ),
]
