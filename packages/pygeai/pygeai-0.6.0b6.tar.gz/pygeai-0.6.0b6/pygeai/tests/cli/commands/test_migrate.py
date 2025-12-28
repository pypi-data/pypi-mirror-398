import unittest
from unittest.mock import patch, Mock
from pygeai.cli.commands.migrate import (
    show_help,
    migrate_base,
    clone_project,
    clone_agent,
    clone_tool,
    clone_process,
    clone_task,
    Option
)
from pygeai.core.common.exceptions import MissingRequirementException


class TestMigrateCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_migrate.TestMigrateCommands
    """
    def setUp(self):
        # Helper to create Option objects for testing
        self.mock_option = lambda name, value: (Option(name, [f"--{name}"], f"Description for {name}", True), value)

    @patch('pygeai.cli.commands.migrate.Console.write_stdout')
    @patch('pygeai.cli.commands.migrate.build_help_text')
    def test_show_help(self, mock_build_help, mock_write_stdout):
        mock_help_text = "Mocked help text"
        mock_build_help.return_value = mock_help_text

        show_help()

        mock_build_help.assert_called_once()
        mock_write_stdout.assert_called_once_with(mock_help_text)

    def test_migrate_base_success(self):
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_instance", "to_instance")
        ]

        result = migrate_base(option_list)

        self.assertEqual(result, ("from_key", "from_instance", "to_key", "to_instance"))

    def test_migrate_base_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            migrate_base(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: API key and instance")

    @patch('pygeai.cli.commands.migrate.Console.write_stdout')
    @patch('pygeai.cli.commands.migrate.MigrationTool')
    @patch('pygeai.cli.commands.migrate.ProjectMigrationStrategy')
    def test_clone_project_success(self, mock_strategy, mock_tool, mock_write_stdout):
        mock_strategy_instance = Mock()
        mock_strategy.return_value = mock_strategy_instance
        mock_tool_instance = Mock()
        mock_tool.return_value = mock_tool_instance
        mock_tool_instance.run_migration.return_value = {"status": "success"}
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_name", "new_project"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("admin_email", "admin@example.com")
        ]

        clone_project(option_list)

        mock_strategy.assert_called_once_with(
            from_api_key="from_key",
            from_project_id="proj123",
            from_instance="from_instance",
            to_api_key="to_key",
            to_project_name="new_project",
            to_instance="to_instance",
            admin_email="admin@example.com"
        )
        mock_tool.assert_called_once_with(mock_strategy_instance)
        mock_tool_instance.run_migration.assert_called_once()
        mock_write_stdout.assert_called_once_with("Migration result: \n{'status': 'success'}")

    def test_clone_project_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_name", "new_project"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("admin_email", "admin@example.com")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_project(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: project and instance")

    def test_clone_project_missing_admin_email(self):
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_name", "new_project"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_project(option_list)

        self.assertEqual(str(context.exception), "Admin email for new project must be defined.")

    @patch('pygeai.cli.commands.migrate.MigrationTool')
    @patch('pygeai.cli.commands.migrate.AgentMigrationStrategy')
    def test_clone_agent_success(self, mock_strategy, mock_tool):
        mock_strategy_instance = Mock()
        mock_strategy.return_value = mock_strategy_instance
        mock_tool_instance = Mock()
        mock_tool.return_value = mock_tool_instance
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("agent_id", "agent456")
        ]

        clone_agent(option_list)

        mock_strategy.assert_called_once_with(
            from_api_key="from_key",
            from_project_id="proj123",
            from_instance="from_instance",
            to_api_key="to_key",
            to_project_id="to_proj123",
            to_instance="to_instance",
            agent_id="agent456"
        )
        mock_tool.assert_called_once_with(mock_strategy_instance)
        mock_tool_instance.run_migration.assert_called_once()

    def test_clone_agent_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_agent(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: project, instance and agent id")

    @patch('pygeai.cli.commands.migrate.MigrationTool')
    @patch('pygeai.cli.commands.migrate.ToolMigrationStrategy')
    def test_clone_tool_success(self, mock_strategy, mock_tool):
        mock_strategy_instance = Mock()
        mock_strategy.return_value = mock_strategy_instance
        mock_tool_instance = Mock()
        mock_tool.return_value = mock_tool_instance
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("tool_id", "tool789")
        ]

        clone_tool(option_list)

        mock_strategy.assert_called_once_with(
            from_api_key="from_key",
            from_project_id="proj123",
            from_instance="from_instance",
            to_api_key="to_key",
            to_project_id="to_proj123",
            to_instance="to_instance",
            tool_id="tool789"
        )
        mock_tool.assert_called_once_with(mock_strategy_instance)
        mock_tool_instance.run_migration.assert_called_once()

    def test_clone_tool_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_tool(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: project, instance, and tool ID")

    @patch('pygeai.cli.commands.migrate.MigrationTool')
    @patch('pygeai.cli.commands.migrate.AgenticProcessMigrationStrategy')
    def test_clone_process_success(self, mock_strategy, mock_tool):
        mock_strategy_instance = Mock()
        mock_strategy.return_value = mock_strategy_instance
        mock_tool_instance = Mock()
        mock_tool.return_value = mock_tool_instance
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("process_id", "proc101")
        ]

        clone_process(option_list)

        mock_strategy.assert_called_once_with(
            from_api_key="from_key",
            from_project_id="proj123",
            from_instance="from_instance",
            to_api_key="to_key",
            to_project_id="to_proj123",
            to_instance="to_instance",
            process_id="proc101"
        )
        mock_tool.assert_called_once_with(mock_strategy_instance)
        mock_tool_instance.run_migration.assert_called_once()

    def test_clone_process_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_process(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: project, instance, and process ID")

    @patch('pygeai.cli.commands.migrate.Console.write_stdout')
    @patch('pygeai.cli.commands.migrate.MigrationTool')
    @patch('pygeai.cli.commands.migrate.TaskMigrationStrategy')
    def test_clone_task_success(self, mock_strategy, mock_tool, mock_write_stdout):
        mock_strategy_instance = Mock()
        mock_strategy.return_value = mock_strategy_instance
        mock_tool_instance = Mock()
        mock_tool.return_value = mock_tool_instance
        mock_tool_instance.run_migration.return_value = {"status": "success"}
        option_list = [
            self.mock_option("from_api_key", "from_key"),
            self.mock_option("from_project_id", "proj123"),
            self.mock_option("from_instance", "from_instance"),
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance"),
            self.mock_option("task_id", "task202")
        ]

        clone_task(option_list)

        mock_strategy.assert_called_once_with(
            from_api_key="from_key",
            from_project_id="proj123",
            from_instance="from_instance",
            to_api_key="to_key",
            to_project_id="to_proj123",
            to_instance="to_instance",
            task_id="task202"
        )
        mock_tool.assert_called_once_with(mock_strategy_instance)
        mock_tool_instance.run_migration.assert_called_once()
        mock_write_stdout.assert_called_once_with("Migration result: \n{'status': 'success'}")

    def test_clone_task_missing_source(self):
        option_list = [
            self.mock_option("to_api_key", "to_key"),
            self.mock_option("to_project_id", "to_proj123"),
            self.mock_option("to_instance", "to_instance")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            clone_task(option_list)

        self.assertEqual(str(context.exception), "Cannot migrate resources without indicating source: project, instance, and task ID")

