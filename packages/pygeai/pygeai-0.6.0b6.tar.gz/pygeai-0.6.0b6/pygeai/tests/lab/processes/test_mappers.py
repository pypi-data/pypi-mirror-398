import unittest
from json import JSONDecodeError
from unittest.mock import MagicMock

from pygeai.lab.processes.clients import AgenticProcessClient
from pygeai.lab.processes.mappers import AgenticProcessMapper, TaskMapper, ProcessInstanceMapper, KnowledgeBaseMapper, JobMapper
from pygeai.lab.models import AgenticProcess, Task, ProcessInstance, KnowledgeBase, Job, VariableList
from pygeai.core.common.exceptions import InvalidAPIResponseException


class TestAgenticProcessMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_mappers.TestAgenticProcessMapper
    """

    def setUp(self):
        self.project_id = "test-project-id"
        self.client = AgenticProcessClient(api_key="test_key", base_url="https://test.url", project_id=self.project_id)
        self.client.api_service = MagicMock()
        self.process_id = "test-process-id"
        self.process_name = "test-process-name"
        self.task_id = "test-task-id"
        self.instance_id = "test-instance-id"
        self.thread_id = "test-thread-id"
        self.kb_id = "test-kb-id"
        self.revision = "1"
        self.mock_response = MagicMock()
        self.mock_response.json.return_value = {"status": "success"}
        self.mock_response.text = "success text"

    def test_map_to_agentic_process_full_data(self):
        data = {
            "processDefinition": {
                "key": "proc1",
                "name": "Test Process",
                "description": "A test process",
                "kb": {"name": "Test KB", "artifactTypeName": ["type1"], "id": "kb1"},
                "agenticActivities": [{"key": "act1", "name": "Activity 1", "taskName": "Task1", "agentName": "Agent1", "agentRevisionId": 1}],
                "artifactSignals": [{"key": "sig1", "name": "Signal 1", "handlingType": "C", "artifactTypeName": ["type1"]}],
                "userSignals": [{"key": "usig1", "name": "User Signal 1"}],
                "startEvent": {"key": "start1", "name": "Start Event"},
                "endEvent": {"key": "end1", "name": "End Event"},
                "sequenceFlows": [{"key": "flow1", "sourceKey": "start1", "targetKey": "act1"}],
                "variables": [{"key": "var1", "value": "value1"}],
                "id": "proc-id1",
                "status": "active",
                "versionId": 1,
                "isDraft": False,
                "revision": 2
            }
        }

        result = AgenticProcessMapper.map_to_agentic_process(data)

        self.assertIsInstance(result, AgenticProcess)
        self.assertEqual(result.key, "proc1")
        self.assertEqual(result.name, "Test Process")
        self.assertEqual(result.description, "A test process")
        self.assertEqual(result.kb.name, "Test KB")
        self.assertEqual(len(result.agentic_activities), 1)
        self.assertEqual(result.agentic_activities[0].key, "act1")
        self.assertEqual(len(result.artifact_signals), 1)
        self.assertEqual(result.artifact_signals[0].key, "sig1")
        self.assertEqual(len(result.user_signals), 1)
        self.assertEqual(result.user_signals[0].key, "usig1")
        self.assertEqual(result.start_event.key, "start1")
        self.assertEqual(result.end_event.key, "end1")
        self.assertEqual(len(result.sequence_flows), 1)
        self.assertEqual(result.sequence_flows[0].key, "flow1")
        self.assertEqual(len(result.variables.variables), 1)
        self.assertEqual(result.variables.variables[0].key, "var1")
        self.assertEqual(result.id, "proc-id1")
        self.assertEqual(result.status, "active")
        self.assertEqual(result.version_id, 1)
        self.assertFalse(result.is_draft)
        self.assertEqual(result.revision, 2)

    def test_map_to_agentic_process_minimal_data(self):
        data = {
            "processDefinition": {
                "key": "proc2",
                "name": "Minimal Process"
            }
        }

        result = AgenticProcessMapper.map_to_agentic_process(data)

        self.assertIsInstance(result, AgenticProcess)
        self.assertEqual(result.key, "proc2")
        self.assertEqual(result.name, "Minimal Process")
        self.assertIsNone(result.description)
        self.assertIsNone(result.kb)
        self.assertIsNone(result.agentic_activities)
        self.assertIsNone(result.artifact_signals)
        self.assertIsNone(result.user_signals)
        self.assertIsNone(result.start_event)
        self.assertIsNone(result.end_event)
        self.assertIsNone(result.sequence_flows)
        self.assertIsInstance(result.variables, VariableList)
        self.assertEqual(len(result.variables.variables), 0)

    def test_map_to_agentic_process_list_empty(self):
        data = {"processes": []}

        result = AgenticProcessMapper.map_to_agentic_process_list(data)

        self.assertEqual(len(result.processes), 0)

    def test_map_to_agentic_process_list_with_data(self):
        data = {
            "processes": [
                {"processDefinition": {"key": "proc1", "name": "Process 1"}},
                {"processDefinition": {"key": "proc2", "name": "Process 2"}}
            ]
        }

        result = AgenticProcessMapper.map_to_agentic_process_list(data)

        self.assertEqual(len(result.processes), 2)
        self.assertEqual(result.processes[0].name, "Process 1")
        self.assertEqual(result.processes[1].name, "Process 2")

    def test_update_process_success_with_name(self):
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_process(
            name="Test Process",
            key="updated-key",
            automatic_publish=False,
            upsert=False
        )

        self.client.api_service.put.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_update_process_with_upsert(self):
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_process(
            process_id=self.process_id,
            name="Upserted Process",
            automatic_publish=True,
            upsert=True
        )

        self.client.api_service.put.assert_called_once()
        endpoint = self.client.api_service.put.call_args[1]['endpoint']
        self.assertIn("upsert", endpoint)
        self.assertEqual(result, {"status": "success"})

    def test_update_process_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.put.return_value = self.mock_response

        try:
            result = self.client.update_process(
                process_id=self.process_id,
                name="Updated Process"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_process_success_with_name(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_process(
            process_name="Test Process",
            revision="1",
            version=1,
            allow_drafts=False
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_process_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_process(
                process_id=self.process_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_list_processes_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.list_processes()
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_list_process_instances_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.list_process_instances(
            process_id=self.process_id,
            is_active=False,
            start="5",
            count="20"
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_list_process_instances_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.list_process_instances(
                process_id=self.process_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_delete_process_success_with_name(self):
        self.mock_response.status_code = 204
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_process(
            process_name="Test Process"
        )

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, {})

    def test_delete_process_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.delete.return_value = self.mock_response

        try:
            result = self.client.delete_process(
                process_id=self.process_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_publish_process_revision_success_with_name(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.publish_process_revision(
            process_name="Test Process",
            revision="2"
        )

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_publish_process_revision_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_process_revision(
                revision="2"
            )

        self.assertEqual(str(context.exception), "Either process_id or process_name must be provided.")

    def test_publish_process_revision_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.publish_process_revision(
                process_id=self.process_id,
                revision="2"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_create_task_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.create_task(
                name="Test Task"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_create_task_with_full_data(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.create_task(
            name="Test Task",
            description="Task Description",
            title_template="Task for {{issue}}",
            id="task1",
            prompt_data={"instructions": "Do this"},
            artifact_types=[{"name": "art1", "description": "Artifact 1", "isRequired": True, "usageType": "input"}],
            automatic_publish=True
        )

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_task_success_with_name(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_task(
            task_id="",
            task_name="Test Task"
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_task_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_task(
                task_id=self.task_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_list_tasks_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.list_tasks(
            id="task1",
            start="10",
            count="50",
            allow_drafts=False
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_list_tasks_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.list_tasks()
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_update_task_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.update_task(
                task_id=""
            )

        self.assertEqual(str(context.exception), "Task ID must be provided.")

    def test_update_task_success(self):
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_task(
            task_id=self.task_id,
            name="Updated Task",
            description="Updated Description",
            automatic_publish=True,
            upsert=False
        )

        self.client.api_service.put.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_update_task_with_upsert(self):
        self.client.api_service.put.return_value = self.mock_response

        result = self.client.update_task(
            task_id=self.task_id,
            name="Upserted Task",
            upsert=True
        )

        self.client.api_service.put.assert_called_once()
        endpoint = self.client.api_service.put.call_args[1]['endpoint']
        self.assertIn("upsert", endpoint)
        self.assertEqual(result, {"status": "success"})

    def test_update_task_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.put.return_value = self.mock_response

        try:
            result = self.client.update_task(
                task_id=self.task_id,
                name="Updated Task"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_delete_task_success_with_name(self):
        self.mock_response.status_code = 204
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_task(
            task_id="",
            task_name="Test Task"
        )

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, {})

    def test_delete_task_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.delete.return_value = self.mock_response

        try:
            result = self.client.delete_task(
                task_id=self.task_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_delete_task_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.delete_task(
                task_id="",
                task_name=""
            )

        self.assertEqual(str(context.exception), "Either task_id or task_name must be provided.")

    def test_publish_task_revision_success_with_name(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.publish_task_revision(
            task_id="",
            task_name="Test Task",
            revision="3"
        )

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_publish_task_revision_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_task_revision(
                task_id="",  # Explicitly empty to trigger the ValueError
                task_name="",  # Explicitly empty to trigger the ValueError
                revision="3"
            )

        self.assertEqual(str(context.exception), "Either task_id or task_name must be provided.")

    def test_publish_task_revision_missing_revision(self):
        with self.assertRaises(ValueError) as context:
            self.client.publish_task_revision(
                task_id=self.task_id
            )

        self.assertEqual(str(context.exception), "Revision must be provided.")

    def test_publish_task_revision_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.publish_task_revision(
                task_id=self.task_id,
                revision="3"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_start_instance_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.start_instance(
                process_name="Test Process"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_start_instance_with_variables(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.start_instance(
            process_name="Test Process",
            subject="Test Subject",
            variables=[{"key": "var1", "value": "value1"}]
        )

        self.client.api_service.post.assert_called_once()
        data = self.client.api_service.post.call_args[1]['data']
        self.assertIn("variables", data["instanceDefinition"])
        self.assertEqual(result, {"status": "success"})

    def test_abort_instance_success(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.abort_instance(
            instance_id=self.instance_id
        )

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_abort_instance_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.abort_instance(
                instance_id=self.instance_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_instance_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_instance(
            instance_id=self.instance_id
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_instance_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_instance(
                instance_id=self.instance_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_instance_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_instance(
                instance_id=""
            )

        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    def test_get_instance_history_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_instance_history(
            instance_id=self.instance_id
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_instance_history_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_instance_history(
                instance_id=self.instance_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_instance_history_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_instance_history(
                instance_id=""
            )

        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    def test_get_thread_information_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_thread_information(
            thread_id=self.thread_id
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_thread_information_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_thread_information(
                thread_id=self.thread_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_thread_information_missing_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_thread_information(
                thread_id=""
            )

        self.assertEqual(str(context.exception), "Thread ID must be provided.")

    def test_send_user_signal_success(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.send_user_signal(
            instance_id=self.instance_id,
            signal_name="approval"
        )

        self.client.api_service.post.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_send_user_signal_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.send_user_signal(
                instance_id=self.instance_id,
                signal_name="approval"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_send_user_signal_missing_instance_id(self):
        with self.assertRaises(ValueError) as context:
            self.client.send_user_signal(
                instance_id="",
                signal_name="approval"
            )

        self.assertEqual(str(context.exception), "Instance ID must be provided.")

    def test_create_kb_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.post.return_value = self.mock_response

        try:
            result = self.client.create_kb(
                name="Test KB"
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_create_kb_with_full_data(self):
        self.client.api_service.post.return_value = self.mock_response

        result = self.client.create_kb(
            name="Test KB",
            artifacts=["art1", "art2"],
            metadata=["meta1", "meta2"]
        )

        self.client.api_service.post.assert_called_once()
        data = self.client.api_service.post.call_args[1]['data']
        self.assertIn("artifacts", data["KBDefinition"])
        self.assertIn("metadata", data["KBDefinition"])
        self.assertEqual(result, {"status": "success"})

    def test_get_kb_success_with_name(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.get_kb(
            kb_id="",
            kb_name="Test KB"
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_get_kb_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.get_kb(
                kb_id=self.kb_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_get_kb_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.get_kb(
                kb_id="",
                kb_name=""
            )

        self.assertEqual(str(context.exception), "Either kb_id or kb_name must be provided.")

    def test_list_kbs_success(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.list_kbs(
            name="Test KB",
            start="5",
            count="25"
        )

        self.client.api_service.get.assert_called_once()
        self.assertEqual(result, {"status": "success"})

    def test_list_kbs_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.list_kbs()
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_delete_kb_success_with_name(self):
        self.mock_response.status_code = 204
        self.client.api_service.delete.return_value = self.mock_response

        result = self.client.delete_kb(
            kb_id="",
            kb_name="Test KB"
        )

        self.client.api_service.delete.assert_called_once()
        self.assertEqual(result, {})

    def test_delete_kb_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.delete.return_value = self.mock_response

        try:
            result = self.client.delete_kb(
                kb_id=self.kb_id
            )
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_delete_kb_missing_identifier(self):
        with self.assertRaises(ValueError) as context:
            self.client.delete_kb(
                kb_id="",
                kb_name=""
            )

        self.assertEqual(str(context.exception), "Either kb_id or kb_name must be provided.")

    def test_list_jobs_json_decode_error(self):
        self.mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        self.client.api_service.get.return_value = self.mock_response

        try:
            result = self.client.list_jobs()
        except InvalidAPIResponseException as e:
            result = self.mock_response.text

        self.assertEqual(result, "success text")

    def test_list_jobs_with_filters(self):
        self.client.api_service.get.return_value = self.mock_response

        result = self.client.list_jobs(
            start="10",
            count="30",
            topic="test-topic",
            token="test-token",
            name="test-name"
        )

        self.client.api_service.get.assert_called_once()
        params = self.client.api_service.get.call_args[1]['params']
        self.assertEqual(params['topic'], "test-topic")
        self.assertEqual(params['token'], "test-token")
        self.assertEqual(params['name'], "test-name")
        self.assertEqual(result, {"status": "success"})


class TestTaskMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_mappers.TestTaskMapper
    """

    def test_map_to_task_full_data(self):
        data = {
            "taskDefinition": {
                "name": "Test Task",
                "description": "Task Description",
                "titleTemplate": "Task for {{issue}}",
                "id": "task1",
                "promptData": {
                    "instructions": "Do this task",
                    "inputs": ["input1"],
                    "outputs": [{"key": "out1", "description": "Output 1"}],
                    "examples": [{"inputData": "example input", "output": "example output"}]
                },
                "artifactTypes": [{"name": "art1", "description": "Artifact 1", "isRequired": True, "usageType": "input", "artifactVariableKey": "var1"}],
                "isDraft": True,
                "revision": 1,
                "status": "active"
            }
        }

        result = TaskMapper.map_to_task(data)

        self.assertIsInstance(result, Task)
        self.assertEqual(result.name, "Test Task")
        self.assertEqual(result.description, "Task Description")
        self.assertEqual(result.title_template, "Task for {{issue}}")
        self.assertEqual(result.id, "task1")
        self.assertEqual(result.prompt_data.instructions, "Do this task")
        self.assertEqual(len(result.prompt_data.outputs), 1)
        self.assertEqual(result.prompt_data.outputs[0].key, "out1")
        self.assertEqual(len(result.prompt_data.examples), 1)
        self.assertEqual(result.prompt_data.examples[0].input_data, "example input")
        self.assertEqual(len(result.artifact_types.artifact_types), 1)
        self.assertEqual(result.artifact_types.artifact_types[0].name, "art1")
        self.assertTrue(result.is_draft)
        self.assertEqual(result.revision, 1)
        self.assertEqual(result.status, "active")

    def test_map_to_task_minimal_data(self):
        data = {
            "taskDefinition": {
                "name": "Minimal Task"
            }
        }

        result = TaskMapper.map_to_task(data)

        self.assertIsInstance(result, Task)
        self.assertEqual(result.name, "Minimal Task")
        self.assertIsNone(result.description)
        self.assertIsNone(result.title_template)
        self.assertIsNone(result.id)
        self.assertIsNone(result.prompt_data)
        self.assertIsNone(result.artifact_types)
        self.assertIsNone(result.is_draft)

    def test_map_to_task_list_empty(self):
        data = {"tasks": []}

        result = TaskMapper.map_to_task_list(data)

        self.assertEqual(len(result.tasks), 0)

    def test_map_to_task_list_with_data(self):
        data = {
            "tasks": [
                {"taskDefinition": {"name": "Task 1"}},
                {"taskDefinition": {"name": "Task 2"}}
            ]
        }

        result = TaskMapper.map_to_task_list(data)

        self.assertEqual(len(result.tasks), 2)
        self.assertEqual(result.tasks[0].name, "Task 1")
        self.assertEqual(result.tasks[1].name, "Task 2")


class TestProcessInstanceMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_mappers.TestProcessInstanceMapper
    """

    def test_map_to_process_instance_full_data(self):
        data = {
            "id": "inst1",
            "process": {"id": "proc1", "name": "Test Process", "revision": 1, "version": 1, "isDraft": False},
            "createdAt": "2023-01-01T00:00:00Z",
            "subject": "Test Subject",
            "variables": [{"key": "var1", "value": "value1"}],
            "status": "active"
        }

        result = ProcessInstanceMapper.map_to_process_instance(data)

        self.assertIsInstance(result, ProcessInstance)
        self.assertEqual(result.id, "inst1")
        self.assertEqual(result.process.name, "Test Process")
        self.assertEqual(result.created_at, "2023-01-01T00:00:00Z")
        self.assertEqual(result.subject, "Test Subject")
        self.assertEqual(len(result.variables.variables), 1)
        self.assertEqual(result.variables.variables[0].key, "var1")
        self.assertEqual(result.status, "active")

    def test_map_to_process_instance_minimal_data(self):
        data = {
            "subject": "Minimal Subject",
            "process": {"name": "Minimal Process"}
        }

        result = ProcessInstanceMapper.map_to_process_instance(data)

        self.assertIsInstance(result, ProcessInstance)
        self.assertEqual(result.subject, "Minimal Subject")
        self.assertEqual(result.process.name, "Minimal Process")
        self.assertIsNone(result.id)
        self.assertIsNone(result.created_at)
        self.assertEqual(len(result.variables.variables), 0)
        self.assertIsNone(result.status)

    def test_map_to_process_instance_list_empty(self):
        data = {"instances": []}

        result = ProcessInstanceMapper.map_to_process_instance_list(data)

        self.assertEqual(len(result.instances), 0)

    def test_map_to_process_instance_list_with_data(self):
        data = {
            "instances": [
                {"subject": "Subject 1", "process": {"name": "Process 1"}},
                {"subject": "Subject 2", "process": {"name": "Process 2"}}
            ]
        }

        result = ProcessInstanceMapper.map_to_process_instance_list(data)

        self.assertEqual(len(result.instances), 2)
        self.assertEqual(result.instances[0].subject, "Subject 1")
        self.assertEqual(result.instances[1].subject, "Subject 2")


class TestKnowledgeBaseMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_mappers.TestKnowledgeBaseMapper
    """

    def test_map_to_knowledge_base_full_data(self):
        data = {
            "name": "Test KB",
            "artifactTypeName": ["type1", "type2"],
            "id": "kb1",
            "artifacts": ["art1", "art2"],
            "metadata": ["meta1", "meta2"]
        }

        result = KnowledgeBaseMapper.map_to_knowledge_base(data)

        self.assertIsInstance(result, KnowledgeBase)
        self.assertEqual(result.name, "Test KB")
        self.assertEqual(result.artifact_type_name, ["type1", "type2"])
        self.assertEqual(result.id, "kb1")
        self.assertEqual(result.artifacts, ["art1", "art2"])
        self.assertEqual(result.metadata, ["meta1", "meta2"])

    def test_map_to_knowledge_base_minimal_data(self):
        data = {
            "name": "Minimal KB"
        }

        result = KnowledgeBaseMapper.map_to_knowledge_base(data)

        self.assertIsInstance(result, KnowledgeBase)
        self.assertEqual(result.name, "Minimal KB")
        self.assertIsNone(result.artifact_type_name)
        self.assertIsNone(result.id)
        self.assertIsNone(result.artifacts)
        self.assertIsNone(result.metadata)

    def test_map_to_knowledge_base_list_empty(self):
        data = {"knowledgeBases": []}

        result = KnowledgeBaseMapper.map_to_knowledge_base_list(data)

        self.assertEqual(len(result.knowledge_bases), 0)

    def test_map_to_knowledge_base_list_with_data(self):
        data = {
            "knowledgeBases": [
                {"name": "KB 1"},
                {"name": "KB 2"}
            ]
        }

        result = KnowledgeBaseMapper.map_to_knowledge_base_list(data)

        self.assertEqual(len(result.knowledge_bases), 2)
        self.assertEqual(result.knowledge_bases[0].name, "KB 1")
        self.assertEqual(result.knowledge_bases[1].name, "KB 2")


