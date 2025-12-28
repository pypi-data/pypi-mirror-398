import unittest
from unittest.mock import patch, Mock

from pygeai.cli.commands.assistant import (
    show_help,
    get_assistant_detail,
    create_assistant,
    update_assistant,
    delete_assistant,
    send_chat_request,
    get_request_status,
    cancel_request
)
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError


class TestAssistant(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_assistant.TestAssistant
    """
    def test_show_help(self):
        with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
            show_help()
            mock_stdout.assert_called_once()

    def test_get_assistant_detail_success(self):
        option_list = [
            (Mock(spec=['name'], name="detail"), "full"),
            (Mock(spec=['name'], name="assistant_id"), "123")
        ]
        option_list[0][0].name = "detail"
        option_list[1][0].name = "assistant_id"
        with patch('pygeai.assistant.clients.AssistantClient.get_assistant_data', return_value="Assistant data"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_assistant_detail(option_list)
                mock_stdout.assert_called_once_with("Assistant detail: \nAssistant data")

    def test_get_assistant_detail_missing_id(self):
        option_list = [(Mock(spec=['name'], name="detail"), "full")]
        option_list[0][0].name = "detail"
        with self.assertRaises(MissingRequirementException) as context:
            get_assistant_detail(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve assistant detail without assistant_id")

    def test_create_assistant_success(self):
        option_list = [
            (Mock(spec=['name'], name="type"), "text"),
            (Mock(spec=['name'], name="name"), "Test Assistant"),
            (Mock(spec=['name'], name="prompt"), "Test prompt"),
            (Mock(spec=['name'], name="description"), "Description"),
            (Mock(spec=['name'], name="provider_name"), "provider"),
            (Mock(spec=['name'], name="model_name"), "model"),
            (Mock(spec=['name'], name="temperature"), "0.5"),
            (Mock(spec=['name'], name="max_tokens"), "100"),
            (Mock(spec=['name'], name="welcome_data_title"), "Welcome"),
            (Mock(spec=['name'], name="welcome_data_description"), "Welcome description")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with patch('pygeai.assistant.clients.AssistantClient.create_assistant', return_value="Created assistant"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                with patch('pygeai.cli.commands.common.get_llm_settings', return_value={"provider": "provider"}):
                    with patch('pygeai.cli.commands.common.get_welcome_data', return_value={"title": "Welcome"}):
                        create_assistant(option_list)
                        mock_stdout.assert_called_once_with("New assistant detail: \nCreated assistant")

    def test_create_assistant_missing_required(self):
        option_list = [(Mock(spec=['name'], name="type"), "text")]
        option_list[0][0].name = "type"
        with self.assertRaises(MissingRequirementException) as context:
            create_assistant(option_list)
        self.assertEqual(str(context.exception), "Cannot create new assistant without 'type', 'name' and 'prompt'")

    def test_create_assistant_invalid_temperature(self):
        option_list = [
            (Mock(spec=['name'], name="type"), "text"),
            (Mock(spec=['name'], name="name"), "Test Assistant"),
            (Mock(spec=['name'], name="prompt"), "Test prompt"),
            (Mock(spec=['name'], name="temperature"), "invalid")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with self.assertRaises(WrongArgumentError) as context:
            create_assistant(option_list)
        self.assertEqual(str(context.exception), "When defined, temperature must be a decimal numer. Example: 0.5")

    def test_update_assistant_success(self):
        option_list = [
            (Mock(spec=['name'], name="assistant_id"), "123"),
            (Mock(spec=['name'], name="name"), "Updated Assistant"),
            (Mock(spec=['name'], name="prompt"), "Updated prompt"),
            (Mock(spec=['name'], name="action"), "saveNewRevision")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with patch('pygeai.assistant.clients.AssistantClient.update_assistant', return_value="Updated assistant"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                update_assistant(option_list)
                mock_stdout.assert_called_once_with("Updated assistant detail: \nUpdated assistant")

    def test_update_assistant_missing_id(self):
        option_list = [(Mock(spec=['name'], name="name"), "Updated Assistant")]
        option_list[0][0].name = "name"
        with self.assertRaises(MissingRequirementException) as context:
            update_assistant(option_list)
        self.assertEqual(str(context.exception), "Cannot update existing assistant without 'assistant_id'")

    def test_update_assistant_missing_revision_id_for_save(self):
        option_list = [
            (Mock(spec=['name'], name="assistant_id"), "123"),
            (Mock(spec=['name'], name="action"), "save")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with self.assertRaises(MissingRequirementException) as context:
            update_assistant(option_list)
        self.assertEqual(str(context.exception), "A revision_id is necessary when updating an existing version.")

    def test_update_assistant_missing_prompt_for_new_revision(self):
        option_list = [
            (Mock(spec=['name'], name="assistant_id"), "123"),
            (Mock(spec=['name'], name="action"), "saveNewRevision")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with self.assertRaises(MissingRequirementException) as context:
            update_assistant(option_list)
        self.assertEqual(str(context.exception), "Prompt must be defined if revisionId is specified or in case of actions saveNewRevision and savePublishNewRevision.")

    def test_delete_assistant_success(self):
        option_list = [(Mock(spec=['name'], name="assistant_id"), "123")]
        option_list[0][0].name = "assistant_id"
        with patch('pygeai.assistant.clients.AssistantClient.delete_assistant', return_value="Deleted assistant"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                delete_assistant(option_list)
                mock_stdout.assert_called_once_with("Deleted assistant: \nDeleted assistant")

    def test_delete_assistant_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            delete_assistant(option_list)
        self.assertEqual(str(context.exception), "Cannot delete assistant without 'assistant_id'")

    def test_send_chat_request_success(self):
        option_list = [
            (Mock(spec=['name'], name="assistant_name"), "Test Assistant"),
            (Mock(spec=['name'], name="messages"), '{"role": "user", "content": "Hello"}')
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with patch('pygeai.assistant.clients.AssistantClient.send_chat_request', return_value="Chat response"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                with patch('pygeai.cli.commands.common.get_messages', return_value=[{"role": "user", "content": "Hello"}]):
                    send_chat_request(option_list)
                    mock_stdout.assert_called_once_with("Chat request response: \nChat response")

    def test_send_chat_request_missing_name(self):
        option_list = [(Mock(spec=['name'], name="messages"), '{"role": "user", "content": "Hello"}')]
        option_list[0][0].name = "messages"
        with self.assertRaises(MissingRequirementException) as context:
            send_chat_request(option_list)
        self.assertEqual(str(context.exception), "Cannot send chat request without specifying assistant name")

    def test_send_chat_request_invalid_messages(self):
        option_list = [
            (Mock(spec=['name'], name="assistant_name"), "Test Assistant"),
            (Mock(spec=['name'], name="messages"), "invalid_json")
        ]
        for opt, _ in option_list:
            opt.name = opt._mock_name
        with self.assertRaises(WrongArgumentError) as context:
            send_chat_request(option_list)
        self.assertIn("Each message must be in json format", str(context.exception))

    def test_get_request_status_success(self):
        option_list = [(Mock(spec=['name'], name="request_id"), "456")]
        option_list[0][0].name = "request_id"
        with patch('pygeai.assistant.clients.AssistantClient.get_request_status', return_value="Request status data"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                get_request_status(option_list)
                mock_stdout.assert_called_once_with("Request status: \nRequest status data")

    def test_get_request_status_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            get_request_status(option_list)
        self.assertEqual(str(context.exception), "Cannot retrieve status of request without request_id.")

    def test_cancel_request_success(self):
        option_list = [(Mock(spec=['name'], name="request_id"), "456")]
        option_list[0][0].name = "request_id"
        with patch('pygeai.assistant.clients.AssistantClient.cancel_request', return_value="Request cancelled"):
            with patch('pygeai.core.utils.console.Console.write_stdout') as mock_stdout:
                cancel_request(option_list)
                mock_stdout.assert_called_once_with("Cancel request detail: \nRequest cancelled")

    def test_cancel_request_missing_id(self):
        option_list = []
        with self.assertRaises(MissingRequirementException) as context:
            cancel_request(option_list)
        self.assertEqual(str(context.exception), "Cannot cancel request without request_id.")

