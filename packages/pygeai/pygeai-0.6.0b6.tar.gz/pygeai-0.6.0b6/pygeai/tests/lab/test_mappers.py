import unittest
from unittest import TestCase
from typing import List, Dict

from pygeai.lab.models import (
    AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event,
    SequenceFlow, Task, AgenticProcessList, TaskList, ProcessInstance, ProcessInstanceList, Variable, Job
)
from pygeai.lab.processes.mappers import AgenticProcessMapper, TaskMapper, ProcessInstanceMapper, JobMapper


class TestAgenticProcessMapper(TestCase):
    """
    python -m unittest pygeai.tests.lab.test_mappers.TestAgenticProcessMapper
    """

    def test_map_to_agentic_process(self):
        process_data = {
            "key": "proc1",
            "name": "TestProcess",
            "description": "A test process",
            "kb": {"name": "TestKB", "artifactTypeName": ["doc"], "id": "kb123"},
            "agenticActivities": [
                {"key": "act1", "name": "Activity1", "taskName": "Task1", "agentName": "Agent1", "agentRevisionId": 1}
            ],
            "artifactSignals": [
                {"key": "sig1", "name": "Signal1", "handlingType": "C", "artifactTypeName": ["text"]}
            ],
            "userSignals": [
                {"key": "user1", "name": "UserSignal1"}
            ],
            "startEvent": {"key": "start", "name": "Start"},
            "endEvent": {"key": "end", "name": "End"},
            "sequenceFlows": [
                {"key": "flow1", "sourceKey": "start", "targetKey": "end"}
            ],
            "id": "proc123",
            "status": "active",
            "versionId": 1,
            "isDraft": False,
            "revision": 2
        }
        process = AgenticProcessMapper.map_to_agentic_process(process_data)
        self.assertEqual(process.key, process_data["key"])
        self.assertEqual(process.name, process_data["name"])
        self.assertEqual(process.description, process_data["description"])
        self.assertEqual(process.kb.name, process_data["kb"]["name"])
        self.assertEqual(process.agentic_activities[0].key, process_data["agenticActivities"][0]["key"])
        self.assertEqual(process.artifact_signals[0].name, process_data["artifactSignals"][0]["name"])
        self.assertEqual(process.user_signals[0].key, process_data["userSignals"][0]["key"])
        self.assertEqual(process.start_event.name, process_data["startEvent"]["name"])
        self.assertEqual(process.end_event.key, process_data["endEvent"]["key"])
        self.assertEqual(process.sequence_flows[0].target_key, process_data["sequenceFlows"][0]["targetKey"])
        self.assertEqual(process.id, process_data["id"])
        self.assertEqual(process.status, process_data["status"])
        self.assertEqual(process.version_id, process_data["versionId"])
        self.assertEqual(process.is_draft, process_data["isDraft"])
        self.assertEqual(process.revision, process_data["revision"])

    def test_map_to_agentic_process_list(self):
        process_list_data = {
            "processes": [
                {"name": "Process1", "id": "proc1"},
                {"name": "Process2", "id": "proc2"}
            ]
        }
        process_list = AgenticProcessMapper.map_to_agentic_process_list(process_list_data)
        self.assertEqual(len(process_list.processes), 2)
        self.assertEqual(process_list.processes[0].name, process_list_data["processes"][0]["name"])
        self.assertEqual(process_list.processes[1].id, process_list_data["processes"][1]["id"])
        self.assertTrue(process_list.to_dict() == {"processes": [p.to_dict() for p in process_list.processes]})

    def test_map_to_agentic_process_list_empty(self):
        process_list_data = {"processes": []}
        process_list = AgenticProcessMapper.map_to_agentic_process_list(process_list_data)
        self.assertEqual(len(process_list.processes), 0)
        self.assertTrue(process_list.to_dict() == {"processes": []})


class TestTaskMapper(TestCase):
    """
    python -m unittest pygeai.tests.lab.test_mappers.TestTaskMapper
    """

    def test_map_to_task(self):
        task_data = {
            "name": "TestTask",
            "description": "A test task",
            "titleTemplate": "Task #{{id}}",
            "id": "task123",
            "isDraft": True,
            "revision": 1,
            "status": "active"
        }
        task = TaskMapper.map_to_task(task_data)
        self.assertEqual(task.name, task_data["name"])
        self.assertEqual(task.description, task_data["description"])
        self.assertEqual(task.title_template, task_data["titleTemplate"])
        self.assertEqual(task.id, task_data["id"])
        self.assertEqual(task.is_draft, task_data["isDraft"])
        self.assertEqual(task.revision, task_data["revision"])
        self.assertEqual(task.status, task_data["status"])

    def test_map_to_task_list(self):
        task_list_data = {
            "tasks": [
                {"name": "Task1", "id": "task1"},
                {"name": "Task2", "id": "task2"}
            ]
        }
        task_list = TaskMapper.map_to_task_list(task_list_data)
        self.assertEqual(len(task_list.tasks), 2)
        self.assertEqual(task_list.tasks[0].name, task_list_data["tasks"][0]["name"])
        self.assertEqual(task_list.tasks[1].id, task_list_data["tasks"][1]["id"])
        self.assertTrue(task_list.to_dict() == [t.to_dict() for t in task_list.tasks])

    def test_map_to_task_list_empty(self):
        task_list_data = {"tasks": []}
        task_list = TaskMapper.map_to_task_list(task_list_data)
        self.assertEqual(len(task_list.tasks), 0)
        self.assertTrue(task_list.to_dict() == [])


