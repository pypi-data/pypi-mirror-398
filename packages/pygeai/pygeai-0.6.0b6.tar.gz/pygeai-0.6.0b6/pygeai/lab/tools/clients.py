import json
from json import JSONDecodeError

from pygeai import logger
from pygeai.core.common.exceptions import InvalidAPIResponseException, MissingRequirementException, APIResponseError
from pygeai.lab.constants import VALID_SCOPES, VALID_ACCESS_SCOPES, VALID_REPORT_EVENTS
from pygeai.lab.tools.endpoints import CREATE_TOOL_V2, LIST_TOOLS_V2, GET_TOOL_V2, UPDATE_TOOL_V2, UPSERT_TOOL_V2, \
    PUBLISH_TOOL_REVISION_V2, GET_PARAMETER_V2, SET_PARAMETER_V2, DELETE_TOOL_V2, EXPORT_TOOL_V2
from pygeai.lab.clients import AILabClient


class ToolClient(AILabClient):

    def create_tool(
            self,
            name: str,
            description: str = None,
            scope: str = None,
            access_scope: str = "private",
            public_name: str = None,
            icon: str = None,
            open_api: str = None,
            open_api_json: dict = None,
            report_events: str = "None",
            parameters: list = None,
            automatic_publish: bool = False
    ) -> dict:
        """
        Creates a new tool in the specified project.

        :param name: str - Name of the tool. Must be non-empty, unique within the project, and exclude ':' or '/'.
        :param description: str - Description of the tool's purpose, helping agents decide when to use it. Optional.
        :param scope: str - Scope of the tool, either 'builtin', 'external', or 'api'. Optional.
        :param access_scope: str - Access scope of the tool, either 'public' or 'private'. Defaults to 'private'.
        :param public_name: str - Public name of the tool, required if access_scope is 'public'. Must be unique within the installation and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores. Optional if access_scope is 'private'.
        :param icon: str - URL for the tool's icon or avatar image. Optional.
        :param open_api: str - URL where the OpenAPI specification can be loaded. Required for 'api' scope tools if open_api_json is not provided. Optional otherwise.
        :param open_api_json: dict - OpenAPI specification as a dictionary. Required for 'api' scope tools if open_api is not provided. Serialized to a JSON string in the request. Optional otherwise.
        :param report_events: str - Event reporting mode for tool progress feedback, one of 'None', 'All', 'Start', 'Finish', 'Progress'. Defaults to 'None'.
        :param parameters: list - List of parameter dictionaries defining tool inputs and configurations. Optional for 'api' scope tools (as parameters are in OpenAPI spec), required otherwise if parameters are needed. Each dictionary includes:
            - key: str (unique identifier, case-sensitive, must match OpenAPI for 'api' tools)
            - description: str (explains parameter usage)
            - isRequired: bool (whether parameter is mandatory)
            - type: str (one of 'config', 'app', 'context'; defaults to 'app')
            - value: str (for 'config' type, the static value; for 'context' type, the context variable like 'USER_EMAIL')
            - fromSecret: bool (for 'config' type, indicates if value is a secret name). Example:
            [
                {
                    'key': 'api_key',
                    'description': 'API key for service',
                    'isRequired': True,
                    'type': 'config',
                    'value': 'my-secret-key',
                    'fromSecret': True
                },
                {
                    'key': 'query',
                    'description': 'Search query',
                    'isRequired': False,
                    'type': 'app'
                }
            ]
        :param automatic_publish: bool - If True, automatically publishes the tool after creation. Defaults to False.
        :return: dict - JSON response containing the created tool details if successful, otherwise the raw response text.
        :raises JSONDecodeError: If the response cannot be parsed as JSON.
        """
        if scope is not None and scope not in VALID_SCOPES:
            raise ValueError(f"Scope must be one of {', '.join(VALID_SCOPES)}.")
        if access_scope is not None and access_scope not in VALID_ACCESS_SCOPES:
            raise ValueError(f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")
        if report_events is not None and report_events not in VALID_REPORT_EVENTS:
            raise ValueError(f"Report events must be one of {', '.join(VALID_REPORT_EVENTS)}.")

        data = {
            "tool": {
                "reportEvents": report_events,
            }
        }
        if name:
            data["tool"]["name"] = name
        if description:
            data["tool"]["description"] = description
        if scope:
            data["tool"]["scope"] = scope
        if access_scope:
            data["tool"]["accessScope"] = access_scope
        if public_name:
            data["tool"]["publicName"] = public_name
        if icon:
            data["tool"]["icon"] = icon
        if open_api:
            data["tool"]["openApi"] = open_api
        if open_api_json:
            open_api_str = json.dumps(open_api_json, indent=2)
            data["tool"]["openApiJson"] = open_api_str
        if parameters:
            data["tool"]["parameters"] = parameters

        logger.debug(f"Creating new tool with data: {data}")

        endpoint = CREATE_TOOL_V2
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create tool for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create tool for project {self.project_id}: {response.text}")

        return result

    def list_tools(
            self,
            id: str = "",
            count: str = "100",
            access_scope: str = "public",
            allow_drafts: bool = True,
            scope: str = "api",
            allow_external: bool = True
    ) -> dict | str:
        """
        Retrieves a list of tools associated with the specified project.

        :param id: str - ID of the tool to filter by. Defaults to "" (no filtering).
        :param count: str - Number of tools to retrieve. Defaults to "100".
        :param access_scope: str - Access scope of the tools, either "public" or "private". Defaults to "public".
        :param allow_drafts: bool - Whether to include draft tools. Defaults to True.
        :param scope: str - Scope of the tools, must be "builtin", "external", or "api". Defaults to "api".
        :param allow_external: bool - Whether to include external tools. Defaults to True.
        :return: dict or str - JSON response containing the list of tools if successful, otherwise the raw response text.
        """
        endpoint = LIST_TOOLS_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if scope and scope not in VALID_SCOPES:
            raise ValueError(f"Scope must be one of {', '.join(VALID_SCOPES)}.")

        logger.debug(f"Listing tools available for the project with ID: {self.project_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={
                "id": id,
                "count": count,
                "accessScope": access_scope,
                "allowDrafts": allow_drafts,
                "scope": scope,
                "allowExternal": allow_external
            }
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list tools for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list tools for project {self.project_id}: {response.text}")

        return result

    def get_tool(
            self,
            tool_id: str,
            revision: str = 0,
            version: int = 0,
            allow_drafts: bool = True
    ):
        """
        Retrieves details of a specific tool from the specified project.

        :param tool_id: str - Unique identifier of the tool to retrieve.
        :param revision: str - Revision of the tool to retrieve. Defaults to 0 (latest revision).
        :param version: int - Version of the tool to retrieve. Defaults to 0 (latest version).
        :param allow_drafts: bool - Whether to include draft tool in the retrieval. Defaults to True.
        :return: dict or str - JSON response containing the tool details if successful, otherwise the raw response text.
        """
        endpoint = GET_TOOL_V2.format(toolId=tool_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Retrieving detail of tool with ID: {tool_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={
                "revision": revision,
                "version": version,
                "allowDrafts": allow_drafts,
            }
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve tool {tool_id} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve tool {tool_id} for project {self.project_id}: {response.text}")

        return result

    def delete_tool(
            self,
            tool_id: str = None,
            tool_name: str = None
    ) -> dict | str:
        """
        Deletes a specific tool from the specified project.

        :param tool_id: str, optional - Unique identifier of the tool to delete. Defaults to None.
        :param tool_name: str, optional - Name of the tool to delete. Defaults to None.
        :return: dict or str - JSON response containing the result of the delete operation if successful,
            otherwise the raw response text.
        :raises ValueError: If neither tool_id nor tool_name is provided.
        """
        if not (tool_id or tool_name):
            raise ValueError("Either tool_id or tool_name must be provided.")

        endpoint = DELETE_TOOL_V2.format(toolId=tool_id if tool_id else tool_name)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if tool_id:
            logger.debug(f"Deleting tool with ID {tool_id}")
        else:
            logger.debug(f"Deleting tool with name '{tool_name}'")

        response = self.api_service.delete(
            endpoint=endpoint,
            headers=headers
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")

        if response.status_code != 204:
            logger.error(f"Unable to delete tool {tool_id or tool_name} in project {self.project_id}: JSON parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete tool {tool_id or tool_name} in project {self.project_id}: {response.text}")
        else:
            return {}

    def update_tool(
            self,
            tool_id: str = None,
            name: str = None,
            description: str = None,
            scope: str = None,
            access_scope: str = None,
            public_name: str = None,
            icon: str = None,
            open_api: str = None,
            open_api_json: dict = None,
            report_events: str = "None",
            parameters: list = None,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> dict | str:
        """
        Updates an existing tool in the specified project or upserts it if specified.

        :param tool_id: str - Unique identifier of the tool to update. Required for update operations.
        :param name: str - Updated name of the tool. Must be non-empty, unique within the project, and exclude ':' or '/' if provided. Optional.
        :param description: str - Updated description of the tool's purpose, helping agents decide when to use it. Optional.
        :param scope: str - Updated scope of the tool, one of 'builtin', 'external', or 'api'. Optional.
        :param access_scope: str - Updated access scope of the tool, either 'public' or 'private'. Optional.
        :param public_name: str - Updated public name of the tool, required if access_scope is set to 'public'. Must be unique within the installation and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores. Optional otherwise.
        :param icon: str - Updated URL for the tool's icon or avatar image. Optional.
        :param open_api: str - Updated URL where the OpenAPI specification can be loaded. Required for 'api' scope tools if open_api_json is not provided during upsert or if scope is changed to 'api'. Optional otherwise.
        :param open_api_json: dict - Updated OpenAPI specification as a dictionary. Required for 'api' scope tools if open_api is not provided during upsert or if scope is changed to 'api'. Serialized to a JSON string in the request. Optional otherwise.
        :param report_events: str - Updated event reporting mode for tool progress feedback, one of 'None', 'All', 'Start', 'Finish', 'Progress'. Optional.
        :param parameters: list - Updated list of parameter dictionaries defining tool inputs and configurations. Optional for 'api' scope tools (as parameters are in OpenAPI spec). Each dictionary includes:
            - key: str (unique identifier, case-sensitive, must match OpenAPI for 'api' tools)
            - description: str (explains parameter usage)
            - isRequired: bool (whether parameter is mandatory)
            - type: str (one of 'config', 'app', 'context'; defaults to 'app')
            - value: str (for 'config' type, the static value; for 'context' type, the context variable like 'USER_EMAIL')
            - fromSecret: bool (for 'config' type, indicates if value is a secret name). Example:
            [
                {
                    'key': 'api_key',
                    'description': 'API key for service',
                    'isRequired': True,
                    'type': 'config',
                    'value': 'my-secret-key',
                    'fromSecret': True
                },
                {
                    'key': 'query',
                    'description': 'Search query',
                    'isRequired': False,
                    'type': 'app'
                }
            ]
        :param automatic_publish: bool - If True, automatically publishes the tool after updating. Defaults to False.
        :param upsert: bool - If True, creates the tool if it does not exist (upsert); otherwise, only updates an existing tool. Defaults to False.
        :return: dict or str - JSON response containing the updated or created tool details if successful, otherwise the raw response text.
        :raises ValueError: If scope is provided and not one of 'builtin', 'external', or 'api', or if access_scope is provided and not one of 'public' or 'private', or if report_events is provided and not one of 'None', 'All', 'Start', 'Finish', 'Progress'.
        :raises JSONDecodeError: Caught internally if the response cannot be parsed as JSON; returns raw response text.
        :raises Exception: May be raised by `api_service.put` for network issues, authentication errors, or server-side problems (not caught here).
        """
        if not (tool_id or name):
            raise ValueError(f"Either tool ID or tool Name must be defined in order to update tool.")
        if scope and scope not in VALID_SCOPES:
            raise ValueError(f"Scope must be one of {', '.join(VALID_SCOPES)}.")
        if access_scope and access_scope not in VALID_ACCESS_SCOPES:
            raise ValueError(f"Access scope must be one of {', '.join(VALID_ACCESS_SCOPES)}.")
        if report_events and report_events not in VALID_REPORT_EVENTS:
            raise ValueError(f"Report events must be one of {', '.join(VALID_REPORT_EVENTS)}.")

        data = {
            "tool": {
                "reportEvents": report_events,
            }
        }
        if name:
            data["tool"]["name"] = name
        if description:
            data["tool"]["description"] = description
        if scope:
            data["tool"]["scope"] = scope
        if access_scope:
            data["tool"]["accessScope"] = access_scope
        if public_name:
            data["tool"]["publicName"] = public_name
        if icon:
            data["tool"]["icon"] = icon
        if open_api:
            data["tool"]["openApi"] = open_api
        if open_api_json:
            open_api_str = json.dumps(open_api_json, indent=2)
            data["tool"]["openApiJson"] = open_api_str
        if parameters:
            data["tool"]["parameters"] = parameters

        logger.debug(f"Updating tool with ID {tool_id} with data: {data}")

        endpoint = UPSERT_TOOL_V2 if upsert else UPDATE_TOOL_V2
        endpoint = endpoint.format(toolId=tool_id) if tool_id else endpoint.format(toolId=name)

        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        response = self.api_service.put(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to update tool {tool_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update tool {tool_id} in project {self.project_id}: {response.text}")

        return result

    def publish_tool_revision(
            self,
            tool_id: str,
            revision: str
    ):
        """
        Publishes a specific revision of a tool in the specified project.

        :param tool_id: str - Unique identifier of the tool to publish.
        :param revision: str - Revision of the tool to publish.
        :return: dict or str - JSON response containing the result of the publish operation if successful, otherwise the raw response text.
        """
        endpoint = PUBLISH_TOOL_REVISION_V2.format(toolId=tool_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Publishing revision {revision} for tool with ID {tool_id}")

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data={
                "revision": revision,
            }
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to publish revision {revision} for tool {tool_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to publish revision {revision} for tool {tool_id} in project {self.project_id}: {response.text}")

        return result

    def get_parameter(
            self,
            tool_id: str = None,
            tool_public_name: str = None,
            revision: str = 0,
            version: int = 0,
            allow_drafts: bool = True
    ):
        """
        Retrieves details of parameters for a specific tool identified by either its ID or public name in the specified project.

        :param tool_id: str, optional - Unique identifier of the tool whose parameters are to be retrieved. Defaults to None.
        :param tool_public_name: str, optional - Public name of the tool whose parameters are to be retrieved. Defaults to None.
        :param revision: str - Revision of the parameters to retrieve. Defaults to "0" (latest revision).
        :param version: int - Version of the parameters to retrieve. Defaults to 0 (latest version).
        :param allow_drafts: bool - Whether to include draft parameters in the retrieval. Defaults to True.
        :return: dict or str - JSON response containing the parameter details if successful, otherwise the raw response text.
        :raises ValueError: If neither tool_id nor tool_public_name is provided.
        """
        if not (tool_id or tool_public_name):
            raise ValueError("Either tool_id or tool_public_name must be provided.")

        if tool_id:
            logger.debug(f"Retrieving parameter for tool with ID {tool_id}")
        else:
            logger.debug(f"Retrieving parameter for tool with name '{tool_public_name}'")

        endpoint = GET_PARAMETER_V2.format(toolPublicName=tool_public_name) if tool_public_name else GET_PARAMETER_V2.format(toolPublicName=tool_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params={
                "revision": revision,
                "version": version,
                "allowDrafts": allow_drafts,
            }
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve parameters for tool {tool_id or tool_public_name} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve parameters for tool {tool_id or tool_public_name} in project {self.project_id}: {response.text}")

        return result

    def set_parameter(
            self,
            tool_id: str = None,
            tool_public_name: str = None,
            parameters: list = None
    ):
        """
        Sets or updates parameters for a specific tool identified by either its ID or public name in the specified project.

        :param tool_id: str, optional - Unique identifier of the tool whose parameters are to be set. Defaults to None.
        :param tool_public_name: str, optional - Public name of the tool whose parameters are to be set. Defaults to None.
        :param parameters: list - List of parameter dictionaries defining the tool's parameters.
                                 Each dictionary must contain 'key', 'dataType', 'description', and 'isRequired'.
                                 For config parameters, include 'type', 'fromSecret', and 'value'. Defaults to None.
        :return: dict or str - JSON response containing the result of the set operation if successful, otherwise the raw response text.
        :raises ValueError: If neither tool_id nor tool_public_name is provided, or if parameters is None or empty.
        """
        if not (tool_id or tool_public_name):
            raise ValueError("Either tool_id or tool_public_name must be provided.")
        if not parameters:
            raise ValueError("Parameters list must be provided and non-empty.")

        endpoint = SET_PARAMETER_V2.format(toolPublicName=tool_public_name) if tool_public_name else SET_PARAMETER_V2.format(toolPublicName=tool_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "parameterDefinition": {
                "parameters": parameters
            }
        }

        if tool_id:
            logger.debug(f"Setting parameter for tool with ID {tool_id} with data: {data}")
        else:
            logger.debug(f"Setting parameter for tool with name '{tool_public_name}' with data: {data}")

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        if response.status_code != 204:
            logger.error(f"Unable to set parameters for tool {tool_id or tool_public_name} in project {self.project_id}: JSON parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to set parameters for tool {tool_id or tool_public_name} in project {self.project_id}: {response.text}")
        else:
            return {}

    def export_tool(
            self,
            tool_id: str,
    ) -> dict:
        """
        Retrieves details of a specific tool from the specified project.

        :param tool_id: str - Unique identifier of the tool to retrieve.
        :return: dict - JSON response containing the tool details.
        :raises InvalidAPIResponseException: If the response cannot be parsed as JSON or an error occurs.
        :raises MissingRequirementException: If project_id or tool_id is not provided.
        """

        if not tool_id:
            raise MissingRequirementException("tool_id must be specified in order to retrieve the tool")

        endpoint = EXPORT_TOOL_V2.format(toolId=tool_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Exporting tool with ID {tool_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
        )
        if response.status_code >= 300:
            logger.error(f"Invalid status code returned from the API endpoint: {response.text}")
            raise APIResponseError(f"API returned an error: {response.text}")
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to export tool {tool_id} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to export tool {tool_id} for project {self.project_id}: {response.text}")

        return result