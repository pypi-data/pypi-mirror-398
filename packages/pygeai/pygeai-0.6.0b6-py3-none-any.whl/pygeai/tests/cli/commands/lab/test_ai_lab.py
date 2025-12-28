import unittest
from unittest.mock import patch, MagicMock
import json
from pygeai.cli.commands.lab.ai_lab import (
    show_help,
    list_agents,
    create_agent,
    get_agent,
    create_sharing_link,
    publish_agent_revision,
    delete_agent,
    update_agent,
    create_tool,
    list_tools,
    get_tool,
    delete_tool,
    update_tool,
    publish_tool_revision,
    get_parameter,
    set_parameter,
    list_reasoning_strategies,
    create_reasoning_strategy,
    update_reasoning_strategy,
    get_reasoning_strategy,
    create_process,
    update_process,
    get_process,
    list_processes,
    list_processes_instances,
    delete_process,
    publish_process_revision,
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
    publish_task_revision,
    start_instance,
    abort_instance,
    get_instance,
    get_instance_history,
    get_thread_information,
    send_user_signal,
    create_kb,
    get_kb,
    list_kbs,
    delete_kb,
    list_jobs
)
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.cli.commands import Option


class TestAILab(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.lab.test_ai_lab.TestAILab
    """

    def test_show_help(self):
        with patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_list_agents_auto_fetch_project_id(self):
        option_list = []
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client_instance.project_id = "auto_fetched_proj"
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_agents.return_value = []
            list_agents(option_list)
            mock_client.assert_called_once_with(project_id=None)
            mock_stdout.assert_called_once_with("Agent list: \n[]")

    def test_list_agents_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_agents.return_value = [{"id": "agent1"}]
            list_agents(option_list)
            mock_client_instance.list_agents.assert_called_once_with(
                status="", start="", count="", access_scope="public",
                allow_drafts=True, allow_external=False
            )
            mock_stdout.assert_called_once_with("Agent list: \n[{'id': 'agent1'}]")

    def test_create_agent_missing_required_parameters(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with self.assertRaises(MissingRequirementException) as cm:
            create_agent(option_list)
        self.assertEqual(str(cm.exception), "Cannot create assistant without specifying name, access scope and public name")

    def test_create_agent_invalid_input_json(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "agent1"),
            (Option("access_scope", ["--access-scope"], "", True), "public"),
            (Option("public_name", ["--public-name"], "", True), "pub.agent1"),
            (Option("agent_data_prompt_input", ["--agent-data-prompt-input"], "", True), "invalid_json[")
        ]
        with self.assertRaises(WrongArgumentError) as cm:
            create_agent(option_list)
        self.assertIn("Inputs must be a list of strings", str(cm.exception))

    def test_create_agent_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "agent1"),
            (Option("access_scope", ["--access-scope"], "", True), "public"),
            (Option("public_name", ["--public-name"], "", True), "pub.agent1"),
            (Option("agent_data_prompt_input", ["--agent-data-prompt-input"], "", True), '["input1"]'),
            (Option("agent_data_prompt_output", ["--agent-data-prompt-output"], "", True), '{"key": "out1", "description": "desc"}'),
            (Option("agent_data_prompt_example", ["--agent-data-prompt-example"], "", True), '{"inputData": "ex", "output": "out"}'),
            (Option("agent_data_resource_pools", ["--agent-data-resource-pools"], "", True), '[{"name": "pool1"}]')
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout, \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_inputs', return_value=["input1"]), \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_outputs', return_value=[{"key": "out1", "description": "desc"}]), \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_examples', return_value=[{"inputData": "ex", "output": "out"}]):
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_agent.return_value = {"id": "agent1"}
            create_agent(option_list)
            mock_client_instance.create_agent.assert_called_once()
            mock_stdout.assert_called_once_with("New agent detail: \n{'id': 'agent1'}")

    def test_get_agent_missing_required_parameters(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as cm:
            get_agent(option_list)
        self.assertEqual(str(cm.exception), "Agent ID must be specified.")

    def test_get_agent_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("agent_id", ["--agent-id"], "", True), "agent1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_agent.return_value = {"id": "agent1"}
            get_agent(option_list)
            mock_client_instance.get_agent.assert_called_once_with(
                agent_id="agent1", revision=0, version=0, allow_drafts=True
            )
            mock_stdout.assert_called_once_with("Agent detail: \n{'id': 'agent1'}")

    def test_create_sharing_link_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("agent_id", ["--agent-id"], "", True), "agent1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_sharing_link.return_value = {"token": "share123"}
            create_sharing_link(option_list)
            mock_client_instance.create_sharing_link.assert_called_once_with(
                agent_id="agent1"
            )
            mock_stdout.assert_called_once_with("Sharing token: \n{'token': 'share123'}")

    def test_publish_agent_revision_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("agent_id", ["--agent-id"], "", True), "agent1"),
            (Option("revision", ["--revision"], "", True), "1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.publish_agent_revision.return_value = {"status": "published"}
            publish_agent_revision(option_list)
            mock_client_instance.publish_agent_revision.assert_called_once_with(
                agent_id="agent1", revision="1"
            )
            mock_stdout.assert_called_once_with("Published revision detail: \n{'status': 'published'}")

    def test_delete_agent_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("agent_id", ["--agent-id"], "", True), "agent1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_agent.return_value = {"status": "deleted"}
            delete_agent(option_list)
            mock_client_instance.delete_agent.assert_called_once_with(
                agent_id="agent1"
            )
            mock_stdout.assert_called_once_with("Deleted agent detail: \n{'status': 'deleted'}")

    def test_update_agent_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("agent_id", ["--agent-id"], "", True), "agent1"),
            (Option("name", ["--name"], "", True), "agent_updated"),
            (Option("access_scope", ["--access-scope"], "", True), "public"),
            (Option("public_name", ["--public-name"], "", True), "pub.agent_updated")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgentClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout, \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_inputs', return_value=[]), \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_outputs', return_value=[]), \
             patch('pygeai.cli.commands.lab.ai_lab.get_agent_data_prompt_examples', return_value=[]):
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.update_agent.return_value = {"id": "agent1", "name": "agent_updated"}
            update_agent(option_list)
            mock_client_instance.update_agent.assert_called_once()
            mock_stdout.assert_called_once_with("Updated agent detail: \n{'id': 'agent1', 'name': 'agent_updated'}")

    # Tool-related tests
    def test_create_tool_missing_required_parameters(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with self.assertRaises(MissingRequirementException) as cm:
            create_tool(option_list)
        self.assertEqual(str(cm.exception), "Tool name must be specified.")

    def test_create_tool_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "tool1"),
            (Option("access_scope", ["--access-scope"], "", True), "private")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout, \
             patch('pygeai.cli.commands.lab.ai_lab.get_tool_parameters', return_value=[]):
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_tool.return_value = {"id": "tool1"}
            create_tool(option_list)
            mock_client_instance.create_tool.assert_called_once()
            mock_stdout.assert_called_once_with("New tool detail: \n{'id': 'tool1'}")

    def test_list_tools_invalid_scope(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("scope", ["--scope"], "", True), "invalid")
        ]
        with self.assertRaises(ValueError) as cm:
            list_tools(option_list)
        self.assertIn("Scope must be one of", str(cm.exception))

    def test_list_tools_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_tools.return_value = [{"id": "tool1"}]
            list_tools(option_list)
            mock_client_instance.list_tools.assert_called_once_with(
                id="", count="100", access_scope="public",
                allow_drafts=True, scope="api", allow_external=True
            )
            mock_stdout.assert_called_once_with("Tool list: \n[{'id': 'tool1'}]")

    def test_get_tool_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_tool.return_value = {"id": "tool1"}
            get_tool(option_list)
            mock_client_instance.get_tool.assert_called_once_with(
                tool_id="tool1", revision=0, version=0, allow_drafts=True
            )
            mock_stdout.assert_called_once_with("Tool detail: \n{'id': 'tool1'}")

    def test_delete_tool_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_tool.return_value = {"status": "deleted"}
            delete_tool(option_list)
            mock_client_instance.delete_tool.assert_called_once_with(
                tool_id="tool1", tool_name=None
            )
            mock_stdout.assert_called_once_with("Deleted tool detail: \n{'status': 'deleted'}")

    def test_update_tool_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1"),
            (Option("name", ["--name"], "", True), "tool_updated")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout, \
             patch('pygeai.cli.commands.lab.ai_lab.get_tool_parameters', return_value=[]):
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.update_tool.return_value = {"id": "tool1", "name": "tool_updated"}
            update_tool(option_list)
            mock_client_instance.update_tool.assert_called_once()
            mock_stdout.assert_called_once_with("Updated tool detail: \n{'id': 'tool1', 'name': 'tool_updated'}")

    def test_publish_tool_revision_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1"),
            (Option("revision", ["--revision"], "", True), "1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.publish_tool_revision.return_value = {"status": "published"}
            publish_tool_revision(option_list)
            mock_client_instance.publish_tool_revision.assert_called_once_with(
                tool_id="tool1", revision="1"
            )
            mock_stdout.assert_called_once_with("Published revision detail: \n{'status': 'published'}")

    def test_get_parameter_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_parameter.return_value = {"key": "param1"}
            get_parameter(option_list)
            mock_client_instance.get_parameter.assert_called_once_with(
                tool_id="tool1", tool_public_name=None, revision=0, version=0, allow_drafts=True
            )
            mock_stdout.assert_called_once_with("Parameter detail: \n{'key': 'param1'}")

    def test_set_parameter_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("tool_id", ["--tool-id"], "", True), "tool1"),
            (Option("parameter", ["--parameter"], "", True), '{"key": "param1", "dataType": "String"}')
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ToolClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout, \
             patch('pygeai.cli.commands.lab.ai_lab.get_tool_parameters', return_value=[{"key": "param1", "dataType": "String"}]):
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.set_parameter.return_value = {"status": "set"}
            set_parameter(option_list)
            mock_client_instance.set_parameter.assert_called_once_with(
                tool_id="tool1", tool_public_name=None, parameters=[{"key": "param1", "dataType": "String"}]
            )
            mock_stdout.assert_called_once_with("Set parameter detail: \n{'status': 'set'}")

    def test_list_reasoning_strategies_invalid_access_scope(self):
        option_list = [(Option("access_scope", ["--access-scope"], "", True), "invalid")]
        with self.assertRaises(WrongArgumentError) as cm:
            list_reasoning_strategies(option_list)
        self.assertEqual(str(cm.exception), "Access scope must be either 'public' or 'private'.")

    def test_list_reasoning_strategies_success(self):
        option_list = []
        with patch('pygeai.cli.commands.lab.ai_lab.ReasoningStrategyClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_reasoning_strategies.return_value = [{"id": "rs1"}]
            list_reasoning_strategies(option_list)
            mock_client_instance.list_reasoning_strategies.assert_called_once_with(
                name="", start="0", count="100", allow_external=True, access_scope="public"
            )
            mock_stdout.assert_called_once_with("Reasoning strategies list: \n[{'id': 'rs1'}]")

    def test_create_reasoning_strategy_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "rs1"),
            (Option("system_prompt", ["--system-prompt"], "", True), "prompt text")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ReasoningStrategyClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_reasoning_strategy.return_value = {"id": "rs1"}
            create_reasoning_strategy(option_list)
            mock_client_instance.create_reasoning_strategy.assert_called_once()
            mock_stdout.assert_called_once_with("Created reasoning strategy detail: \n{'id': 'rs1'}")

    def test_update_reasoning_strategy_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("reasoning_strategy_id", ["--reasoning-strategy-id"], "", True), "rs1"),
            (Option("name", ["--name"], "", True), "rs_updated")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ReasoningStrategyClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.update_reasoning_strategy.return_value = {"id": "rs1", "name": "rs_updated"}
            update_reasoning_strategy(option_list)
            mock_client_instance.update_reasoning_strategy.assert_called_once()
            mock_stdout.assert_called_once_with("Updated reasoning strategy detail: \n{'id': 'rs1', 'name': 'rs_updated'}")

    def test_get_reasoning_strategy_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("reasoning_strategy_id", ["--reasoning-strategy-id"], "", True), "rs1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.ReasoningStrategyClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_reasoning_strategy.return_value = {"id": "rs1"}
            get_reasoning_strategy(option_list)
            mock_client_instance.get_reasoning_strategy.assert_called_once_with(
                reasoning_strategy_id="rs1", reasoning_strategy_name=None
            )
            mock_stdout.assert_called_once_with("Reasoning strategy detail: \n{'id': 'rs1'}")

    # Process-related tests
    def test_create_process_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("key", ["--key"], "", True), "proc_key"),
            (Option("name", ["--name"], "", True), "proc1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_process.return_value = {"id": "proc1"}
            create_process(option_list)
            mock_client_instance.create_process.assert_called_once()
            mock_stdout.assert_called_once_with("Created process detail: \n{'id': 'proc1'}")

    def test_update_process_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_id", ["--process-id"], "", True), "proc1"),
            (Option("name", ["--name"], "", True), "proc_updated")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.update_process.return_value = {"id": "proc1", "name": "proc_updated"}
            update_process(option_list)
            mock_client_instance.update_process.assert_called_once()
            mock_stdout.assert_called_once_with("Updated process detail: \n{'id': 'proc1', 'name': 'proc_updated'}")

    def test_get_process_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_id", ["--process-id"], "", True), "proc1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_process.return_value = {"id": "proc1"}
            get_process(option_list)
            mock_client_instance.get_process.assert_called_once_with(
                process_id="proc1", process_name=None, revision="0", version=0, allow_drafts=True
            )
            mock_stdout.assert_called_once_with("Process detail: \n{'id': 'proc1'}")

    def test_list_processes_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_processes.return_value = [{"id": "proc1"}]
            list_processes(option_list)
            mock_client_instance.list_processes.assert_called_once_with(
                id=None, name=None, status=None, start="0", count="100", allow_draft=True
            )
            mock_stdout.assert_called_once_with("Process list: \n[{'id': 'proc1'}]")

    def test_list_processes_instances_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_id", ["--process-id"], "", True), "proc1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_process_instances.return_value = [{"id": "inst1"}]
            list_processes_instances(option_list)
            mock_client_instance.list_process_instances.assert_called_once_with(
                process_id="proc1", is_active=True, start="0", count="10"
            )
            mock_stdout.assert_called_once_with("Process instances list: \n[{'id': 'inst1'}]")

    def test_delete_process_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_id", ["--process-id"], "", True), "proc1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_process.return_value = {"status": "deleted"}
            delete_process(option_list)
            mock_client_instance.delete_process.assert_called_once_with(
                process_id="proc1", process_name=None
            )
            mock_stdout.assert_called_once_with("Delete process result: \n{'status': 'deleted'}")

    def test_publish_process_revision_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_id", ["--process-id"], "", True), "proc1"),
            (Option("revision", ["--revision"], "", True), "1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.publish_process_revision.return_value = {"status": "published"}
            publish_process_revision(option_list)
            mock_client_instance.publish_process_revision.assert_called_once_with(
                process_id="proc1", process_name=None, revision="1"
            )
            mock_stdout.assert_called_once_with("Published process revision detail: \n{'status': 'published'}")

    # Task-related tests
    def test_create_task_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "task1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_task.return_value = {"id": "task1"}
            create_task(option_list)
            mock_client_instance.create_task.assert_called_once()
            mock_stdout.assert_called_once_with("Created task detail: \n{'id': 'task1'}")

    def test_get_task_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("task_id", ["--task-id"], "", True), "task1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_task.return_value = {"id": "task1"}
            get_task(option_list)
            mock_client_instance.get_task.assert_called_once_with(
                task_id="task1", task_name=None
            )
            mock_stdout.assert_called_once_with("Task detail: \n{'id': 'task1'}")

    def test_list_tasks_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_tasks.return_value = [{"id": "task1"}]
            list_tasks(option_list)
            mock_client_instance.list_tasks.assert_called_once_with(
                id=None, start="0", count="100", allow_drafts=True
            )
            mock_stdout.assert_called_once_with("Task list: \n[{'id': 'task1'}]")

    def test_update_task_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("task_id", ["--task-id"], "", True), "task1"),
            (Option("name", ["--name"], "", True), "task_updated")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.update_task.return_value = {"id": "task1", "name": "task_updated"}
            update_task(option_list)
            mock_client_instance.update_task.assert_called_once()
            mock_stdout.assert_called_once_with("Updated task detail: \n{'id': 'task1', 'name': 'task_updated'}")

    def test_delete_task_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("task_id", ["--task-id"], "", True), "task1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_task.return_value = {"status": "deleted"}
            delete_task(option_list)
            mock_client_instance.delete_task.assert_called_once_with(
                task_id="task1", task_name=None
            )
            mock_stdout.assert_called_once_with("Delete task result: \n{'status': 'deleted'}")

    def test_publish_task_revision_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("task_id", ["--task-id"], "", True), "task1"),
            (Option("revision", ["--revision"], "", True), "1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.publish_task_revision.return_value = {"status": "published"}
            publish_task_revision(option_list)
            mock_client_instance.publish_task_revision.assert_called_once_with(
                task_id="task1", task_name=None, revision="1"
            )
            mock_stdout.assert_called_once_with("Published task revision detail: \n{'status': 'published'}")

    def test_start_instance_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("process_name", ["--process-name"], "", True), "proc1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.start_instance.return_value = {"id": "inst1"}
            start_instance(option_list)
            mock_client_instance.start_instance.assert_called_once_with(
                process_name="proc1", subject=None, variables=None
            )
            mock_stdout.assert_called_once_with("Started instance detail: \n{'id': 'inst1'}")

    def test_abort_instance_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("instance_id", ["--instance-id"], "", True), "inst1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.abort_instance.return_value = {"status": "aborted"}
            abort_instance(option_list)
            mock_client_instance.abort_instance.assert_called_once_with(
                instance_id="inst1"
            )
            mock_stdout.assert_called_once_with("Abort instance result: \n{'status': 'aborted'}")

    def test_get_instance_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("instance_id", ["--instance-id"], "", True), "inst1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
             patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_instance.return_value = {"id": "inst1"}
            get_instance(option_list)
            mock_client_instance.get_instance.assert_called_once_with(
                instance_id="inst1"
            )
            mock_stdout.assert_called_once_with("Instance detail: \n{'id': 'inst1'}")

    def test_get_thread_information_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("thread_id", ["--thread-id"], "", True), "thread1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_thread_information.return_value = {"id": "thread1"}
            get_thread_information(option_list)
            mock_client_instance.get_thread_information.assert_called_once_with(
                thread_id="thread1"
            )
            mock_stdout.assert_called_once_with("Thread information: \n{'id': 'thread1'}")

    def test_send_user_signal_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("instance_id", ["--instance-id"], "", True), "inst1"),
            (Option("signal_name", ["--signal-name"], "", True), "signal1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.send_user_signal.return_value = {"status": "sent"}
            send_user_signal(option_list)
            mock_client_instance.send_user_signal.assert_called_once_with(
                instance_id="inst1", signal_name="signal1"
            )
            mock_stdout.assert_called_once_with("Send user signal result: \n{'status': 'sent'}")

    def test_create_kb_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("name", ["--name"], "", True), "kb1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.create_kb.return_value = {"id": "kb1"}
            create_kb(option_list)
            mock_client_instance.create_kb.assert_called_once_with(
                name="kb1", artifacts=None, metadata=None
            )
            mock_stdout.assert_called_once_with("Created knowledge base detail: \n{'id': 'kb1'}")

    def test_get_kb_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("kb_id", ["--kb-id"], "", True), "kb1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.get_kb.return_value = {"id": "kb1"}
            get_kb(option_list)
            mock_client_instance.get_kb.assert_called_once_with(
                kb_id="kb1", kb_name=None
            )
            mock_stdout.assert_called_once_with("Knowledge base detail: \n{'id': 'kb1'}")

    def test_list_kbs_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_kbs.return_value = [{"id": "kb1"}]
            list_kbs(option_list)
            mock_client_instance.list_kbs.assert_called_once_with(
                name=None, start="0", count="100"
            )
            mock_stdout.assert_called_once_with("Knowledge base list: \n[{'id': 'kb1'}]")

    def test_delete_kb_success(self):
        option_list = [
            (Option("project_id", ["--project-id"], "", True), "proj123"),
            (Option("kb_id", ["--kb-id"], "", True), "kb1")
        ]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.delete_kb.return_value = {"status": "deleted"}
            delete_kb(option_list)
            mock_client_instance.delete_kb.assert_called_once_with(
                kb_id="kb1", kb_name=None
            )
            mock_stdout.assert_called_once_with("Delete knowledge base result: \n{'status': 'deleted'}")

    def test_list_jobs_success(self):
        option_list = [(Option("project_id", ["--project-id"], "", True), "proj123")]
        with patch('pygeai.cli.commands.lab.ai_lab.AgenticProcessClient') as mock_client, \
                patch('pygeai.cli.commands.lab.ai_lab.Console.write_stdout') as mock_stdout:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.list_jobs.return_value = [{"id": "job1"}]
            list_jobs(option_list)
            mock_client_instance.list_jobs.assert_called_once_with(
                start="0", count="100", topic=None, token=None, name=None
            )
            mock_stdout.assert_called_once_with("Job list: \n[{'id': 'job1'}]")
