import unittest
from unittest.mock import patch, Mock

from pygeai.cli.commands.secrets import (
    show_help,
    get_secret,
    create_secret,
    update_secret,
    list_secrets,
    set_secret_accesses,
    get_secret_accesses
)
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError


class TestSecretsCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_secrets.TestSecretsCommands
    """

    def test_show_help(self):
        with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_get_secret_success(self):
        option_list = [
            (Mock(spec=['name'], name="secret_id"), "secret-123")
        ]
        option_list[0][0].name = "secret_id"

        with patch('pygeai.core.secrets.clients.SecretClient.get_secret', return_value="Secret data") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_secret(option_list)
                mock_get.assert_called_once_with(secret_id="secret-123")
                mock_stdout.assert_called_once_with("Get secret result: \nSecret data")

    def test_get_secret_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_secret(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve secret without specifying secret-id")

    def test_create_secret_success(self):
        option_list = [
            (Mock(spec=['name'], name="name"), "MySecret"),
            (Mock(spec=['name'], name="secret_string"), "secret-value"),
            (Mock(spec=['name'], name="description"), "Test description")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.core.secrets.clients.SecretClient.create_secret', return_value="Created secret") as mock_create:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                create_secret(option_list)
                mock_create.assert_called_once_with(
                    name="MySecret",
                    secret_string="secret-value",
                    description="Test description"
                )
                mock_stdout.assert_called_once_with("Create secret result: \nCreated secret")

    def test_create_secret_missing_name(self):
        option_list = [
            (Mock(spec=['name'], name="secret_string"), "secret-value")
        ]
        option_list[0][0].name = "secret_string"

        with self.assertRaises(MissingRequirementException) as context:
            create_secret(option_list)
        self.assertEqual(str(context.exception), "Cannot create secret without specifying name and secret-string")

    def test_create_secret_missing_secret_string(self):
        option_list = [
            (Mock(spec=['name'], name="name"), "MySecret")
        ]
        option_list[0][0].name = "name"

        with self.assertRaises(MissingRequirementException) as context:
            create_secret(option_list)
        self.assertEqual(str(context.exception), "Cannot create secret without specifying name and secret-string")

    def test_update_secret_success(self):
        option_list = [
            (Mock(spec=['name'], name="secret_id"), "secret-123"),
            (Mock(spec=['name'], name="name"), "UpdatedSecret"),
            (Mock(spec=['name'], name="secret_string"), "updated-value")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.core.secrets.clients.SecretClient.update_secret', return_value="Updated secret") as mock_update:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_secret(option_list)
                mock_update.assert_called_once()
                mock_stdout.assert_called_once_with("Update secret result: \nUpdated secret")

    def test_update_secret_missing_id(self):
        option_list = [
            (Mock(spec=['name'], name="name"), "UpdatedSecret")
        ]
        option_list[0][0].name = "name"

        with self.assertRaises(MissingRequirementException) as context:
            update_secret(option_list)
        self.assertEqual(str(context.exception), "Cannot update secret without specifying secret-id, name, and secret-string")

    def test_list_secrets_success(self):
        option_list = []

        with patch('pygeai.core.secrets.clients.SecretClient.list_secrets', return_value="Secrets list") as mock_list:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                list_secrets(option_list)
                mock_list.assert_called_once_with(name=None, id=None, start=0, count=10)
                mock_stdout.assert_called_once_with("List secrets result: \nSecrets list")

    def test_set_secret_accesses_success(self):
        option_list = [
            (Mock(spec=['name'], name="secret_id"), "secret-123"),
            (Mock(spec=['name'], name="access_list"), '[{"project_id": "project-456"}]')
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name

        with patch('pygeai.core.secrets.clients.SecretClient.set_secret_accesses', return_value="Access set") as mock_set:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                set_secret_accesses(option_list)
                mock_set.assert_called_once()
                mock_stdout.assert_called_once_with("Set secret accesses result: \nAccess set")

    def test_set_secret_accesses_missing_secret_id(self):
        option_list = [
            (Mock(spec=['name'], name="project_id"), "project-456")
        ]
        option_list[0][0].name = "project_id"

        with self.assertRaises(MissingRequirementException) as context:
            set_secret_accesses(option_list)
        self.assertEqual(str(context.exception), "Cannot set secret accesses without specifying secret-id and access-list")

    def test_set_secret_accesses_missing_project_id(self):
        option_list = [
            (Mock(spec=['name'], name="secret_id"), "secret-123")
        ]
        option_list[0][0].name = "secret_id"

        with self.assertRaises(MissingRequirementException) as context:
            set_secret_accesses(option_list)
        self.assertEqual(str(context.exception), "Cannot set secret accesses without specifying secret-id and access-list")

    def test_get_secret_accesses_success(self):
        option_list = [
            (Mock(spec=['name'], name="secret_id"), "secret-123")
        ]
        option_list[0][0].name = "secret_id"

        with patch('pygeai.core.secrets.clients.SecretClient.get_secret_accesses', return_value="Access list") as mock_get:
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_secret_accesses(option_list)
                mock_get.assert_called_once_with(secret_id="secret-123")
                mock_stdout.assert_called_once_with("Get secret accesses result: \nAccess list")

    def test_get_secret_accesses_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_secret_accesses(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve secret accesses without specifying secret-id")


if __name__ == '__main__':
    unittest.main()
