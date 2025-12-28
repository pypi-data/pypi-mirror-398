from json import JSONDecodeError
from typing import List

from pygeai import logger
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.lab.processes.endpoints import CREATE_PROCESS_V2, UPDATE_PROCESS_V2, UPSERT_PROCESS_V2, GET_PROCESS_V2, \
    LIST_PROCESSES_V2, LIST_PROCESS_INSTANCES_V2, DELETE_PROCESS_V2, PUBLISH_PROCESS_REVISION_V2, CREATE_TASK_V2, \
    UPDATE_TASK_V2, UPSERT_TASK_V2, GET_TASK_V2, LIST_TASKS_V2, DELETE_TASK_V2, PUBLISH_TASK_REVISION_V2, \
    START_INSTANCE_V2, ABORT_INSTANCE_V2, GET_INSTANCE_V2, GET_INSTANCE_HISTORY_V2, GET_THREAD_INFORMATION_V2, \
    SEND_USER_SIGNAL_V2, CREATE_KB_V1, GET_KB_V1, LIST_KBS_V1, DELETE_KB_V1, LIST_JOBS_V1
from pygeai.lab.clients import AILabClient


class AgenticProcessClient(AILabClient):

    def create_process(
            self,
            key: str,
            name: str,
            description: str = None,
            kb: dict = None,
            agentic_activities: list = None,
            artifact_signals: list = None,
            user_signals: list = None,
            start_event: dict = None,
            end_event: dict = None,
            sequence_flows: list = None,
            variables: list = None,
            automatic_publish: bool = False
    ) -> dict:
        """
        Creates a new process in the specified project.

        :param key: str - Unique key for the process within the project.
        :param name: str - Name of the process.
        :param description: str, optional - Description of the process purpose.
        :param kb: dict, optional - Knowledge base configuration.
        :param agentic_activities: list, optional - List of agentic activity definitions.
        :param artifact_signals: list, optional - List of artifact signal definitions.
        :param user_signals: list, optional - List of user signal definitions.
        :param start_event: dict, optional - Start event definition.
        :param end_event: dict, optional - End event definition.
        :param sequence_flows: list, optional - List of sequence flow definitions.
        :param variables: list, optional - List of variables used in the process.
        :param automatic_publish: bool, optional - Publish the process after creation (default: False).
        :return: dict or str - Created process details or error message.
        :raises InvalidAPIResponseException: If an error occurs during creation.
        """
        endpoint = CREATE_PROCESS_V2
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "processDefinition": {
                "key": key,
                "name": name
            }
        }
        if description:
            data["processDefinition"]["description"] = description
        if kb:
            data["processDefinition"]["kb"] = kb
        if agentic_activities:
            data["processDefinition"]["agenticActivities"] = agentic_activities
        if artifact_signals:
            data["processDefinition"]["artifactSignals"] = artifact_signals
        if user_signals:
            data["processDefinition"]["userSignals"] = user_signals
        if start_event:
            data["processDefinition"]["startEvent"] = start_event
        if end_event:
            data["processDefinition"]["endEvent"] = end_event
        if sequence_flows:
            data["processDefinition"]["sequenceFlows"] = sequence_flows
        if variables:
            data["processDefinition"]["variables"] = variables

        logger.debug(f"Creating agentic process with data: {data}")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create process for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create process for project {self.project_id}: {response.text}")

        return result

    def update_process(
            self,
            process_id: str = None,
            name: str = None,
            key: str = None,
            description: str = None,
            kb: dict = None,
            agentic_activities: list = None,
            artifact_signals: list = None,
            user_signals: list = None,
            start_event: dict = None,
            end_event: dict = None,
            sequence_flows: list = None,
            variables: list = None,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> dict:
        """
        Updates an existing process or creates it if upsert is enabled.

        :param process_id: str, optional - Unique identifier of the process to update.
        :param name: str, optional - Name of the process to update or create.
        :param key: str, optional - Updated unique key for the process.
        :param description: str, optional - Updated description of the process.
        :param kb: dict, optional - Updated knowledge base configuration.
        :param agentic_activities: list, optional - Updated list of agentic activity definitions.
        :param artifact_signals: list, optional - Updated list of artifact signal definitions.
        :param user_signals: list, optional - Updated list of user signal definitions.
        :param start_event: dict, optional - Updated start event definition.
        :param end_event: dict, optional - Updated end event definition.
        :param sequence_flows: list, optional - Updated list of sequence flow definitions.
        :param variables: list, optional - Updated list of variables.
        :param automatic_publish: bool, optional - Publish the process after updating (default: False).
        :param upsert: bool, optional - Create the process if it does not exist (default: False).
        :return: dict or str - Updated or created process details or error message.
        :raises ValueError: If neither process_id nor name is provided.
        :raises InvalidAPIResponseException: If an error occurs during the update.
        """
        if not (process_id or name):
            raise ValueError("Either process_id or name must be provided.")

        identifier = process_id if process_id else name
        endpoint = UPSERT_PROCESS_V2 if upsert else UPDATE_PROCESS_V2
        endpoint = endpoint.format(processId=identifier)

        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "processDefinition": {}
        }
        if key is not None:
            data["processDefinition"]["key"] = key
        if name is not None:
            data["processDefinition"]["name"] = name
        if description is not None:
            data["processDefinition"]["description"] = description
        if kb is not None:
            data["processDefinition"]["kb"] = kb
        if agentic_activities is not None:
            data["processDefinition"]["agenticActivities"] = agentic_activities
        if artifact_signals is not None:
            data["processDefinition"]["artifactSignals"] = artifact_signals
        if user_signals is not None:
            data["processDefinition"]["userSignals"] = user_signals
        if start_event is not None:
            data["processDefinition"]["startEvent"] = start_event
        if end_event is not None:
            data["processDefinition"]["endEvent"] = end_event
        if sequence_flows is not None:
            data["processDefinition"]["sequenceFlows"] = sequence_flows
        if variables:
            data["processDefinition"]["variables"] = variables

        if kb is None and not upsert:
            current_process = self.get_process(process_id=process_id, process_name=name)
            if isinstance(current_process, dict) and "processDefinition" in current_process:
                kb = current_process["processDefinition"].get("kb")

        if agentic_activities is None and not upsert:
            current_process = self.get_process(process_id=process_id, process_name=name)
            if isinstance(current_process, dict) and "processDefinition" in current_process:
                agentic_activities = current_process["processDefinition"].get("agenticActivities")
        if agentic_activities is not None:
            data["processDefinition"]["agenticActivities"] = agentic_activities

        if process_id:
            logger.debug(f"Updating agentic process with ID {process_id} with data: {data}")
        else:
            logger.debug(f"Updating agentic process with name{name} with data: {data}")

        response = self.api_service.put(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to update process {process_id or name} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update process {process_id or name} in project {self.project_id}: {response.text}")

        return result

    def get_process(
            self,
            process_id: str = None,
            process_name: str = None,
            revision: str = "0",
            version: int = 0,
            allow_drafts: bool = True
    ) -> dict:
        """
        Retrieves details of a specific process by its ID or name.

        :param process_id: str, optional - Unique identifier of the process.
        :param process_name: str, optional - Name of the process.
        :param revision: str, optional - Revision of the process (default: '0').
        :param version: int, optional - Version of the process (default: 0).
        :param allow_drafts: bool, optional - Include draft processes (default: True).
        :return: dict or str - Process details or error message.
        :raises ValueError: If neither process_id nor process_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not (process_id or process_name):
            raise ValueError("Either process_id or process_name must be provided.")

        identifier = process_id if process_id else process_name
        endpoint = GET_PROCESS_V2.format(processId=identifier)

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "revision": revision,
            "version": version,
            "allowDrafts": allow_drafts
        }

        if process_id:
            logger.debug(f"Retrieving agentic process detail with ID {process_id}")
        else:
            logger.debug(f"Retrieving agentic process detail with name '{process_name}'")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve process {process_id or process_name} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve process {process_id or process_name} for project {self.project_id}: {response.text}")

        return result

    def list_processes(
            self,
            id: str = None,
            name: str = None,
            status: str = None,
            start: str = "0",
            count: str = "100",
            allow_draft: bool = True
    ) -> dict:
        """
        Retrieves a list of processes in the specified project.

        :param id: str, optional - ID of the process to filter by.
        :param name: str, optional - Name of the process to filter by.
        :param status: str, optional - Status of the processes (e.g., 'active', 'inactive').
        :param start: str, optional - Starting index for pagination (default: '0').
        :param count: str, optional - Number of processes to retrieve (default: '100').
        :param allow_draft: bool, optional - Include draft processes (default: True).
        :return: dict or str - List of processes or error message.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        endpoint = LIST_PROCESSES_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "start": start,
            "count": count,
            "allowDraft": allow_draft
        }
        if id:
            params["id"] = id
        if name:
            params["name"] = name
        if status:
            params["status"] = status

        logger.debug(f"Listing agentic processes for project with ID {self.project_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list processes for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list processes for project {self.project_id}: {response.text}")

        return result

    def list_process_instances(
            self,
            process_id: str,
            is_active: bool = True,
            start: str = "0",
            count: str = "10"
    ) -> dict:
        """
        Retrieves a list of process instances for a specific process.

        :param process_id: str - Unique identifier of the process.
        :param is_active: bool, optional - List only active instances (default: True).
        :param start: str, optional - Starting index for pagination (default: '0').
        :param count: str, optional - Number of instances to retrieve (default: '10').
        :return: dict or str - List of process instances or error message.
        :raises ValueError: If process_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not process_id:
            raise ValueError("Process ID must be provided.")

        endpoint = LIST_PROCESS_INSTANCES_V2.format(processId=process_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "isActive": is_active,
            "start": start,
            "count": count
        }

        logger.debug(f"Listing instances for agentic process with ID {process_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list process instances for process {process_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list process instances for process {process_id} in project {self.project_id}: {response.text}")

        return result

    def delete_process(
            self,
            process_id: str = None,
            process_name: str = None
    ) -> dict:
        """
        Deletes a specific process by its ID or name.

        :param process_id: str, optional - Unique identifier of the process.
        :param process_name: str, optional - Name of the process.
        :return: dict or str - Confirmation of deletion or error message.
        :raises ValueError: If neither process_id nor process_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during deletion.
        """
        if not (process_id or process_name):
            raise ValueError("Either process_id or process_name must be provided.")

        identifier = process_id if process_id else process_name
        endpoint = DELETE_PROCESS_V2.format(processId=identifier)

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Deleting agentic process with ID {process_id}")

        response = self.api_service.delete(
            endpoint=endpoint,
            headers=headers
        )

        if response.status_code != 204:
            logger.error(f"Unable to delete process {process_id or process_name} from project {self.project_id}: JSON parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete process {process_id or process_name} from project {self.project_id}: {response.text}")
        else:
            return {}

    def publish_process_revision(
            self,
            process_id: str = None,
            process_name: str = None,
            revision: str = None
    ) -> dict:
        """
        Publishes a specific revision of a process.

        :param process_id: str, optional - Unique identifier of the process.
        :param process_name: str, optional - Name of the process.
        :param revision: str, optional - Revision of the process to publish.
        :return: dict or str - Result of the publish operation or error message.
        :raises ValueError: If neither process_id nor process_name is provided, or if revision is not specified.
        :raises InvalidAPIResponseException: If an error occurs during publishing.
        """
        if not (process_id or process_name):
            raise ValueError("Either process_id or process_name must be provided.")
        if not revision:
            raise ValueError("Revision must be provided.")

        identifier = process_id if process_id else process_name
        endpoint = PUBLISH_PROCESS_REVISION_V2.format(processId=identifier)

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if process_id:
            logger.debug(f"Publishing revision {revision} for agentic process with ID {process_id}")
        else:
            logger.debug(f"Publishing revision {revision} for agentic process with name '{process_name}'")

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data={
                "revision": revision
            }
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to publish revision {revision} for process {process_id or process_name} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to publish revision {revision} for process {process_id or process_name} in project {self.project_id}: {response.text}")

        return result

    def create_task(
            self,
            name: str,
            description: str = None,
            title_template: str = None,
            id: str = None,
            prompt_data: dict = None,
            artifact_types: List[dict] = None,
            automatic_publish: bool = False
    ) -> dict:
        """
        Creates a new task in the specified project.

        :param name: str - Name of the task, unique within the project, excluding ':' or '/'.
        :param description: str, optional - Description of the task purpose.
        :param title_template: str, optional - Template for task instance names (e.g., 'specs for {{issue}}').
        :param id: str, optional - Custom identifier for the task.
        :param prompt_data: dict, optional - Prompt configuration for task execution.
        :param artifact_types: List[dict], optional - List of artifact types with 'name', 'description', 'isRequired', 'usageType', and 'artifactVariableKey'.
        :param automatic_publish: bool, optional - Publish the task after creation (default: False).
        :return: dict or str - Created task details or error message.
        :raises InvalidAPIResponseException: If an error occurs during creation.
        """
        endpoint = CREATE_TASK_V2
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "taskDefinition": {
                "name": name
            }
        }
        if id:
            data["taskDefinition"]["id"] = id
        if description:
            data["taskDefinition"]["description"] = description
        if title_template:
            data["taskDefinition"]["titleTemplate"] = title_template
        if prompt_data:
            data["taskDefinition"]["promptData"] = prompt_data
        if artifact_types:
            data["taskDefinition"]["artifactTypes"] = artifact_types

        logger.debug(f"Creating task with data: {data}")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create task for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create task for project {self.project_id}: {response.text}")

    def get_task(
            self,
            task_id: str,
            task_name: str = None
    ) -> dict:
        """
        Retrieves details of a specific task by its ID or name.

        :param task_id: str, optional - Unique identifier of the task.
        :param task_name: str, optional - Name of the task.
        :return: dict or str - Task details or error message.
        :raises ValueError: If neither task_id nor task_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not (task_id or task_name):
            raise ValueError("Either task_id or task_name must be provided.")

        identifier = task_id if task_id else task_name
        endpoint = GET_TASK_V2.format(taskId=identifier)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if task_id:
            logger.debug(f"Retrieving task detail with ID {task_id}")
        else:
            logger.debug(f"Retrieving task detail with name {task_name}")

        response = self.api_service.get(endpoint=endpoint, headers=headers)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve task {task_id or task_name} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve task {task_id or task_name} for project {self.project_id}: {response.text}")

    def list_tasks(
            self,
            id: str = None,
            start: str = "0",
            count: str = "100",
            allow_drafts: bool = True
    ) -> dict:
        """
        Retrieves a list of tasks in the specified project.

        :param id: str, optional - ID of the task to filter by.
        :param start: str, optional - Starting index for pagination (default: '0').
        :param count: str, optional - Number of tasks to retrieve (default: '100').
        :param allow_drafts: bool, optional - Include draft tasks (default: True).
        :return: dict or str - List of tasks or error message.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        endpoint = LIST_TASKS_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "start": start,
            "count": count,
            "allowDrafts": allow_drafts
        }
        if id:
            params["id"] = id

        logger.debug(f"Listing tasks for project with ID {self.project_id}")

        response = self.api_service.get(endpoint=endpoint, headers=headers, params=params)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list tasks for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list tasks for project {self.project_id}: {response.text}")

    def update_task(
            self,
            task_id: str,
            name: str = None,
            description: str = None,
            title_template: str = None,
            id: str = None,
            prompt_data: dict = None,
            artifact_types: List[dict] = None,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> dict:
        """
        Updates an existing task or creates it if upsert is enabled.

        :param task_id: str - Unique identifier of the task to update.
        :param name: str, optional - Updated name of the task, unique within the project, excluding ':' or '/'.
        :param description: str, optional - Updated description of the task purpose.
        :param title_template: str, optional - Updated template for task instance names (e.g., 'specs for {{issue}}').
        :param id: str, optional - Custom identifier for the task (used in upsert mode).
        :param prompt_data: dict, optional - Updated prompt configuration for task execution.
        :param artifact_types: List[dict], optional - Updated list of artifact types with 'name', 'description', 'isRequired', 'usageType', and 'artifactVariableKey'.
        :param automatic_publish: bool, optional - Publish the task after updating (default: False).
        :param upsert: bool, optional - Create the task if it does not exist (default: False).
        :return: dict or str - Updated or created task details or error message.
        :raises ValueError: If task_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during the update.
        """
        if not task_id:
            raise ValueError("Task ID must be provided.")

        identifier = task_id
        endpoint = UPSERT_TASK_V2 if upsert else UPDATE_TASK_V2
        endpoint = endpoint.format(taskId=identifier)
        if automatic_publish:
            endpoint = f"{endpoint}?automaticPublish=true"

        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "taskDefinition": {}
        }
        if id is not None and upsert:
            data["taskDefinition"]["id"] = id
        if name is not None:
            data["taskDefinition"]["name"] = name
        if description is not None:
            data["taskDefinition"]["description"] = description
        if title_template is not None:
            data["taskDefinition"]["titleTemplate"] = title_template
        if prompt_data is not None:
            data["taskDefinition"]["promptData"] = prompt_data
        if artifact_types is not None:
            data["taskDefinition"]["artifactTypes"] = artifact_types

        logger.debug(f"Updating task with ID {task_id} with data: {data}")

        response = self.api_service.put(endpoint=endpoint, headers=headers, data=data)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to update task {task_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to update task {task_id} in project {self.project_id}: {response.text}")

    def delete_task(
            self,
            task_id: str,
            task_name: str = None
    ) -> dict:
        """
        Deletes a specific task by its ID or name.

        :param task_id: str, optional - Unique identifier of the task.
        :param task_name: str, optional - Name of the task.
        :return: dict or str - Confirmation of deletion or error message.
        :raises ValueError: If neither task_id nor task_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during deletion.
        """
        if not (task_id or task_name):
            raise ValueError("Either task_id or task_name must be provided.")

        identifier = task_id if task_id else task_name
        endpoint = DELETE_TASK_V2.format(taskId=identifier)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if task_id:
            logger.debug(f"Deleting task with ID {task_id}")
        else:
            logger.debug(f"Deleting task with name {task_name}")

        response = self.api_service.delete(endpoint=endpoint, headers=headers)

        if response.status_code != 204:
            logger.error(f"Unable to delete task {task_id or task_name} from project {self.project_id}: JSON parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete task {task_id or task_name} from project {self.project_id}: {response.text}")
        else:
            return {}

    def publish_task_revision(
            self,
            task_id: str,
            task_name: str = None,
            revision: str = None
    ) -> dict:
        """
        Publishes a specific revision of a task.

        :param task_id: str, optional - Unique identifier of the task.
        :param task_name: str, optional - Name of the task.
        :param revision: str, optional - Revision of the task to publish.
        :return: dict or str - Result of the publish operation or error message.
        :raises ValueError: If neither task_id nor task_name is provided, or if revision is not specified.
        :raises InvalidAPIResponseException: If an error occurs during publishing.
        """
        if not (task_id or task_name):
            raise ValueError("Either task_id or task_name must be provided.")
        if not revision:
            raise ValueError("Revision must be provided.")

        identifier = task_id if task_id else task_name
        endpoint = PUBLISH_TASK_REVISION_V2.format(taskId=identifier)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "revision": revision
        }

        if task_id:
            logger.debug(f"Publishing revision {revision} for task with ID {task_id}")
        else:
            logger.debug(f"Publishing revision {revision} for task with name {task_name}")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to publish revision {revision} for task {task_id or task_name} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to publish revision {revision} for task {task_id or task_name} in project {self.project_id}: {response.text}")

    def start_instance(
            self,
            process_name: str,
            subject: str = None,
            variables: list = None
    ) -> dict:
        """
        Starts a new process instance.

        :param process_name: str - Name of the process to start.
        :param subject: str, optional - Subject of the process instance.
        :param variables: list, optional - List of variables (e.g., [{"key": "location", "value": "Paris"}]).
        :return: dict or str - Started instance details or error message.
        :raises InvalidAPIResponseException: If an error occurs during instance creation.
        """
        endpoint = START_INSTANCE_V2
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "instanceDefinition": {
                "process": process_name
            }
        }
        if subject:
            data["instanceDefinition"]["subject"] = subject
        if variables:
            data["instanceDefinition"]["variables"] = variables

        logger.info(f"Starting instance for process with name '{process_name}'")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to start instance for process {process_name} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to start instance for process {process_name} in project {self.project_id}: {response.text}")

    def abort_instance(
            self,
            instance_id: str
    ) -> dict:
        """
        Aborts a specific process instance.

        :param instance_id: str - Unique identifier of the instance to abort.
        :return: dict or str - Confirmation of abort operation or error message.
        :raises ValueError: If instance_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during the abort.
        """
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        endpoint = ABORT_INSTANCE_V2.format(instanceId=instance_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info(f"Aborting instance with ID '{instance_id}'")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data={})
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to abort instance {instance_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to abort instance {instance_id} in project {self.project_id}: {response.text}")

    def get_instance(
            self,
            instance_id: str
    ) -> dict:
        """
        Retrieves details of a specific process instance.

        :param instance_id: str - Unique identifier of the instance.
        :return: dict or str - Instance details or error message.
        :raises ValueError: If instance_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        endpoint = GET_INSTANCE_V2.format(instanceId=instance_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.info(f"Retrieving instance detail with ID '{instance_id}'")

        response = self.api_service.get(endpoint=endpoint, headers=headers)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve instance {instance_id} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve instance {instance_id} for project {self.project_id}: {response.text}")

    def get_instance_history(
            self,
            instance_id: str
    ) -> dict:
        """
        Retrieves the history of a specific process instance.

        :param instance_id: str - Unique identifier of the instance.
        :return: dict or str - Instance history or error message.
        :raises ValueError: If instance_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        endpoint = GET_INSTANCE_HISTORY_V2.format(instanceId=instance_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.info(f"Retrieving instance history with ID '{instance_id}'")

        response = self.api_service.get(endpoint=endpoint, headers=headers)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve history for instance {instance_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve history for instance {instance_id} in project {self.project_id}: {response.text}")

    def get_thread_information(
            self,
            thread_id: str
    ) -> dict:
        """
        Retrieves information about a specific thread.

        :param thread_id: str - Unique identifier of the thread.
        :return: dict or str - Thread information or error message.
        :raises ValueError: If thread_id is not provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not thread_id:
            raise ValueError("Thread ID must be provided.")

        endpoint = GET_THREAD_INFORMATION_V2.format(threadId=thread_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        logger.debug(f"Retrieving information about thread with ID {thread_id}")

        response = self.api_service.get(endpoint=endpoint, headers=headers)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve thread information for thread {thread_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve thread information for thread {thread_id} in project {self.project_id}: {response.text}")

    def send_user_signal(
            self,
            instance_id: str,
            signal_name: str
    ) -> dict:
        """
        Sends a user signal to a specific process instance.

        :param instance_id: str - Unique identifier of the instance.
        :param signal_name: str - Name of the user signal (e.g., 'approval').
        :return: dict or str - Confirmation of signal operation or error message.
        :raises ValueError: If instance_id or signal_name is not provided.
        :raises InvalidAPIResponseException: If an error occurs during signal sending.
        """
        if not instance_id:
            raise ValueError("Instance ID must be provided.")
        if not signal_name:
            raise ValueError("Signal name must be provided.")

        endpoint = SEND_USER_SIGNAL_V2.format(instanceId=instance_id)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "name": signal_name
        }

        logger.debug(f"Sending user signal to process instance with ID {instance_id} with data: {data}")

        response = self.api_service.post(endpoint=endpoint, headers=headers, data=data)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to send user signal {signal_name} to instance {instance_id} in project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to send user signal {signal_name} to instance {instance_id} in project {self.project_id}: {response.text}")

    def create_kb(
            self,
            name: str,
            artifacts: List[str] = None,
            metadata: List[str] = None
    ) -> dict:
        """
        Creates a new knowledge base (KB) in the specified project.

        :param name: str - Name of the knowledge base.
        :param artifacts: List[str], optional - List of artifact names associated with the KB.
        :param metadata: List[str], optional - List of metadata fields for the KB.
        :return: dict or str - Created KB details or error message.
        :raises InvalidAPIResponseException: If an error occurs during creation.
        """
        endpoint = CREATE_KB_V1
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        data = {
            "KBDefinition": {
                "name": name
            }
        }
        if artifacts:
            data["KBDefinition"]["artifacts"] = artifacts
        if metadata:
            data["KBDefinition"]["metadata"] = metadata

        logger.debug(f"Creating KB with data: {data}")

        response = self.api_service.post(
            endpoint=endpoint,
            headers=headers,
            data=data
        )
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to create knowledge base for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to create knowledge base for project {self.project_id}: {response.text}")

    def get_kb(
            self,
            kb_id: str = None,
            kb_name: str = None
    ) -> dict:
        """
        Retrieves details of a specific knowledge base (KB) by its ID or name.

        :param kb_id: str, optional - Unique identifier of the KB.
        :param kb_name: str, optional - Name of the KB.
        :return: dict or str - KB details or error message.
        :raises ValueError: If neither kb_id nor kb_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        if not (kb_id or kb_name):
            raise ValueError("Either kb_id or kb_name must be provided.")

        identifier = kb_id if kb_id else kb_name
        endpoint = GET_KB_V1.format(kbId=identifier)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if kb_id:
            logger.debug(f"Retrieving KB detail with ID {kb_id}")
        else:
            logger.debug(f"Retrieving KB detail with name {kb_name}")

        response = self.api_service.get(endpoint=endpoint, headers=headers)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to retrieve knowledge base {kb_id or kb_name} for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to retrieve knowledge base {kb_id or kb_name} for project {self.project_id}: {response.text}")

    def list_kbs(
            self,
            name: str = None,
            start: str = "0",
            count: str = "100"
    ) -> dict:
        """
        Retrieves a list of knowledge bases (KBs) in the specified project.

        :param name: str, optional - Name of the KB to filter by.
        :param start: str, optional - Starting index for pagination (default: '0').
        :param count: str, optional - Number of KBs to retrieve (default: '100').
        :return: dict or str - List of KBs or error message.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        endpoint = LIST_KBS_V1
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "start": start,
            "count": count
        }
        if name:
            params["name"] = name

        logger.debug(f"Listing tasks in project with ID {self.project_id}")

        response = self.api_service.get(endpoint=endpoint, headers=headers, params=params)
        try:
            return response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list knowledge bases for project {self.project_id}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list knowledge bases for project {self.project_id}: {response.text}")

    def delete_kb(
            self,
            kb_id: str = None,
            kb_name: str = None
    ) -> dict:
        """
        Deletes a specific knowledge base (KB) by its ID or name.

        :param kb_id: str, optional - Unique identifier of the KB.
        :param kb_name: str, optional - Name of the KB.
        :return: dict or str - Confirmation of deletion or error message.
        :raises ValueError: If neither kb_id nor kb_name is provided.
        :raises InvalidAPIResponseException: If an error occurs during deletion.
        """
        if not (kb_id or kb_name):
            raise ValueError("Either kb_id or kb_name must be provided.")

        identifier = kb_id if kb_id else kb_name
        endpoint = DELETE_KB_V1.format(kbId=identifier)
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }

        if kb_id:
            logger.debug(f"Deleting KB with ID {kb_id}")
        else:
            logger.debug(f"Deleting KB with name {kb_name}")

        response = self.api_service.delete(endpoint=endpoint, headers=headers)

        if response.status_code != 204:
            logger.error(f"Unable to delete knowledge base {kb_id or kb_name} from project {self.project_id}: JSONDecodeError parsing error (status {response.status_code}). Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to delete knowledge base {kb_id or kb_name} from project {self.project_id}: {response.text}")
        else:
            return {}

    def list_jobs(
            self,
            start: str = "0",
            count: str = "100",
            topic: str = None,
            token: str = None,
            name: str = None
    ) -> dict:
        """
        Retrieves a specific list of jobs in the specified project.

        :param start: str, optional - Starting index for pagination (default: '0').
        :param count: str, optional - Number of jobs to retrieve (default: '100').
        :param topic: str - optional - Topiccollege of the jobs to filter by.
        :param token: str, optional - Token of the jobs to filter by.
        :param name: str, optional - Name of the jobs to filter by.
        :return: dict or str - List of jobs or error message.
        :raises InvalidAPIResponseException: If an error occurs during retrieval.
        """
        endpoint = LIST_JOBS_V1
        headers = {
            "Authorization": self.api_service.token,
            "ProjectId": self.project_id
        }
        params = {
            "start": start,
            "count": count
        }
        if topic:
            params["topic"] = topic
        if token:
            params["token"] = token
        if name:
            params["name"] = name

        logger.debug(f"Listing jobs for project with ID {self.project_id}")

        response = self.api_service.get(
            endpoint=endpoint,
            headers=headers,
            params=params
        )
        try:
            result = response.json()
        except JSONDecodeError as e:
            logger.error(f"Unable to list jobs for project {self.project_id}: JSONDecodeError parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to list jobs for project {self.project_id}: {response.text}")

        return result
