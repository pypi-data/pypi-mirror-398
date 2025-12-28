LIST_DATASETS = "dataSetApi/dataSets"  # GET -> Lists all datasets.
CREATE_DATASET = "dataSetApi/dataSet"  # POST -> Creates a new dataset.
UPLOAD_DATASET_FILE = "dataSetApi/dataSet/FileUpload"  # POST -> Uploads one complete dataset via file upload.
GET_DATASET = "dataSetApi/dataSet/{dataSetId}"  # GET -> Retrieves a specific dataset.
UPDATE_DATASET = "dataSetApi/dataSet/{dataSetId}"  # PUT -> Updates an existing dataset.
DELETE_DATASET = "dataSetApi/dataSet/{dataSetId}"  # DELETE -> Deletes a dataset.

CREATE_DATASET_ROW = "dataSetApi/dataSet/{dataSetId}/dataSetRow"  # POST -> Creates a new row in a dataset.
LIST_DATASET_ROWS = "dataSetApi/dataSet/{dataSetId}/dataSetRows"  # GET -> Lists rows for a dataset.
GET_DATASET_ROW = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}"  # GET -> Retrieves a specific dataset row.
UPDATE_DATASET_ROW = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}"  # PUT -> Updates a dataset row.
DELETE_DATASET_ROW = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}"  # DELETE -> Deletes a dataset row.

CREATE_EXPECTED_SOURCE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowExpectedSource"  # POST -> Creates a new expected source for a dataset row.
LIST_EXPECTED_SOURCES = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowExpectedSources"  # GET -> Lists expected sources for a dataset row.
GET_EXPECTED_SOURCE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowExpectedSource/{dataSetExpectedSourceId}"  # GET -> Retrieves a specific expected source.
UPDATE_EXPECTED_SOURCE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowExpectedSource/{dataSetExpectedSourceId}"  # PUT -> Updates an expected source.
DELETE_EXPECTED_SOURCE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowExpectedSource/{dataSetExpectedSourceId}"  # DELETE -> Deletes an expected source.

CREATE_FILTER_VARIABLE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowFilterVariable"  # POST -> Creates a new filter variable for a dataset row.
LIST_FILTER_VARIABLES = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowFilterVariables"  # GET -> Lists filter variables for a dataset row.
GET_FILTER_VARIABLE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowFilterVariable/{dataSetRowFilterVarId}"  # GET -> Retrieves a specific filter variable.
UPDATE_FILTER_VARIABLE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowFilterVariable/{dataSetRowFilterVarId}"  # PUT -> Updates a filter variable.
DELETE_FILTER_VARIABLE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/{dataSetRowId}/dataSetRowFilterVariable/{dataSetRowFilterVarId}"  # DELETE -> Deletes a filter variable.

UPLOAD_DATASET_ROWS_FILE = "dataSetApi/dataSet/{dataSetId}/dataSetRow/FileUpload"  # POST -> Uploads multiple dataset rows via file upload.
