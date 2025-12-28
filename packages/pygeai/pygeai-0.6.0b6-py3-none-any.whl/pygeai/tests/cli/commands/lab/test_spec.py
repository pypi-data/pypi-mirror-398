import unittest
from unittest.mock import patch, MagicMock
from pygeai.cli.commands.lab.spec import (
    show_help,
    load_agent,
    create_agent,
    load_tool,
    create_tool,
    load_task,
    create_task,
    load_agentic_process,
    create_agentic_process
)
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.cli.commands import Option


class TestSpec(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.lab.test_spec.TestSpec
    """

    def test_show_help(self):
        with patch('pygeai.cli.commands.lab.spec.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_load_agent_missing_file(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as cm:
            load_agent(option_list)
        self.assertEqual(str(cm.exception), "Cannot load agent definition without specifying path to JSON file.")

    def test_load_agent_single_dict(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        agent_data = {"key": "value"}
        agent_mock = MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=agent_data), \
             patch('pygeai.cli.commands.lab.spec.AgentParser.get_agent', return_value=agent_mock), \
             patch('pygeai.cli.commands.lab.spec.create_agent') as mock_create:
            load_agent(option_list)
            mock_create.assert_called_once_with(agent_mock, False)

    def test_load_agent_list(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        agent_data = [{"key1": "value1"}, {"key2": "value2"}]
        agent_mock1, agent_mock2 = MagicMock(), MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=agent_data), \
             patch('pygeai.cli.commands.lab.spec.AgentParser.get_agent', side_effect=[agent_mock1, agent_mock2]), \
             patch('pygeai.cli.commands.lab.spec.create_agent') as mock_create:
            load_agent(option_list)
            self.assertEqual(mock_create.call_count, 2)
            mock_create.assert_any_call(agent_mock1, False)
            mock_create.assert_any_call(agent_mock2, False)

    def test_create_agent_success(self):
        agent_mock = MagicMock()
        created_agent_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager') as mock_manager, \
             patch('pygeai.cli.commands.lab.spec.Console.write_stdout') as mock_stdout:
            mock_manager.return_value = MagicMock()
            mock_manager.return_value.create_agent.return_value = created_agent_mock
            create_agent(agent_mock, False)
            mock_stdout.assert_called_once_with(f"Created agent detail: \n{created_agent_mock}")

    def test_create_agent_failure(self):
        agent_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager', side_effect=Exception("Error")), \
             patch('pygeai.cli.commands.lab.spec.Console.write_stderr') as mock_stderr, \
             patch('pygeai.cli.commands.lab.spec.logger.error') as mock_logger:
            create_agent(agent_mock, False)
            mock_stderr.assert_called_once_with(f"Error creating agent: \n{agent_mock}")
            mock_logger.assert_called_once()

    def test_load_tool_missing_file(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as cm:
            load_tool(option_list)
        self.assertEqual(str(cm.exception), "Cannot load tool definition without specifying path to JSON file.")

    def test_load_tool_single_dict(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        tool_data = {"key": "value"}
        tool_mock = MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=tool_data), \
             patch('pygeai.cli.commands.lab.spec.ToolParser.get_tool', return_value=tool_mock), \
             patch('pygeai.cli.commands.lab.spec.create_tool') as mock_create:
            load_tool(option_list)
            mock_create.assert_called_once_with(tool_mock, False)

    def test_load_tool_list(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        tool_data = [{"key1": "value1"}, {"key2": "value2"}]
        tool_mock1, tool_mock2 = MagicMock(), MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=tool_data), \
             patch('pygeai.cli.commands.lab.spec.ToolParser.get_tool', side_effect=[tool_mock1, tool_mock2]), \
             patch('pygeai.cli.commands.lab.spec.create_tool') as mock_create:
            load_tool(option_list)
            self.assertEqual(mock_create.call_count, 2)
            mock_create.assert_any_call(tool_mock1, False)
            mock_create.assert_any_call(tool_mock2, False)

    def test_create_tool_success(self):
        tool_mock = MagicMock()
        created_tool_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager') as mock_manager, \
             patch('pygeai.cli.commands.lab.spec.Console.write_stdout') as mock_stdout:
            mock_manager.return_value = MagicMock()
            mock_manager.return_value.create_tool.return_value = created_tool_mock
            create_tool(tool_mock, False)
            mock_stdout.assert_called_once_with(f"Created tool detail: \n{created_tool_mock}")

    def test_create_tool_failure(self):
        tool_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager', side_effect=Exception("Error")), \
             patch('pygeai.cli.commands.lab.spec.Console.write_stderr') as mock_stderr, \
             patch('pygeai.cli.commands.lab.spec.logger.error') as mock_logger:
            create_tool(tool_mock, False)
            mock_stderr.assert_called_once_with(f"Error creating tool: \n{tool_mock}")
            mock_logger.assert_called_once()

    def test_load_task_missing_file(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as cm:
            load_task(option_list)
        self.assertEqual(str(cm.exception), "Cannot load task definition without specifying path to JSON file.")

    def test_load_task_single_dict(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        task_data = {"key": "value"}
        task_mock = MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=task_data), \
             patch('pygeai.cli.commands.lab.spec.TaskParser.get_task', return_value=task_mock), \
             patch('pygeai.cli.commands.lab.spec.create_task') as mock_create:
            load_task(option_list)
            mock_create.assert_called_once_with(task_mock, False)

    def test_load_task_list(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        task_data = [{"key1": "value1"}, {"key2": "value2"}]
        task_mock1, task_mock2 = MagicMock(), MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=task_data), \
             patch('pygeai.cli.commands.lab.spec.TaskParser.get_task', side_effect=[task_mock1, task_mock2]), \
             patch('pygeai.cli.commands.lab.spec.create_task') as mock_create:
            load_task(option_list)
            self.assertEqual(mock_create.call_count, 2)
            mock_create.assert_any_call(task_mock1, False)
            mock_create.assert_any_call(task_mock2, False)

    def test_create_task_success(self):
        task_mock = MagicMock()
        created_task_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager') as mock_manager, \
             patch('pygeai.cli.commands.lab.spec.Console.write_stdout') as mock_stdout:
            mock_manager.return_value = MagicMock()
            mock_manager.return_value.create_task.return_value = created_task_mock
            create_task(task_mock, False)
            mock_stdout.assert_called_once_with(f"Created task detail: \n{created_task_mock}")

    def test_create_task_failure(self):
        task_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager', side_effect=Exception("Error")), \
             patch('pygeai.cli.commands.lab.spec.Console.write_stderr') as mock_stderr, \
             patch('pygeai.cli.commands.lab.spec.logger.error') as mock_logger:
            create_task(task_mock, False)
            mock_stderr.assert_called_once_with(f"Error creating task: \n{task_mock}")
            mock_logger.assert_called_once()

    def test_load_agentic_process_missing_file(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as cm:
            load_agentic_process(option_list)
        self.assertEqual(str(cm.exception), "Cannot load agentic process definition without specifying path to JSON file.")

    def test_load_agentic_process_single_dict(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        process_data = {"key": "value"}
        process_mock = MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=process_data), \
             patch('pygeai.cli.commands.lab.spec.AgenticProcessParser.get_agentic_process', return_value=process_mock), \
             patch('pygeai.cli.commands.lab.spec.create_agentic_process') as mock_create:
            load_agentic_process(option_list)
            mock_create.assert_called_once_with(process_mock, False)

    def test_load_agentic_process_list(self):
        option_list = [
            (Option("file", ["--file"], "", True), "file.json"),
            (Option("automatic_publish", ["--automatic-publish"], "", True), False)
        ]
        process_data = [{"key1": "value1"}, {"key2": "value2"}]
        process_mock1, process_mock2 = MagicMock(), MagicMock()

        with patch('pygeai.cli.commands.lab.spec.JSONLoader.load_data', return_value=process_data), \
             patch('pygeai.cli.commands.lab.spec.AgenticProcessParser.get_agentic_process', side_effect=[process_mock1, process_mock2]), \
             patch('pygeai.cli.commands.lab.spec.create_agentic_process') as mock_create:
            load_agentic_process(option_list)
            self.assertEqual(mock_create.call_count, 2)
            mock_create.assert_any_call(process_mock1, False)
            mock_create.assert_any_call(process_mock2, False)

    def test_create_agentic_process_success(self):
        process_mock = MagicMock()
        created_process_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager') as mock_manager, \
             patch('pygeai.cli.commands.lab.spec.Console.write_stdout') as mock_stdout:
            mock_manager.return_value = MagicMock()
            mock_manager.return_value.create_process.return_value = created_process_mock
            create_agentic_process(process_mock, False)
            mock_stdout.assert_called_once_with(f"Created agentic process detail: \n{created_process_mock}")

    def test_create_agentic_process_failure(self):
        process_mock = MagicMock()
        with patch('pygeai.cli.commands.lab.spec.AILabManager', side_effect=Exception("Error")), \
             patch('pygeai.cli.commands.lab.spec.Console.write_stderr') as mock_stderr, \
             patch('pygeai.cli.commands.lab.spec.logger.error') as mock_logger:
            create_agentic_process(process_mock, False)
            mock_stderr.assert_called_once_with(f"Error creating agentic process: \n{process_mock}")
            mock_logger.assert_called_once()
