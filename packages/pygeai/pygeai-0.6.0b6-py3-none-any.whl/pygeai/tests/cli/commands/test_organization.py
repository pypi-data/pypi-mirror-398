import unittest
from unittest.mock import patch, Mock
from pygeai.cli.commands.organization import (
    show_help,
    list_assistants,
    get_project_list,
    get_project_detail,
    create_project,
    update_project,
    delete_project,
    get_project_tokens,
    export_request_data,
    Option
)
from pygeai.core.common.exceptions import MissingRequirementException


class TestOrganizationCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_organization.TestOrganizationCommands
    """
    def setUp(self):
        # Helper to create Option objects for testing
        self.mock_option = lambda name, value: (Option(name, [f"--{name}"], f"Description for {name}", True), value)

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.build_help_text')
    def test_show_help(self, mock_build_help, mock_write_stdout):
        mock_help_text = "Mocked help text"
        mock_build_help.return_value = mock_help_text

        show_help()

        mock_build_help.assert_called_once()
        mock_write_stdout.assert_called_once_with(mock_help_text)

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.PluginClient')
    def test_list_assistants_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.list_assistants.return_value = {"assistants": ["assistant1", "assistant2"]}
        option_list = [
            self.mock_option("organization_id", "org123"),
            self.mock_option("project_id", "proj456")
        ]

        list_assistants(option_list)

        mock_instance.list_assistants.assert_called_once_with(organization_id="org123", project_id="proj456")
        mock_write_stdout.assert_called_once_with("Assistant list: \n{'assistants': ['assistant1', 'assistant2']}")

    def test_list_assistants_missing_organization_id(self):
        option_list = [self.mock_option("project_id", "proj456")]

        with self.assertRaises(MissingRequirementException) as context:
            list_assistants(option_list)

        self.assertEqual(str(context.exception), "Organization ID and Project ID are required.")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_get_project_list_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_project_list.return_value = {"projects": ["project1", "project2"]}
        option_list = [
            self.mock_option("detail", "full"),
            self.mock_option("name", "test_project")
        ]

        get_project_list(option_list)

        mock_instance.get_project_list.assert_called_once_with("full", "test_project")
        mock_write_stdout.assert_called_once_with("Project list: \n{'projects': ['project1', 'project2']}")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_get_project_detail_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_project_data.return_value = {"id": "proj123", "name": "Test Project"}
        option_list = [self.mock_option("project_id", "proj123")]

        get_project_detail(option_list)

        mock_instance.get_project_data.assert_called_once_with(project_id="proj123")
        mock_write_stdout.assert_called_once_with("Project detail: \n{'id': 'proj123', 'name': 'Test Project'}")

    def test_get_project_detail_missing_project_id(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_project_detail(option_list)

        self.assertEqual(str(context.exception), "Cannot retrieve project detail without project-id")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_create_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.create_project.return_value = {"id": "proj123", "name": "New Project"}
        option_list = [
            self.mock_option("name", "New Project"),
            self.mock_option("admin_email", "admin@example.com"),
            self.mock_option("description", "A test project"),
            self.mock_option("subscription_type", "basic")
        ]

        create_project(option_list)

        mock_instance.create_project.assert_called_once_with("New Project", "admin@example.com", "A test project")
        mock_write_stdout.assert_called_once_with("New project: \n{'id': 'proj123', 'name': 'New Project'}")

    def test_create_project_missing_name_and_email(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            create_project(option_list)

        self.assertEqual(str(context.exception), "Cannot create project without name and administrator's email")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_update_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.update_project.return_value = {"id": "proj123", "name": "Updated Project"}
        option_list = [
            self.mock_option("project_id", "proj123"),
            self.mock_option("name", "Updated Project"),
            self.mock_option("description", "Updated description")
        ]

        update_project(option_list)

        mock_instance.update_project.assert_called_once_with("proj123", "Updated Project", "Updated description")
        mock_write_stdout.assert_called_once_with("Updated project: \n{'id': 'proj123', 'name': 'Updated Project'}")

    def test_update_project_missing_project_id_and_name(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            update_project(option_list)

        self.assertEqual(str(context.exception), "Cannot update project without project-id and/or name")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_delete_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_project.return_value = {"status": "deleted"}
        option_list = [self.mock_option("project_id", "proj123")]

        delete_project(option_list)

        mock_instance.delete_project.assert_called_once_with("proj123")
        mock_write_stdout.assert_called_once_with("Deleted project: \n{'status': 'deleted'}")

    def test_delete_project_missing_project_id(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            delete_project(option_list)

        self.assertEqual(str(context.exception), "Cannot delete project without project-id")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_get_project_tokens_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_project_tokens.return_value = {"tokens": ["token1", "token2"]}
        option_list = [self.mock_option("project_id", "proj123")]

        get_project_tokens(option_list)

        mock_instance.get_project_tokens.assert_called_once_with("proj123")
        mock_write_stdout.assert_called_once_with("Project tokens: \n{'tokens': ['token1', 'token2']}")

    def test_get_project_tokens_missing_project_id(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_project_tokens(option_list)

        self.assertEqual(str(context.exception), "Cannot retrieve project tokens without project-id")

    @patch('pygeai.cli.commands.organization.Console.write_stdout')
    @patch('pygeai.cli.commands.organization.OrganizationClient')
    def test_export_request_data_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.export_request_data.return_value = {"data": ["request1", "request2"]}
        option_list = [
            self.mock_option("assistant_name", "assistant1"),
            self.mock_option("status", "completed"),
            self.mock_option("skip", "10"),
            self.mock_option("count", "20")
        ]

        export_request_data(option_list)

        mock_instance.export_request_data.assert_called_once_with("assistant1", "completed", "10", "20")
        mock_write_stdout.assert_called_once_with("Request data: \n{'data': ['request1', 'request2']}")

