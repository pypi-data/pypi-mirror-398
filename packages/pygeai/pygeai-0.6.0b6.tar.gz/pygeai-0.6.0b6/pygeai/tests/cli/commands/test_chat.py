import unittest
from unittest.mock import patch, MagicMock
from pygeai.cli.commands.chat import show_help, get_chat_completion, chat_with_iris, chat_with_agent
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.cli.commands import Option


class TestChatCommands(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_chat.TestChatCommands
    """

    @patch('pygeai.cli.commands.chat.ChatClient')
    @patch('pygeai.cli.commands.common.get_messages')
    def test_get_chat_completion_success(self, mock_get_messages, mock_chat_client):
        mock_instance = mock_chat_client.return_value
        mock_instance.chat_completion.return_value = "Chat response"
        mock_get_messages.return_value = [{"role": "user", "content": "Hello"}]

        option_list = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("messages", ["--messages"], "", True), '{"role": "user", "content": "Hello"}')
        ]

        get_chat_completion(option_list)
        mock_chat_client.assert_called_once()
        mock_instance.chat_completion.assert_called_once()

    def test_get_chat_completion_missing_requirements(self):
        option_list = [
            (Option("model", ["--model"], "", True), "test-model")
        ]
        with self.assertRaises(MissingRequirementException):
            get_chat_completion(option_list)

    def test_get_chat_completion_invalid_messages_format(self):
        option_list = [
            (Option("model", ["--model"], "", True), "test-model"),
            (Option("messages", ["--messages"], "", True), "invalid-json")
        ]
        with self.assertRaises(WrongArgumentError):
            get_chat_completion(option_list)

    @patch('pygeai.cli.commands.chat.Iris')
    @patch('prompt_toolkit.PromptSession.prompt')
    def test_chat_with_iris_success(self, mock_prompt, mock_iris):
        mock_prompt.side_effect = ["Hello", "exit"]
        mock_iris_instance = mock_iris.return_value
        mock_iris_instance.stream_answer.return_value = iter(["Hi there!"])

        chat_with_iris()
        mock_iris.assert_called_once()
        mock_iris_instance.stream_answer.assert_called()

    @patch('pygeai.cli.commands.chat.get_project_id')
    @patch('pygeai.cli.commands.chat.AgentClient')
    @patch('pygeai.cli.commands.chat.AgentChatSession')
    @patch('prompt_toolkit.PromptSession.prompt')
    def test_chat_with_agent_success(self, mock_prompt, mock_agent_session, mock_agent_client, mock_get_project_id):
        mock_prompt.side_effect = ["Hello", "exit"]
        mock_session_instance = mock_agent_session.return_value
        mock_session_instance.get_answer.return_value = "Hello, I'm your agent!"
        mock_session_instance.stream_answer.return_value = iter(["Hi there!"])
        
        mock_get_project_id.return_value = "test-project-id"
        mock_client_instance = mock_agent_client.return_value
        mock_client_instance.get_agent.return_value = {"agentId": "123", "agentName": "test-agent"}

        option_list = [
            (Option("agent_name", ["--agent-name"], "", True), "test-agent")
        ]

        chat_with_agent(option_list)
        mock_agent_session.assert_called_once_with("test-agent")
        mock_session_instance.stream_answer.assert_called()

    def test_chat_with_agent_missing_agent_name(self):
        option_list = []
        with self.assertRaises(MissingRequirementException):
            chat_with_agent(option_list)

    @patch('pygeai.cli.commands.chat.get_project_id')
    @patch('pygeai.cli.commands.chat.AgentClient')
    @patch('pygeai.cli.commands.chat.AgentChatSession')
    @patch('prompt_toolkit.PromptSession.prompt')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.load')
    def test_chat_with_agent_restore_session_success(self, mock_json_load, mock_open, mock_prompt, mock_agent_session, mock_agent_client, mock_get_project_id):
        mock_prompt.side_effect = ["Hello", "exit"]
        mock_session_instance = mock_agent_session.return_value
        mock_session_instance.get_answer.return_value = "Hello, I'm your agent!"
        mock_session_instance.stream_answer.return_value = iter(["Hi there!"])
        mock_json_load.return_value = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello!"}]
        
        mock_get_project_id.return_value = "test-project-id"
        mock_client_instance = mock_agent_client.return_value
        mock_client_instance.get_agent.return_value = {"agentId": "123", "agentName": "test-agent"}

        option_list = [
            (Option("agent_name", ["--agent-name"], "", True), "test-agent"),
            (Option("restore_session", ["--restore-session"], "", True), "session.json")
        ]

        chat_with_agent(option_list)
        mock_json_load.assert_called_once()

    @patch('pygeai.cli.commands.chat.get_project_id')
    @patch('pygeai.cli.commands.chat.AgentClient')
    @patch('pygeai.cli.commands.chat.AgentChatSession')
    @patch('prompt_toolkit.PromptSession.prompt')
    @patch('builtins.open', new_callable=MagicMock)
    @patch('json.dump')
    def test_chat_with_agent_save_session_success(self, mock_json_dump, mock_open, mock_prompt, mock_agent_session, mock_agent_client, mock_get_project_id):
        mock_prompt.side_effect = ["Hello", "exit"]
        mock_session_instance = mock_agent_session.return_value
        mock_session_instance.get_answer.return_value = "Hello, I'm your agent!"
        mock_session_instance.stream_answer.return_value = iter(["Hi there!"])
        
        mock_get_project_id.return_value = "test-project-id"
        mock_client_instance = mock_agent_client.return_value
        mock_client_instance.get_agent.return_value = {"agentId": "123", "agentName": "test-agent"}

        option_list = [
            (Option("agent_name", ["--agent-name"], "", True), "test-agent"),
            (Option("save_session", ["--save-session"], "", True), "session.json")
        ]

        chat_with_agent(option_list)
        mock_json_dump.assert_called()

