import json
from pathlib import Path

from pygeai.evaluation.clients import EvaluationClient
from pygeai.evaluation.dataset.endpoints import (
    LIST_DATASETS, CREATE_DATASET, UPLOAD_DATASET_FILE, GET_DATASET, UPDATE_DATASET, DELETE_DATASET,
    CREATE_DATASET_ROW, LIST_DATASET_ROWS, GET_DATASET_ROW, UPDATE_DATASET_ROW, DELETE_DATASET_ROW,
    CREATE_EXPECTED_SOURCE, LIST_EXPECTED_SOURCES, GET_EXPECTED_SOURCE, UPDATE_EXPECTED_SOURCE, DELETE_EXPECTED_SOURCE,
    CREATE_FILTER_VARIABLE, LIST_FILTER_VARIABLES, GET_FILTER_VARIABLE, UPDATE_FILTER_VARIABLE, DELETE_FILTER_VARIABLE,
    UPLOAD_DATASET_ROWS_FILE
)


class EvaluationDatasetClient(EvaluationClient):

    def list_datasets(self) -> dict:
        """
        Lists all datasets.

        :return: dict - API response containing a list of datasets.
        """
        response = self.api_service.get(
            endpoint=LIST_DATASETS
        )
        result = response.json()
        return result

    def create_dataset(
            self,
            dataset_name: str,
            dataset_description: str,
            dataset_type: str,
            dataset_active: bool = True,
            rows: list = None,
    ) -> dict:
        """
        Creates a new dataset with the specified details.

        :param dataset_name: The name of the dataset.
        :param dataset_description: A description of the dataset.
        :param dataset_type: The type of the dataset.
        :param dataset_active: Whether the dataset is active (default: True).
        :param rows: A list of dataset rows (optional).

        :return: The API response containing the created dataset details.
        """
        data = {
            "dataSetName": dataset_name,
            "dataSetDescription": dataset_description,
            "dataSetType": dataset_type,
            "dataSetActive": dataset_active,
            "rows": rows
        }

        response = self.api_service.post(
            endpoint=CREATE_DATASET,
            data=data
        )
        result = response.json()
        return result

    def create_dataset_from_file(self, file_path: str) -> dict:
        """
        Creates a new dataset from a JSON file.

        :param file_path: str - JSON File with data for the dataset upload.

        :return: dict - API response with the file upload result.
        """
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        headers = {
            "Content-Type": "application/json",
        }

        file = file_path.open("rb")
        try:
            response = self.api_service.post_file_binary(
                endpoint=UPLOAD_DATASET_FILE,
                headers=headers,
                file=file
            )
            result = response.json()
            return result
        finally:
            if file:
                file.close()

    def get_dataset(self, dataset_id: str) -> dict:
        """
        Retrieves a specific dataset.

        :param dataset_id: str - UUID representing the dataset to retrieve.

        :return: dict - The dataset metadata.
        """
        endpoint = GET_DATASET.format(dataSetId=dataset_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def update_dataset(
            self,
            dataset_id: str,
            dataset_name: str,
            dataset_description: str,
            dataset_type: str,
            dataset_active: bool = True,
            rows: list = None,
    ) -> dict:
        """
        Updates an existing dataset with the provided details.

        :param dataset_id: The unique identifier of the dataset to update.
        :param dataset_name: The new name of the dataset.
        :param dataset_description: A description of the dataset.
        :param dataset_type: The type of the dataset.
        :param dataset_active: Whether the dataset is active (default: True).
        :param rows: A list of dataset rows to update (optional).

        :return: The API response containing the updated dataset details.
        """
        data = dict()
        if dataset_name is not None:
            data["dataSetName"] = dataset_name
        if dataset_description is not None:
            data["dataSetDescription"] = dataset_description
        if dataset_type is not None:
            data["dataSetType"] = dataset_type
        if dataset_active is not None:
            data["dataSetActive"] = dataset_active
        if rows is not None and any(rows):
            data["rows"] = rows
        
        endpoint = UPDATE_DATASET.format(dataSetId=dataset_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        result = response.json()
        return result

    def delete_dataset(self, dataset_id: str) -> dict:
        """
        Deletes a dataset.

        :param dataset_id: str - The ID of the dataset.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_DATASET.format(dataSetId=dataset_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def create_dataset_row(self, dataset_id: str, row: dict) -> dict:
        """
        Creates a new row in a dataset.

        :param dataset_id: str - The ID of the dataset.
        :param row: dict - Row data for the new dataset.

        :return: dict - API response with the created dataset row.
        """
        endpoint = CREATE_DATASET_ROW.format(dataSetId=dataset_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data=row
        )
        result = response.json()
        return result

    def list_dataset_rows(self, dataset_id: str) -> dict:
        """
        Lists rows for a dataset.

        :param dataset_id: str - The ID of the dataset.

        :return: dict - List of dataset rows.
        """
        endpoint = LIST_DATASET_ROWS.format(dataSetId=dataset_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def get_dataset_row(self, dataset_id: str, dataset_row_id: str) -> dict:
        """
        Retrieves a specific dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.

        :return: dict - The dataset row metadata.
        """
        endpoint = GET_DATASET_ROW.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def update_dataset_row(self, dataset_id: str, dataset_row_id: str, row: dict) -> dict:
        """
        Updates a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param row: dict - Data to update the dataset row.

        :return: dict - API response with the updated dataset row.
        """
        endpoint = UPDATE_DATASET_ROW.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=row
        )
        result = response.json()
        return result

    def delete_dataset_row(self, dataset_id: str, dataset_row_id: str) -> dict:
        """
        Deletes a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_DATASET_ROW.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def create_expected_source(
            self,
            dataset_id: str,
            dataset_row_id: str,
            expected_source_name: str,
            expected_source_value: str,
            expected_source_extension: str
    ) -> dict:
        """
        Creates a new expected source for a specific dataset row.

        :param dataset_id: str - The unique identifier of the dataset.
        :param dataset_row_id: str - The unique identifier of the dataset row.
        :param expected_source_name: str - The name of the expected source.
        :param expected_source_value: str - The value associated with the expected source.
        :param expected_source_extension: str - The file extension or format of the expected source.

        :return: dict - API response containing the details of the created expected source.
        """
        data = {
            "dataSetExpectedSourceName": expected_source_name,
            "dataSetExpectedSourceValue": expected_source_value,
            "dataSetExpectedSourceExtension": expected_source_extension
        }
        endpoint = CREATE_EXPECTED_SOURCE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data=data
        )
        result = response.json()
        return result

    def list_expected_sources(self, dataset_id: str, dataset_row_id: str) -> dict:
        """
        Lists expected sources for a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.

        :return: dict - List of expected sources for the dataset row.
        """
        endpoint = LIST_EXPECTED_SOURCES.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def get_expected_source(self, dataset_id: str, dataset_row_id: str, expected_source_id: str) -> dict:
        """
        Retrieves a specific expected source.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param expected_source_id: str - The ID of the expected source.

        :return: dict - The expected source metadata.
        """
        endpoint = GET_EXPECTED_SOURCE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetExpectedSourceId=expected_source_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def update_expected_source(
            self,
            dataset_id: str,
            dataset_row_id: str,
            expected_source_id: str,
            expected_source_name: str,
            expected_source_value: str,
            expected_source_extension: str
    ) -> dict:
        """
        Updates an expected source for a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param expected_source_id: str - The ID of the expected source.
        :param expected_source_name: str - The updated name of the expected source.
        :param expected_source_value: str - The updated value of the expected source.
        :param expected_source_extension: str - The updated file extension of the expected source.

        :return: dict - API response with the updated expected source.
        """
        data = {
            "dataSetExpectedSourceName": expected_source_name,
            "dataSetExpectedSourceValue": expected_source_value,
            "dataSetExpectedSourceExtension": expected_source_extension
        }
        endpoint = UPDATE_EXPECTED_SOURCE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetExpectedSourceId=expected_source_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        result = response.json()
        return result

    def delete_expected_source(self, dataset_id: str, dataset_row_id: str, expected_source_id: str) -> dict:
        """
        Deletes an expected source.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param expected_source_id: str - The ID of the expected source.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_EXPECTED_SOURCE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetExpectedSourceId=expected_source_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def create_filter_variable(
            self,
            dataset_id: str,
            dataset_row_id: str,
            metadata_type: str,
            filter_variable_key: str,
            filter_variable_value: str,
            filter_variable_operator: str
    ) -> dict:
        """
        Creates a new filter variable for a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param metadata_type: str - The type of metadata (e.g., "V" for variable, "F" for flag).
        :param filter_variable_key: str - The key to filter by.
        :param filter_variable_value: str - The value to filter by.
        :param filter_variable_operator: str - The filter operation (e.g., "=", "!=", ">", "<", "contains").

        :return: dict - API response with the created filter variable.
        """
        data = {
            "dataSetMetadataType": metadata_type,
            "dataSetRowFilterKey": filter_variable_key,
            "dataSetRowFilterValue": filter_variable_value,
            "dataSetRowFilterOperator": filter_variable_operator
        }
        endpoint = CREATE_FILTER_VARIABLE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.post(
            endpoint=endpoint,
            data=data
        )
        result = response.json()
        return result

    def list_filter_variables(self, dataset_id: str, dataset_row_id: str) -> dict:
        """
        Lists filter variables for a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.

        :return: dict - List of filter variables.
        """
        endpoint = LIST_FILTER_VARIABLES.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def get_filter_variable(self, dataset_id: str, dataset_row_id: str, filter_variable_id: str) -> dict:
        """
        Retrieves a specific filter variable.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param filter_variable_id: str - The ID of the filter variable.

        :return: dict - The filter variable metadata.
        """
        endpoint = GET_FILTER_VARIABLE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetRowFilterVarId=filter_variable_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def update_filter_variable(
            self,
            dataset_id: str,
            dataset_row_id: str,
            filter_variable_id: str,
            metadata_type: str,
            filter_variable_key: str,
            filter_variable_value: str,
            filter_variable_operator: str
    ) -> dict:
        """
        Updates a filter variable for a dataset row.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param filter_variable_id: str - The ID of the filter variable.
        :param metadata_type: str - The type of metadata (e.g., "V" for variable, "F" for flag).
        :param filter_variable_key: str - The key to filter by.
        :param filter_variable_value: str - The value to filter by.
        :param filter_variable_operator: str - The filter operation (e.g., "=", "!=", ">", "<", "contains").

        :return: dict - API response with the updated filter variable.
        """
        data = {
            "dataSetMetadataType": metadata_type,
            "dataSetRowFilterKey": filter_variable_key,
            "dataSetRowFilterValue": filter_variable_value,
            "dataSetRowFilterOperator": filter_variable_operator
        }
        endpoint = UPDATE_FILTER_VARIABLE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetRowFilterVarId=filter_variable_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data=data
        )
        result = response.json()
        return result

    def delete_filter_variable(self, dataset_id: str, dataset_row_id: str, filter_variable_id: str) -> dict:
        """
        Deletes a filter variable.

        :param dataset_id: str - The ID of the dataset.
        :param dataset_row_id: str - The ID of the dataset row.
        :param filter_variable_id: str - The ID of the filter variable.

        :return: dict - Response indicating the success or failure of the deletion.
        """
        endpoint = DELETE_FILTER_VARIABLE.format(dataSetId=dataset_id, dataSetRowId=dataset_row_id, dataSetRowFilterVarId=filter_variable_id)
        response = self.api_service.delete(
            endpoint=endpoint
        )
        result = response.json()
        return result

    def upload_dataset_rows_file(self, dataset_id: str, file_path: str) -> dict:
        """
        Uploads multiple dataset rows via file upload.

        :param dataset_id: str - The ID of the dataset.
        :param file_path: dict - File path with data for the dataset rows upload.

        :return: dict - API response with the file upload result.
        """
        file_path = Path(file_path)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        headers = {
            "Content-Type": "application/json",
        }
        endpoint = UPLOAD_DATASET_ROWS_FILE.format(dataSetId=dataset_id)

        file = file_path.open("rb")
        try:
            response = self.api_service.post_file_binary(
                endpoint=endpoint,
                headers=headers,
                file=file
            )
            result = response.json()
            return result
        finally:
            if file:
                file.close()