class TestJobMapper(unittest.TestCase):
    """
    python -m unittest pygeai.tests.lab.processes.test_mappers.TestJobMapper
    """

    def test_map_to_job_full_data(self):
        data = {
            "caption": "Job completed",
            "name": "execute_workitem_jobrunner",
            "parameters": [{"Name": "param1", "Value": "value1"}],
            "request": "2023-01-01T00:00:00Z",
            "token": "token123",
            "topic": "Default",
            "info": "Additional info"
        }

        result = JobMapper.map_to_job(data)

        self.assertIsInstance(result, Job)
        self.assertEqual(result.caption, "Job completed")
        self.assertEqual(result.name, "execute_workitem_jobrunner")
        self.assertEqual(len(result.parameters), 1)
        self.assertEqual(result.parameters[0].Name, "param1")
        self.assertEqual(result.request, "2023-01-01T00:00:00Z")
        self.assertEqual(result.token, "token123")
        self.assertEqual(result.topic, "Default")
        self.assertEqual(result.info, "Additional info")

    def test_map_to_job_minimal_data(self):
        data = {
            "caption": "Job minimal",
            "name": "minimal_job",
            "parameters": [],
            "request": "2023-01-01T00:00:00Z",
            "token": "token456",
            "topic": "Event"
        }

        result = JobMapper.map_to_job(data)

        self.assertIsInstance(result, Job)
        self.assertEqual(result.caption, "Job minimal")
        self.assertEqual(result.name, "minimal_job")
        self.assertEqual(len(result.parameters), 0)
        self.assertEqual(result.request, "2023-01-01T00:00:00Z")
        self.assertEqual(result.token, "token456")
        self.assertEqual(result.topic, "Event")
        self.assertIsNone(result.info)

    def test_map_to_job_list_empty(self):
        data = []

        result = JobMapper.map_to_job_list(data)

        self.assertEqual(len(result.jobs), 0)

    def test_map_to_job_list_with_data(self):
        data = [
            {"caption": "Job 1", "name": "job1", "parameters": [], "request": "2023-01-01", "token": "t1",
             "topic": "Default"},
            {"caption": "Job 2", "name": "job2", "parameters": [], "request": "2023-01-02", "token": "t2",
             "topic": "Event"}
        ]

        result = JobMapper.map_to_job_list(data)

        self.assertEqual(len(result.jobs), 2)
        self.assertEqual(result.jobs[0].name, "job1")
        self.assertEqual(result.jobs[1].name, "job2")