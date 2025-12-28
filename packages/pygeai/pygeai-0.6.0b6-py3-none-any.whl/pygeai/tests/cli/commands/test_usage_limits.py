import unittest
from unittest.mock import patch, Mock

from pygeai.cli.commands import Option
from pygeai.cli.commands.usage_limits import (
    show_help,
    set_organization_usage_limit,
    get_organization_latest_usage_limit,
    get_all_usage_limits_from_organization,
    delete_usage_limit_from_organization,
    update_organization_usage_limit,
    set_project_usage_limit,
    get_all_usage_limits_from_project,
    get_latest_usage_limit_from_project,
    get_active_usage_limit_from_project,
    delete_usage_limit_from_project,
    update_project_usage_limit
)
from pygeai.core.common.exceptions import MissingRequirementException


class TestUsageLimitsCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_usage_limits.TestUsageLimitsCommands
    """
    def setUp(self):
        # Helper to create Option objects for testing
        self.mock_option = lambda name, value: (Option(name, [f"--{name}"], f"Description for {name}", True), value)

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.build_help_text')
    def test_show_help(self, mock_build_help, mock_write_stdout):
        mock_help_text = "Mocked help text"
        mock_build_help.return_value = mock_help_text

        show_help()

        mock_build_help.assert_called_once()
        mock_write_stdout.assert_called_once_with(mock_help_text)

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_set_organization_usage_limit_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.set_organization_usage_limit.return_value = {"status": "set"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("subscription_type", "basic"),
            self.mock_option("usage_unit", "requests"),
            self.mock_option("soft_limit", "100"),
            self.mock_option("hard_limit", "200"),
            self.mock_option("renewal_status", "monthly")
        ]

        set_organization_usage_limit(option_list)

        mock_instance.set_organization_usage_limit.assert_called_once_with(
            organization="org123",
            usage_limit={
                "subscriptionType": "basic",
                "usageUnit": "requests",
                "softLimit": "100",
                "hardLimit": "200",
                "renewalStatus": "monthly"
            }
        )
        mock_write_stdout.assert_called_once_with("Organization usage limit: \n{'status': 'set'}")

    def test_set_organization_usage_limit_missing_organization(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            set_organization_usage_limit(option_list)

        self.assertEqual(str(context.exception), "Cannot set usage limit for organization without organization ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_get_organization_latest_usage_limit_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_organization_latest_usage_limit.return_value = {"limit": "latest"}
        option_list = [self.mock_option("organization", "org123")]

        get_organization_latest_usage_limit(option_list)

        mock_instance.get_organization_latest_usage_limit.assert_called_once_with(organization="org123")
        mock_write_stdout.assert_called_once_with("Organization usage limit: \n{'limit': 'latest'}")

    def test_get_organization_latest_usage_limit_missing_organization(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_organization_latest_usage_limit(option_list)

        self.assertEqual(str(context.exception), "Cannot get latest usage limit for organization without organization ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_get_all_usage_limits_from_organization_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_all_usage_limits_from_organization.return_value = {"limits": ["limit1", "limit2"]}
        option_list = [self.mock_option("organization", "org123")]

        get_all_usage_limits_from_organization(option_list)

        mock_instance.get_all_usage_limits_from_organization.assert_called_once_with(organization="org123")
        mock_write_stdout.assert_called_once_with("Organization usage limits: \n{'limits': ['limit1', 'limit2']}")

    def test_get_all_usage_limits_from_organization_missing_organization(self):
        option_list = []

        with self.assertRaises(MissingRequirementException) as context:
            get_all_usage_limits_from_organization(option_list)

        self.assertEqual(str(context.exception), "Cannot get all usage limits for organization without organization ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_delete_usage_limit_from_organization_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_usage_limit_from_organization.return_value = {"status": "deleted"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("limit_id", "limit456")
        ]

        delete_usage_limit_from_organization(option_list)

        mock_instance.delete_usage_limit_from_organization.assert_called_once_with(
            organization="org123",
            limit_id="limit456"
        )
        mock_write_stdout.assert_called_once_with("Deleted usage limit: \n{'status': 'deleted'}")

    def test_delete_usage_limit_from_organization_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            delete_usage_limit_from_organization(option_list)

        self.assertEqual(str(context.exception), "Cannot delete usage limit for organization without organization ID and limit ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_update_organization_usage_limit_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.set_organization_hard_limit.return_value = {"status": "updated_hard"}
        mock_instance.set_organization_soft_limit.return_value = {"status": "updated_soft"}
        mock_instance.set_organization_renewal_status.return_value = {"status": "updated_renewal"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("limit_id", "limit456"),
            self.mock_option("hard_limit", "200"),
            self.mock_option("soft_limit", "100"),
            self.mock_option("renewal_status", "monthly")
        ]

        update_organization_usage_limit(option_list)

        mock_instance.set_organization_hard_limit.assert_called_once_with(
            organization="org123",
            limit_id="limit456",
            hard_limit="200"
        )
        mock_instance.set_organization_soft_limit.assert_called_once_with(
            organization="org123",
            limit_id="limit456",
            soft_limit="100"
        )
        mock_instance.set_organization_renewal_status.assert_called_once_with(
            organization="org123",
            limit_id="limit456",
            renewal_status="monthly"
        )

    def test_update_organization_usage_limit_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            update_organization_usage_limit(option_list)

        self.assertEqual(str(context.exception), "Cannot update usage limit for organization without organization ID and limit ID")

    def test_update_organization_usage_limit_missing_update_values(self):
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("limit_id", "limit456")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            update_organization_usage_limit(option_list)

        self.assertEqual(str(context.exception), "At least one of the following parameters must be define to update usage limit: --soft-limit, --hard-limit or --renewal-status")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_set_project_usage_limit_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.set_project_usage_limit.return_value = {"status": "set"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456"),
            self.mock_option("subscription_type", "premium"),
            self.mock_option("usage_unit", "tokens"),
            self.mock_option("soft_limit", "500"),
            self.mock_option("hard_limit", "1000"),
            self.mock_option("renewal_status", "yearly")
        ]

        set_project_usage_limit(option_list)

        mock_instance.set_project_usage_limit.assert_called_once_with(
            organization="org123",
            project="proj456",
            usage_limit={
                "subscriptionType": "premium",
                "usageUnit": "tokens",
                "softLimit": "500",
                "hardLimit": "1000",
                "renewalStatus": "yearly"
            }
        )
        mock_write_stdout.assert_called_once_with("Project usage limit: \n{'status': 'set'}")

    def test_set_project_usage_limit_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            set_project_usage_limit(option_list)

        self.assertEqual(str(context.exception), "Cannot set usage limit for project without organization and project ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_get_all_usage_limits_from_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_all_usage_limits_from_project.return_value = {"limits": ["limit1", "limit2"]}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456")
        ]

        get_all_usage_limits_from_project(option_list)

        mock_instance.get_all_usage_limits_from_project.assert_called_once_with(
            organization="org123",
            project="proj456"
        )
        mock_write_stdout.assert_called_once_with("Project usage limits: \n{'limits': ['limit1', 'limit2']}")

    def test_get_all_usage_limits_from_project_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            get_all_usage_limits_from_project(option_list)

        self.assertEqual(str(context.exception), "Cannot get usage limits for project without organization and project ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_get_latest_usage_limit_from_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_latest_usage_limit_from_project.return_value = {"limit": "latest"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456")
        ]

        get_latest_usage_limit_from_project(option_list)

        mock_instance.get_latest_usage_limit_from_project.assert_called_once_with(
            organization="org123",
            project="proj456"
        )
        mock_write_stdout.assert_called_once_with("Project's latest usage limit: \n{'limit': 'latest'}")

    def test_get_latest_usage_limit_from_project_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            get_latest_usage_limit_from_project(option_list)

        self.assertEqual(str(context.exception), "Cannot get latest usage limit for project without organization and project ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_get_active_usage_limit_from_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.get_active_usage_limit_from_project.return_value = {"limit": "active"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456")
        ]

        get_active_usage_limit_from_project(option_list)

        mock_instance.get_active_usage_limit_from_project.assert_called_once_with(
            organization="org123",
            project="proj456"
        )
        mock_write_stdout.assert_called_once_with("Project's latest usage limit: \n{'limit': 'active'}")

    def test_get_active_usage_limit_from_project_missing_fields(self):
        option_list = [self.mock_option("organization", "org123")]

        with self.assertRaises(MissingRequirementException) as context:
            get_active_usage_limit_from_project(option_list)

        self.assertEqual(str(context.exception), "Cannot get active usage limit for project without organization and project ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_delete_usage_limit_from_project_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.delete_usage_limit_from_project.return_value = {"status": "deleted"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456"),
            self.mock_option("limit_id", "limit789")
        ]

        delete_usage_limit_from_project(option_list)

        mock_instance.delete_usage_limit_from_project.assert_called_once_with(
            organization="org123",
            project="proj456",
            limit_id="limit789"
        )
        mock_write_stdout.assert_called_once_with("Deleted usage limit: \n{'status': 'deleted'}")

    def test_delete_usage_limit_from_project_missing_fields(self):
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            delete_usage_limit_from_project(option_list)

        self.assertEqual(str(context.exception), "Cannot delete usage limit for project without organization, project and limit ID")

    @patch('pygeai.cli.commands.usage_limits.Console.write_stdout')
    @patch('pygeai.cli.commands.usage_limits.UsageLimitClient')
    def test_update_project_usage_limit_success(self, mock_client, mock_write_stdout):
        mock_instance = Mock()
        mock_client.return_value = mock_instance
        mock_instance.set_hard_limit_for_active_usage_limit_from_project.return_value = {"status": "updated_hard"}
        mock_instance.set_soft_limit_for_active_usage_limit_from_project.return_value = {"status": "updated_soft"}
        mock_instance.set_project_renewal_status.return_value = {"status": "updated_renewal"}
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456"),
            self.mock_option("limit_id", "limit789"),
            self.mock_option("hard_limit", "200"),
            self.mock_option("soft_limit", "100"),
            self.mock_option("renewal_status", "monthly")
        ]

        update_project_usage_limit(option_list)

        mock_instance.set_hard_limit_for_active_usage_limit_from_project.assert_called_once_with(
            organization="org123",
            project="proj456",
            limit_id="limit789",
            hard_limit="200"
        )
        mock_instance.set_soft_limit_for_active_usage_limit_from_project.assert_called_once_with(
            organization="org123",
            project="proj456",
            limit_id="limit789",
            soft_limit="100"
        )
        mock_instance.set_project_renewal_status.assert_called_once_with(
            organization="org123",
            project="proj456",
            limit_id="limit789",
            renewal_status="monthly"
        )

    def test_update_project_usage_limit_missing_fields(self):
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            update_project_usage_limit(option_list)

        self.assertEqual(str(context.exception), "Cannot update usage limit for project without organization ID, project ID and limit ID")

    def test_update_project_usage_limit_missing_update_values(self):
        option_list = [
            self.mock_option("organization", "org123"),
            self.mock_option("project", "proj456"),
            self.mock_option("limit_id", "limit789")
        ]

        with self.assertRaises(MissingRequirementException) as context:
            update_project_usage_limit(option_list)

        self.assertEqual(str(context.exception), "At least one of the following parameters must be define to update usage limit: --soft-limit, --hard-limit or --renewal-status")

