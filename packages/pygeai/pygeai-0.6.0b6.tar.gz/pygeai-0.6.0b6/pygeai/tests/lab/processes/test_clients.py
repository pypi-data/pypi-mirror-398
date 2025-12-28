import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.lab.processes.clients import AgenticProcessClient
from pygeai.lab.processes.endpoints import CREATE_PROCESS_V2, UPDATE_PROCESS_V2, UPSERT_PROCESS_V2, GET_PROCESS_V2, \
    LIST_PROCESSES_V2, LIST_PROCESS_INSTANCES_V2, DELETE_PROCESS_V2, PUBLISH_PROCESS_REVISION_V2, CREATE_TASK_V2, \
    GET_TASK_V2, LIST_TASKS_V2, DELETE_TASK_V2, PUBLISH_TASK_REVISION_V2, START_INSTANCE_V2, ABORT_INSTANCE_V2, \
    GET_INSTANCE_HISTORY_V2, GET_THREAD_INFORMATION_V2, SEND_USER_SIGNAL_V2, CREATE_KB_V1, \
    GET_KB_V1, LIST_KBS_V1, DELETE_KB_V1, LIST_JOBS_V1, UPSERT_TASK_V2, UPDATE_TASK_V2


class TestAgenticProcessClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_clients.TestAgenticProcessClient
    """

    def setUp(self):
        self.project_id = "test-project-id"
        self.client = AgenticProcessClient(api_key="test_key", base_url="https://test.url", project_id=self.project_id)
        self.process_id = "test-process-id"
        self.process_name = "test-process-name"
        self.task_id = "test-task-id"
        self.task_name = "test-task-name"
        self.instance_id = "test-instance-id"
        self.thread_id = "test-thread-id"
        self.kb_id = "test-kb-id"
        self.kb_name = "test-kb-name"
        self.revision = "1"
        self.signal_name = "approval"

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_process_success(self, mock_post):
        expected_response = {"id": "process-123", "name": "Test Process"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_process(
            key="test-key",
            name="Test Process",
            description="Test Description",
            kb={"name": "test-kb"},
            agentic_activities=[{"name": "activity1"}],
            artifact_signals=[{"name": "signal1"}],
            user_signals=[{"name": "user-signal1"}],
            start_event={"type": "start"},
            end_event={"type": "end"},
            sequence_flows=[{"from": "start", "to": "end"}],
            variables=[{"key": "var1", "value": "value1"}],
            automatic_publish=True
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=f"{CREATE_PROCESS_V2}?automaticPublish=true",
            headers=mock_post.call_args[1]['headers'],
            data=mock_post.call_args[1]['data']
        )
        data = mock_post.call_args[1]['data']['processDefinition']
        self.assertEqual(data['key'], "test-key")
        self.assertEqual(data['name'], "Test Process")
        self.assertEqual(data['description'], "Test Description")
        self.assertEqual(data['kb'], {"name": "test-kb"})
        self.assertEqual(data['agenticActivities'], [{"name": "activity1"}])
        self.assertEqual(data['artifactSignals'], [{"name": "signal1"}])
        self.assertEqual(data['userSignals'], [{"name": "user-signal1"}])
        self.assertEqual(data['startEvent'], {"type": "start"})
        self.assertEqual(data['endEvent'], {"type": "end"})
        self.assertEqual(data['sequenceFlows'], [{"from": "start", "to": "end"}])
        self.assertEqual(data['variables'], [{"key": "var1", "value": "value1"}])
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_process_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_process(
                key="test-key",
                name="Test Process"
            )

        self.assertEqual(str(context.exception), f"Unable to create process for project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_success_with_id(self, mock_get, mock_put):
        expected_response = {"id": self.process_id, "name": "Updated Process"}
        mock_response_put = mock_put.return_value
        mock_response_put.json.return_value = expected_response

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        result = self.client.update_process(
            process_id=self.process_id,
            name="Updated Process",
            description="Updated Description",
            automatic_publish=True,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=f"{UPDATE_PROCESS_V2.format(processId=self.process_id)}?automaticPublish=true",
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        data = mock_put.call_args[1]['data']['processDefinition']
        self.assertEqual(data['name'], "Updated Process")
        self.assertEqual(data['description'], "Updated Description")
        headers = mock_put.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_success_with_name(self, mock_get, mock_put):
        expected_response = {"id": "process-123", "name": "Updated Process"}
        mock_response_put = mock_put.return_value
        mock_response_put.json.return_value = expected_response

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        result = self.client.update_process(
            name=self.process_name,
            key="updated-key",
            description="Updated Description",
            automatic_publish=False,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROCESS_V2.format(processId=self.process_name),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_process_with_upsert(self, mock_put):
        expected_response = {"id": self.process_id, "name": "Upserted Process"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_process(
            process_id=self.process_id,
            name="Upserted Process",
            upsert=True
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPSERT_PROCESS_V2.format(processId=self.process_id),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )

    def test_update_process_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_process()
        self.assertEqual(str(context.exception), "Either process_id or name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_json_decode_error(self, mock_get, mock_put):
        mock_response_put = mock_put.return_value
        mock_response_put.status_code = 200
        mock_response_put.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response_put.text = "Invalid JSON response"

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_process(
                process_id=self.process_id,
                name="Updated Process"
            )

        self.assertEqual(str(context.exception),
                         f"Unable to update process {self.process_id} in project {self.project_id}: Invalid JSON response")
        mock_put.assert_called_once()
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_process_success_with_id(self, mock_get):
        expected_response = {"id": self.process_id, "name": "Test Process"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_process(
            process_id=self.process_id,
            revision="0",
            version=0,
            allow_drafts=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_PROCESS_V2.format(processId=self.process_id),
            headers=mock_get.call_args[1]['headers'],
            params={
                "revision": "0",
                "version": 0,
                "allowDrafts": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_process_success_with_name(self, mock_get):
        expected_response = {"id": "process-123", "name": self.process_name}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_process(
            process_name=self.process_name
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_PROCESS_V2.format(processId=self.process_name),
            headers=mock_get.call_args[1]['headers'],
            params=mock_get.call_args[1]['params']
        )

    def test_get_process_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_process()
        self.assertEqual(str(context.exception), "Either process_id or process_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_process_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_process(
                process_id=self.process_id
            )

        self.assertEqual(str(context.exception), f"Unable to retrieve process {self.process_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_processes_success(self, mock_get):
        expected_response = {"processes": [{"id": "process-1", "name": "Process1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_processes(
            id="process-1",
            name="Process1",
            status="active",
            start="0",
            count="10",
            allow_draft=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_PROCESSES_V2,
            headers=mock_get.call_args[1]['headers'],
            params={
                "id": "process-1",
                "name": "Process1",
                "status": "active",
                "start": "0",
                "count": "10",
                "allowDraft": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_processes_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_processes()

        self.assertEqual(str(context.exception), f"Unable to list processes for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_process_instances_success(self, mock_get):
        expected_response = {"instances": [{"id": "instance-1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_process_instances(
            process_id=self.process_id,
            is_active=True,
            start="0",
            count="5"
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_PROCESS_INSTANCES_V2.format(processId=self.process_id),
            headers=mock_get.call_args[1]['headers'],
            params={
                "isActive": True,
                "start": "0",
                "count": "5"
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_list_process_instances_missing_process_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.list_process_instances(process_id="")
        self.assertEqual(str(context.exception), "Process ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_process_instances_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_process_instances(
                process_id=self.process_id
            )

        self.assertEqual(str(context.exception), f"Unable to list process instances for process {self.process_id} in project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_process_success_with_id(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_process(
            process_id=self.process_id
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_PROCESS_V2.format(processId=self.process_id),
            headers=mock_delete.call_args[1]['headers']
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_process_success_with_name(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_process(
            process_name=self.process_name
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_PROCESS_V2.format(processId=self.process_name),
            headers=mock_delete.call_args[1]['headers']
        )

    def test_delete_process_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.delete_process()
        self.assertEqual(str(context.exception), "Either process_id or process_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_process_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_process(
                process_id=self.process_id
            )

        self.assertEqual(str(context.exception), f"Unable to delete process {self.process_id} from project {self.project_id}: Invalid JSON response")
        mock_delete.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_process_revision_success_with_id(self, mock_post):
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.publish_process_revision(
            process_id=self.process_id,
            revision=self.revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_PROCESS_REVISION_V2.format(processId=self.process_id),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": self.revision}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_process_revision_success_with_name(self, mock_post):
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.publish_process_revision(
            process_name=self.process_name,
            revision=self.revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_PROCESS_REVISION_V2.format(processId=self.process_name),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": self.revision}
        )

    def test_publish_process_revision_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_process_revision(
                revision=self.revision
            )
        self.assertEqual(str(context.exception), "Either process_id or process_name must be provided.")

    def test_publish_process_revision_missing_revision(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_process_revision(
                process_id=self.process_id
            )
        self.assertEqual(str(context.exception), "Revision must be provided.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_process_revision_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.publish_process_revision(
                process_id=self.process_id,
                revision=self.revision
            )

        self.assertEqual(str(context.exception), f"Unable to publish revision {self.revision} for process {self.process_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_task_success(self, mock_post):
        expected_response = {"id": "task-123", "name": "Test Task"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_task(
            name="Test Task",
            description="Task Description",
            title_template="Task for {{issue}}",
            id="custom-task-id",
            prompt_data={"instructions": "Complete this task"},
            artifact_types=[{"name": "doc", "isRequired": True}],
            automatic_publish=True
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=f"{CREATE_TASK_V2}?automaticPublish=true",
            headers=mock_post.call_args[1]['headers'],
            data=mock_post.call_args[1]['data']
        )
        data = mock_post.call_args[1]['data']['taskDefinition']
        self.assertEqual(data['name'], "Test Task")
        self.assertEqual(data['description'], "Task Description")
        self.assertEqual(data['titleTemplate'], "Task for {{issue}}")
        self.assertEqual(data['id'], "custom-task-id")
        self.assertEqual(data['promptData'], {"instructions": "Complete this task"})
        self.assertEqual(data['artifactTypes'], [{"name": "doc", "isRequired": True}])
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_task_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_task(
                name="Test Task"
            )

        self.assertEqual(str(context.exception), f"Unable to create task for project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_task_success_with_id(self, mock_get):
        expected_response = {"id": self.task_id, "name": "Test Task"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_task(
            task_id=self.task_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_TASK_V2.format(taskId=self.task_id),
            headers=mock_get.call_args[1]['headers']
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_task_success_with_name(self, mock_get):
        expected_response = {"id": "task-123", "name": self.task_name}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_task(
            task_id=self.task_id,
            task_name=self.task_name
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_TASK_V2.format(taskId=self.task_id),
            headers=mock_get.call_args[1]['headers']
        )

    def test_get_task_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_task(task_id="", task_name="")
        self.assertEqual(str(context.exception), "Either task_id or task_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_task_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_task(
                task_id=self.task_id
            )

        self.assertEqual(str(context.exception), f"Unable to retrieve task {self.task_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_tasks_success(self, mock_get):
        expected_response = {"tasks": [{"id": "task-1", "name": "Task1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_tasks(
            id="task-1",
            start="0",
            count="10",
            allow_drafts=True
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_TASKS_V2,
            headers=mock_get.call_args[1]['headers'],
            params={
                "id": "task-1",
                "start": "0",
                "count": "10",
                "allowDrafts": True
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_tasks_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_tasks()

        self.assertEqual(str(context.exception), f"Unable to list tasks for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_task_success(self, mock_put):
        expected_response = {"id": self.task_id, "name": "Updated Task"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_task(
            task_id=self.task_id,
            name="Updated Task",
            description="Updated Description",
            title_template="Updated Task for {{issue}}",
            prompt_data={"instructions": "Complete this updated task"},
            artifact_types=[{"name": "doc", "isRequired": True}],
            automatic_publish=True,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=f"{UPDATE_TASK_V2.format(taskId=self.task_id)}?automaticPublish=true",
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        data = mock_put.call_args[1]['data']['taskDefinition']
        self.assertEqual(data['name'], "Updated Task")
        self.assertEqual(data['description'], "Updated Description")
        self.assertEqual(data['titleTemplate'], "Updated Task for {{issue}}")
        self.assertEqual(data['promptData'], {"instructions": "Complete this updated task"})
        self.assertEqual(data['artifactTypes'], [{"name": "doc", "isRequired": True}])
        headers = mock_put.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_task_with_upsert(self, mock_put):
        expected_response = {"id": self.task_id, "name": "Upserted Task"}
        mock_response = mock_put.return_value
        mock_response.json.return_value = expected_response

        result = self.client.update_task(
            task_id=self.task_id,
            name="Upserted Task",
            upsert=True
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPSERT_TASK_V2.format(taskId=self.task_id),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )

    def test_update_task_missing_task_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_task(task_id="")
        self.assertEqual(str(context.exception), "Task ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.put")
    def test_update_task_json_decode_error(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_task(
                task_id=self.task_id,
                name="Updated Task"
            )

        self.assertEqual(str(context.exception), f"Unable to update task {self.task_id} in project {self.project_id}: Invalid JSON response")
        mock_put.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_task_success_with_id(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_task(
            task_id=self.task_id
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_TASK_V2.format(taskId=self.task_id),
            headers=mock_delete.call_args[1]['headers']
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_task_success_with_name(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_task(
            task_id=self.task_id,
            task_name=self.task_name
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_TASK_V2.format(taskId=self.task_id),
            headers=mock_delete.call_args[1]['headers']
        )

    def test_delete_task_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.delete_task(task_id="", task_name="")
        self.assertEqual(str(context.exception), "Either task_id or task_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_task_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_task(
                task_id=self.task_id
            )

        self.assertEqual(str(context.exception), f"Unable to delete task {self.task_id} from project {self.project_id}: Invalid JSON response")
        mock_delete.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_task_revision_success_with_id(self, mock_post):
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.publish_task_revision(
            task_id=self.task_id,
            revision=self.revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_TASK_REVISION_V2.format(taskId=self.task_id),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": self.revision}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_task_revision_success_with_name(self, mock_post):
        expected_response = {"status": "published"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.publish_task_revision(
            task_id=self.task_id,
            task_name=self.task_name,
            revision=self.revision
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=PUBLISH_TASK_REVISION_V2.format(taskId=self.task_id),
            headers=mock_post.call_args[1]['headers'],
            data={"revision": self.revision}
        )

    def test_publish_task_revision_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_task_revision(
                task_id="",
                task_name="",
                revision=self.revision
            )
        self.assertEqual(str(context.exception), "Either task_id or task_name must be provided.")

    def test_publish_task_revision_missing_revision(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_task_revision(
                task_id=self.task_id
            )
        self.assertEqual(str(context.exception), "Revision must be provided.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_publish_task_revision_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.publish_task_revision(
                task_id=self.task_id,
                revision=self.revision
            )

        self.assertEqual(str(context.exception), f"Unable to publish revision {self.revision} for task {self.task_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_start_instance_success(self, mock_post):
        expected_response = {"id": "instance-123", "status": "started"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.start_instance(
            process_name=self.process_name,
            subject="Test Subject",
            variables=[{"key": "location", "value": "Paris"}]
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=START_INSTANCE_V2,
            headers=mock_post.call_args[1]['headers'],
            data=mock_post.call_args[1]['data']
        )
        data = mock_post.call_args[1]['data']['instanceDefinition']
        self.assertEqual(data['process'], self.process_name)
        self.assertEqual(data['subject'], "Test Subject")
        self.assertEqual(data['variables'], [{"key": "location", "value": "Paris"}])
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_start_instance_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.start_instance(
                process_name=self.process_name
            )

        self.assertEqual(str(context.exception), f"Unable to start instance for process {self.process_name} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_abort_instance_success(self, mock_post):
        expected_response = {"status": "aborted"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.abort_instance(
            instance_id=self.instance_id
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=ABORT_INSTANCE_V2.format(instanceId=self.instance_id),
            headers=mock_post.call_args[1]['headers'],
            data={}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_abort_instance_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.abort_instance(instance_id="")
        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_abort_instance_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.abort_instance(
                instance_id=self.instance_id
            )

        self.assertEqual(str(context.exception), f"Unable to abort instance {self.instance_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    def test_get_instance_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_instance(instance_id="")
        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_instance_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_instance(
                instance_id=self.instance_id
            )

        self.assertEqual(str(context.exception),
                         f"Unable to retrieve instance {self.instance_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_instance_history_success(self, mock_get):
        expected_response = {"history": [{"event": "start", "time": "2023-01-01"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_instance_history(
            instance_id=self.instance_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_INSTANCE_HISTORY_V2.format(instanceId=self.instance_id),
            headers=mock_get.call_args[1]['headers']
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_get_instance_history_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_instance_history(instance_id="")
        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_instance_history_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_instance_history(
                instance_id=self.instance_id
            )

        self.assertEqual(str(context.exception),
                         f"Unable to retrieve history for instance {self.instance_id} in project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_thread_information_success(self, mock_get):
        expected_response = {"thread": {"id": self.thread_id, "status": "active"}}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_thread_information(
            thread_id=self.thread_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_THREAD_INFORMATION_V2.format(threadId=self.thread_id),
            headers=mock_get.call_args[1]['headers']
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_get_thread_information_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_thread_information(thread_id="")
        self.assertEqual(str(context.exception), "Thread ID must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_thread_information_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_thread_information(
                thread_id=self.thread_id
            )

        self.assertEqual(str(context.exception),
                         f"Unable to retrieve thread information for thread {self.thread_id} in project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_send_user_signal_success(self, mock_post):
        expected_response = {"status": "signal sent"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.send_user_signal(
            instance_id=self.instance_id,
            signal_name=self.signal_name
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=SEND_USER_SIGNAL_V2.format(instanceId=self.instance_id),
            headers=mock_post.call_args[1]['headers'],
            data={"name": self.signal_name}
        )
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    def test_send_user_signal_missing_instance_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.send_user_signal(
                instance_id="",
                signal_name=self.signal_name
            )
        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    def test_send_user_signal_missing_signal_name(self):
        with self.assertRaises(ValueError) as context:
            self.client.send_user_signal(
                instance_id=self.instance_id,
                signal_name=""
            )
        self.assertEqual(str(context.exception), "Signal name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_send_user_signal_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.send_user_signal(
                instance_id=self.instance_id,
                signal_name=self.signal_name
            )

        self.assertEqual(str(context.exception),
                         f"Unable to send user signal {self.signal_name} to instance {self.instance_id} in project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_kb_success(self, mock_post):
        expected_response = {"id": "kb-123", "name": "Test KB"}
        mock_response = mock_post.return_value
        mock_response.json.return_value = expected_response

        result = self.client.create_kb(
            name="Test KB",
            artifacts=["artifact1"],
            metadata=["meta1"]
        )

        self.assertEqual(result, expected_response)
        mock_post.assert_called_once_with(
            endpoint=CREATE_KB_V1,
            headers=mock_post.call_args[1]['headers'],
            data=mock_post.call_args[1]['data']
        )
        data = mock_post.call_args[1]['data']['KBDefinition']
        self.assertEqual(data['name'], "Test KB")
        self.assertEqual(data['artifacts'], ["artifact1"])
        self.assertEqual(data['metadata'], ["meta1"])
        headers = mock_post.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.post")
    def test_create_kb_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_kb(
                name="Test KB"
            )

        self.assertEqual(str(context.exception),
                         f"Unable to create knowledge base for project {self.project_id}: Invalid JSON response")
        mock_post.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_kb_success_with_id(self, mock_get):
        expected_response = {"id": self.kb_id, "name": "Test KB"}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_kb(
            kb_id=self.kb_id
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_KB_V1.format(kbId=self.kb_id),
            headers=mock_get.call_args[1]['headers']
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_kb_success_with_name(self, mock_get):
        expected_response = {"id": "kb-123", "name": self.kb_name}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.get_kb(
            kb_name=self.kb_name
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=GET_KB_V1.format(kbId=self.kb_name),
            headers=mock_get.call_args[1]['headers']
        )

    def test_get_kb_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_kb()
        self.assertEqual(str(context.exception), "Either kb_id or kb_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_get_kb_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_kb(
                kb_id=self.kb_id
            )

        self.assertEqual(str(context.exception),
                         f"Unable to retrieve knowledge base {self.kb_id} for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_kbs_success(self, mock_get):
        expected_response = {"kbs": [{"id": "kb-1", "name": "KB1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_kbs(
            name="KB1",
            start="0",
            count="10"
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_KBS_V1,
            headers=mock_get.call_args[1]['headers'],
            params={
                "name": "KB1",
                "start": "0",
                "count": "10"
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_kbs_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_kbs()

        self.assertEqual(str(context.exception),
                         f"Unable to list knowledge bases for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_kb_success_with_id(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_kb(
            kb_id=self.kb_id
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_KB_V1.format(kbId=self.kb_id),
            headers=mock_delete.call_args[1]['headers']
        )
        headers = mock_delete.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_kb_success_with_name(self, mock_delete):
        expected_response = {}
        mock_response = mock_delete.return_value
        mock_response.status_code = 204

        result = self.client.delete_kb(
            kb_name=self.kb_name
        )

        self.assertEqual(result, expected_response)
        mock_delete.assert_called_once_with(
            endpoint=DELETE_KB_V1.format(kbId=self.kb_name),
            headers=mock_delete.call_args[1]['headers']
        )

    def test_delete_kb_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.delete_kb()
        self.assertEqual(str(context.exception), "Either kb_id or kb_name must be provided.")

    @patch("pygeai.core.services.rest.ApiService.delete")
    def test_delete_kb_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_kb(
                kb_id=self.kb_id
            )

        self.assertEqual(str(context.exception),
                         f"Unable to delete knowledge base {self.kb_id} from project {self.project_id}: Invalid JSON response")
        mock_delete.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_jobs_success(self, mock_get):
        expected_response = {"jobs": [{"id": "job-1", "name": "Job1"}]}
        mock_response = mock_get.return_value
        mock_response.json.return_value = expected_response

        result = self.client.list_jobs(
            start="0",
            count="10",
            topic="test-topic",
            token="test-token",
            name="Job1"
        )

        self.assertEqual(result, expected_response)
        mock_get.assert_called_once_with(
            endpoint=LIST_JOBS_V1,
            headers=mock_get.call_args[1]['headers'],
            params={
                "start": "0",
                "count": "10",
                "topic": "test-topic",
                "token": "test-token",
                "name": "Job1"
            }
        )
        headers = mock_get.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)

    @patch("pygeai.core.services.rest.ApiService.get")
    def test_list_jobs_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.list_jobs()

        self.assertEqual(str(context.exception),
                         f"Unable to list jobs for project {self.project_id}: Invalid JSON response")
        mock_get.assert_called_once()

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_success_with_id(self, mock_get, mock_put):
        expected_response = {"id": self.process_id, "name": "Updated Process"}
        mock_response_put = mock_put.return_value
        mock_response_put.json.return_value = expected_response

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        result = self.client.update_process(
            process_id=self.process_id,
            name="Updated Process",
            description="Updated Description",
            automatic_publish=True,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=f"{UPDATE_PROCESS_V2.format(processId=self.process_id)}?automaticPublish=true",
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        data = mock_put.call_args[1]['data']['processDefinition']
        self.assertEqual(data['name'], "Updated Process")
        self.assertEqual(data['description'], "Updated Description")
        headers = mock_put.call_args[1]['headers']
        self.assertEqual(headers['ProjectId'], self.project_id)
        self.assertEqual(mock_get.call_count, 2)

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_success_with_name(self, mock_get, mock_put):
        expected_response = {"id": "process-123", "name": "Updated Process"}
        mock_response_put = mock_put.return_value
        mock_response_put.json.return_value = expected_response

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        result = self.client.update_process(
            name=self.process_name,
            key="updated-key",
            description="Updated Description",
            automatic_publish=False,
            upsert=False
        )

        self.assertEqual(result, expected_response)
        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROCESS_V2.format(processId=self.process_name),
            headers=mock_put.call_args[1]['headers'],
            data=mock_put.call_args[1]['data']
        )
        self.assertEqual(mock_get.call_count, 2)

    @patch("pygeai.core.services.rest.ApiService.put")
    @patch("pygeai.core.services.rest.ApiService.get")
    def test_update_process_json_decode_error(self, mock_get, mock_put):
        mock_response_put = mock_put.return_value
        mock_response_put.status_code = 200
        mock_response_put.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response_put.text = "Invalid JSON response"

        mock_response_get = mock_get.return_value
        mock_response_get.json.return_value = {
            "processDefinition": {
                "kb": {"name": "current-kb"},
                "agenticActivities": [{"name": "current-activity"}]
            }
        }

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_process(
                process_id=self.process_id,
                name="Updated Process"
            )

        self.assertEqual(str(context.exception),
                         f"Unable to update process {self.process_id} in project {self.project_id}: Invalid JSON response")
        mock_put.assert_called_once()
        self.assertEqual(mock_get.call_count, 2)
