import unittest
from unittest import TestCase
from pydantic import ValidationError
from pygeai.lab.spec.parsers import AgentParser, ToolParser, TaskParser, AgenticProcessParser
from pygeai.lab.models import Agent, Tool, Task, AgenticProcess, Prompt, LlmConfig, Sampling, ModelList, Model, AgentData


class TestParser(TestCase):
    """
    python -m unittest pygeai.tests.lab.spec.test_parsers.TestParser
    """

    def test_get_agent_valid_input(self):
        valid_agent_data = {
            "id": "agent-123",
            "name": "TestAgent",
            "accessScope": "private",
            "status": "active",
            "isDraft": True,
            "isReadonly": False,
            "agentData": {
                "prompt": {
                    "instructions": "Perform a task",
                    "inputs": ["input1"],
                    "outputs": [{"key": "output1", "description": "Output description"}]
                },
                "llmConfig": {
                    "maxTokens": 1000,
                    "timeout": 30,
                    "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}
                },
                "models": [{"name": "model1"}]
            }
        }
        agent = AgentParser.get_agent(valid_agent_data)
        self.assertIsInstance(agent, Agent)
        self.assertEqual(agent.id, valid_agent_data["id"])
        self.assertEqual(agent.name, valid_agent_data["name"])
        self.assertEqual(agent.agent_data.prompt.instructions, valid_agent_data["agentData"]["prompt"]["instructions"])
        self.assertEqual(agent.agent_data.models[0].name, valid_agent_data["agentData"]["models"][0]["name"])

    def test_get_agent_invalid_input(self):
        invalid_agent_data = {
            "id": "agent-123",
            "name": "",  # Invalid: name cannot be blank
            "accessScope": "private"
        }
        with self.assertRaises(ValidationError) as cm:
            AgentParser.get_agent(invalid_agent_data)
        self.assertIn("name cannot be blank", str(cm.exception))

    def test_get_agent_non_dict_input(self):
        with self.assertRaises(ValidationError):
            AgentParser.get_agent("not a dictionary")

    def test_get_tool_valid_input(self):
        valid_tool_data = {
            "name": "TestTool",
            "description": "A test tool",
            "scope": "builtin",
            "parameters": [
                {
                    "key": "param1",
                    "dataType": "String",
                    "description": "Parameter description",
                    "isRequired": True,
                    "type": "app"
                }
            ]
        }
        tool = ToolParser.get_tool(valid_tool_data)
        self.assertIsInstance(tool, Tool)
        self.assertEqual(tool.name, valid_tool_data["name"])
        self.assertEqual(tool.description, valid_tool_data["description"])
        self.assertEqual(len(tool.parameters), 1)
        self.assertEqual(tool.parameters[0].key, valid_tool_data["parameters"][0]["key"])

    def test_get_tool_invalid_input(self):
        invalid_tool_data = {
            "name": "",  # Invalid: name cannot be blank
            "description": "A test tool",
            "scope": "builtin"
        }
        with self.assertRaises(ValidationError) as cm:
            ToolParser.get_tool(invalid_tool_data)
        self.assertIn("name cannot be blank", str(cm.exception))

    def test_get_tool_non_dict_input(self):
        with self.assertRaises(ValidationError):
            ToolParser.get_tool(123)

    def test_get_task_valid_input(self):
        valid_task_data = {
            "name": "TestTask",
            "description": "A test task",
            "titleTemplate": "Task #{{id}}",
            "id": "task123",
            "promptData": {
                "instructions": "Execute task",
                "inputs": ["input1"],
                "outputs": [{"key": "output1", "description": "Output description"}]
            },
            "artifactTypes": [
                {
                    "name": "artifact1",
                    "description": "Artifact description",
                    "isRequired": False,
                    "usageType": "input",
                    "artifactVariableKey": "var1"
                }
            ]
        }
        task = TaskParser.get_task(valid_task_data)
        self.assertIsInstance(task, Task)
        self.assertEqual(task.name, valid_task_data["name"])
        self.assertEqual(task.description, valid_task_data["description"])
        self.assertEqual(task.title_template, valid_task_data["titleTemplate"])
        self.assertEqual(task.id, valid_task_data["id"])
        self.assertEqual(len(task.artifact_types.artifact_types), 1)
        self.assertEqual(task.artifact_types[0].name, valid_task_data["artifactTypes"][0]["name"])

    def test_get_task_invalid_input(self):
        invalid_task_data = {
            "name": "Test:Task",  # Invalid: contains ':'
            "description": "A test task"
        }
        with self.assertRaises(ValidationError) as cm:
            TaskParser.get_task(invalid_task_data)
        self.assertIn("Task name cannot contain ':' or '/'", str(cm.exception))

    def test_get_task_non_dict_input(self):
        with self.assertRaises(ValidationError):
            TaskParser.get_task(None)

    def test_get_agentic_process_valid_input(self):
        valid_process_data = {
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
                {"key": "flow1", "sourceKey": "start", "targetKey": "act1"}
            ],
            "id": "proc123",
            "status": "active",
            "versionId": 1,
            "isDraft": False,
            "revision": 2
        }
        process = AgenticProcessParser.get_agentic_process(valid_process_data)
        self.assertIsInstance(process, AgenticProcess)
        self.assertEqual(process.key, valid_process_data["key"])
        self.assertEqual(process.name, valid_process_data["name"])
        self.assertEqual(process.description, valid_process_data["description"])
        self.assertEqual(process.kb.name, valid_process_data["kb"]["name"])
        self.assertEqual(process.agentic_activities[0].key, valid_process_data["agenticActivities"][0]["key"])
        self.assertEqual(process.artifact_signals[0].name, valid_process_data["artifactSignals"][0]["name"])
        self.assertEqual(process.start_event.name, valid_process_data["startEvent"]["name"])

    def test_get_agentic_process_invalid_input(self):
        invalid_process_data = {
            "name": "",  # Invalid: name cannot be blank
            "description": "A test process"
        }
        with self.assertRaises(ValidationError) as cm:
            AgenticProcessParser.get_agentic_process(invalid_process_data)
        self.assertIn("name cannot be blank", str(cm.exception))

    def test_get_agentic_process_non_dict_input(self):
        with self.assertRaises(ValidationError):
            AgenticProcessParser.get_agentic_process(["not a dict"])