class TestProcessInstanceMapper(TestCase):
    """
    python -m unittest pygeai.tests.lab.test_mappers.TestProcessInstanceMapper
    """

    def test_map_to_process_instance(self):
        instance_data = {
            "id": "inst123",
            "process": {"id": "proc1", "name": "TestProcess", "revision": 1},
            "createdAt": "2023-01-01T12:00:00",
            "subject": "Test Subject",
            "variables": [
                {"key": "var1", "value": "value1"}
            ],
            "status": "active"
        }
        instance = ProcessInstanceMapper.map_to_process_instance(instance_data)
        self.assertEqual(instance.id, instance_data["id"])
        self.assertEqual(instance.process.name, instance_data["process"]["name"])
        self.assertEqual(instance.created_at, instance_data["createdAt"])
        self.assertEqual(instance.subject, instance_data["subject"])
        self.assertEqual(instance.variables[0].key, instance_data["variables"][0]["key"])
        self.assertEqual(instance.status, instance_data["status"])
        self.assertTrue(isinstance(instance.process, AgenticProcess))

    def test_map_to_process_instance_list(self):
        instance_list_data = {
            "instances": [
                {"id": "inst1", "process": {"name": "Process1"}, "subject": "Subject1"},
                {"id": "inst2", "process": {"name": "Process2"}, "subject": "Subject2"}
            ]
        }
        instance_list = ProcessInstanceMapper.map_to_process_instance_list(instance_list_data)
        self.assertEqual(len(instance_list.instances), 2)
        self.assertEqual(instance_list.instances[0].id, instance_list_data["instances"][0]["id"])
        self.assertEqual(instance_list.instances[1].process.name, instance_list_data["instances"][1]["process"]["name"])
        self.assertEqual(instance_list.instances[1].subject, instance_list_data["instances"][1]["subject"])
        self.assertTrue(instance_list.to_dict() == [i.to_dict() for i in instance_list.instances])

    def test_map_to_process_instance_list_empty(self):
        instance_list_data = {"instances": []}
        instance_list = ProcessInstanceMapper.map_to_process_instance_list(instance_list_data)
        self.assertEqual(len(instance_list.instances), 0)
        self.assertTrue(instance_list.to_dict() is None)


class TestJobMapper(TestCase):
    """
    python -m unittest pygeai.tests.lab.test_mappers.TestJobMapper
    """

    def test_map_to_job(self):
        job_data = {
            "caption": "Test Job",
            "name": "Job1",
            "parameters": [
                {"Name": "param1", "Value": "value1"},
                {"Name": "param2", "Value": "value2"}
            ],
            "request": "Sample request",
            "token": "token123",
            "topic": "Default",
            "info": "Sample info"
        }
        job = JobMapper.map_to_job(job_data)
        self.assertEqual(job.caption, job_data["caption"])
        self.assertEqual(job.name, job_data["name"])
        self.assertEqual(len(job.parameters), 2)
        self.assertEqual(job.parameters[0].Name, job_data["parameters"][0]["Name"])
        self.assertEqual(job.parameters[0].Value, job_data["parameters"][0]["Value"])
        self.assertEqual(job.parameters[1].Name, job_data["parameters"][1]["Name"])
        self.assertEqual(job.parameters[1].Value, job_data["parameters"][1]["Value"])
        self.assertEqual(job.request, job_data["request"])
        self.assertEqual(job.token, job_data["token"])
        self.assertEqual(job.topic, job_data["topic"])
        self.assertEqual(job.info, job_data["info"])
        self.assertTrue(isinstance(job, Job))

    def test_map_to_job_list(self):
        job_list_data = [
            {
                "name": "Job1",
                "token": "token1",
                "caption": "Job One",
                "parameters": [
                    {"Name": "param1", "Value": "value1"}
                ],
                "request": "Request for Job1",
                "topic": "Default"
            },
            {
                "name": "Job2",
                "token": "token2",
                "caption": "Job Two",
                "parameters": [
                    {"Name": "param2", "Value": "value2"}
                ],
                "request": "Request for Job2",
                "topic": "Event"
            }
        ]
        job_list = JobMapper.map_to_job_list(job_list_data)
        self.assertEqual(len(job_list.jobs), 2)
        self.assertEqual(job_list.jobs[0].name, job_list_data[0]["name"])
        self.assertEqual(job_list.jobs[0].token, job_list_data[0]["token"])
        self.assertEqual(job_list.jobs[0].caption, job_list_data[0]["caption"])
        self.assertEqual(job_list.jobs[0].parameters[0].Name, job_list_data[0]["parameters"][0]["Name"])
        self.assertEqual(job_list.jobs[0].request, job_list_data[0]["request"])
        self.assertEqual(job_list.jobs[0].topic, job_list_data[0]["topic"])
        self.assertEqual(job_list.jobs[1].name, job_list_data[1]["name"])
        self.assertEqual(job_list.jobs[1].token, job_list_data[1]["token"])
        self.assertEqual(job_list.jobs[1].caption, job_list_data[1]["caption"])
        self.assertEqual(job_list.jobs[1].parameters[0].Name, job_list_data[1]["parameters"][0]["Name"])
        self.assertEqual(job_list.jobs[1].request, job_list_data[1]["request"])
        self.assertEqual(job_list.jobs[1].topic, job_list_data[1]["topic"])
        self.assertTrue(job_list.to_dict() == [j.to_dict() for j in job_list.jobs])

    def test_map_to_job_list_empty(self):
        job_list_data = []
        job_list = JobMapper.map_to_job_list(job_list_data)
        self.assertEqual(len(job_list.jobs), 0)
        self.assertTrue(job_list.to_dict() == [])
