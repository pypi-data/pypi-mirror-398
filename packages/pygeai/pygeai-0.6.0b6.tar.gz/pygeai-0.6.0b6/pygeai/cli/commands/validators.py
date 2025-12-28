from pathlib import Path

from pygeai.core.common.exceptions import WrongArgumentError


def validate_dataset_file(dataset_file: str):
    path = Path(dataset_file)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")
    if not path.is_file():
        raise ValueError(f"Dataset path is not a file: {dataset_file}")


def validate_row_structure(row: dict):
    required_fields = ["dataSetRowExpectedAnswer", "dataSetRowContextDocument", "dataSetRowInput"]
    for field in required_fields:
        if not isinstance(row.get(field), str):
            raise WrongArgumentError(f'Missing or invalid value for required field "{field}". It must be a non-empty string.')

    expected_sources = row.get("expectedSources", [])
    if not isinstance(expected_sources, list):
        raise WrongArgumentError('"expectedSources" must be a list of objects, even if empty.')
    for source in expected_sources:
        if not isinstance(source, dict) or not all(
                key in source and isinstance(source[key], str) for key in [
                    "dataSetExpectedSourceId", "dataSetExpectedSourceName",
                    "dataSetExpectedSourceValue", "dataSetExpectedSourceExtension"
                ]
        ):
            raise WrongArgumentError(
                'Each item in "expectedSources" must be a dictionary containing the following string fields: '
                '"dataSetExpectedSourceId", "dataSetExpectedSourceName", "dataSetExpectedSourceValue", and "dataSetExpectedSourceExtension".'
            )

    filter_variables = row.get("filterVariables", [])
    if not isinstance(filter_variables, list):
        raise WrongArgumentError('"filterVariables" must be a list of objects, even if empty.')
    for variable in filter_variables:
        if not isinstance(variable, dict) or not all(
                key in variable and isinstance(variable[key], str) for key in [
                    "dataSetMetadataType", "dataSetRowFilterKey",
                    "dataSetRowFilterOperator", "dataSetRowFilterValue", "dataSetRowFilterVarId"
                ]
        ):
            raise WrongArgumentError(
                'Each item in "filterVariables" must be a dictionary containing the following string fields: '
                '"dataSetMetadataType", "dataSetRowFilterKey", "dataSetRowFilterOperator", '
                '"dataSetRowFilterValue", and "dataSetRowFilterVarId".'
            )


def validate_system_metric(metric: dict):
    required_fields = ["systemMetricId", "systemMetricWeight"]

    if not isinstance(metric, dict):
        raise WrongArgumentError("Each system metric must be a dictionary.")

    for field in required_fields:
        if field not in metric:
            raise WrongArgumentError(f'Missing required field "{field}" in system metric.')

    if not isinstance(metric["systemMetricId"], str) or not metric["systemMetricId"].strip():
        raise WrongArgumentError('"systemMetricId" must be a non-empty string.')

    if not isinstance(metric["systemMetricWeight"], (int, float)) or not (0 <= metric["systemMetricWeight"] <= 1):
        raise WrongArgumentError('"systemMetricWeight" must be a number between 0 and 1 (inclusive).')
