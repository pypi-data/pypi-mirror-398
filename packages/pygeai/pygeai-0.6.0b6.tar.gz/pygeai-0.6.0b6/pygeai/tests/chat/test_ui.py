import unittest
import os
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
import streamlit as st
from pygeai.chat.ui import (
    parse_args,
    save_session_to_file,
    get_unique_file_path,
    get_session_file_path,
    list_session_files,
    load_session_from_file,
    delete_session_file,
    get_alias_list,
    get_agent_list,
    save_recent_agents,
    load_recent_agents
)
from pygeai.lab.models import AgentList, Agent


class TestStreamlitChat(unittest.TestCase):
    """
    python -m unittest pygeai.tests.chat.test_ui.TestStreamlitChat
    """

    def setUp(self):
        self.test_dir = "test_chats"
        os.makedirs(self.test_dir, exist_ok=True)
        # Mock streamlit.session_state to handle attribute access
        self.session_state_mock = MagicMock()
        self.session_state_patch = patch('streamlit.session_state', self.session_state_mock)
        self.session_state_patch.start()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for file in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, file))
            os.rmdir(self.test_dir)
        if os.path.exists("recent_agents.json"):
            os.remove("recent_agents.json")
        self.session_state_patch.stop()

    def test_parse_args(self):
        with patch('sys.argv', ['script.py', '--agent-name', 'test-agent']):
            args = parse_args()
            self.assertEqual(args.agent_name, 'test-agent')

    def test_save_session_to_file_success(self):
        messages = [{"role": "user", "content": "Hello"}]
        file_path = os.path.join(self.test_dir, "test_session.json")

        result = save_session_to_file(messages, file_path)
        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data, messages)

    def test_save_session_to_file_failure(self):
        messages = [{"role": "user", "content": "Hello"}]
        file_path = "/invalid/path/test_session.json"

        with patch('pygeai.chat.ui.logger.error') as mock_logger:
            result = save_session_to_file(messages, file_path)
            self.assertFalse(result)
            mock_logger.assert_called()

    def test_get_unique_file_path_no_conflict(self):
        base_path = os.path.join(self.test_dir, "unique.json")
        result = get_unique_file_path(base_path)
        self.assertEqual(result, base_path)

    def test_get_unique_file_path_with_conflict(self):
        base_path = os.path.join(self.test_dir, "conflict.json")
        with open(base_path, 'w') as f:
            f.write("test")
        result = get_unique_file_path(base_path)
        self.assertEqual(result, os.path.join(self.test_dir, "conflict_1.json"))

    def test_get_session_file_path_default(self):
        agent_name = "test-agent"
        current_date = datetime.now().strftime("%Y-%m-%d")
        expected_path = os.path.join("chats", f"chat_session_{agent_name}_{current_date}.json")
        result = get_session_file_path(agent_name)
        self.assertEqual(result, expected_path)

    def test_get_session_file_path_custom(self):
        agent_name = "test-agent"
        custom_filename = "custom_session"
        expected_path = os.path.join("chats", "custom_session.json")
        result = get_session_file_path(agent_name, custom_filename)
        self.assertEqual(result, expected_path)

    def test_list_session_files_empty(self):
        with patch('os.path.exists', return_value=False):
            result = list_session_files()
            self.assertEqual(result, [])

    def test_list_session_files_with_files(self):
        test_file = os.path.join(self.test_dir, "session1.json")
        with open(test_file, 'w') as f:
            f.write("test")
        with patch('os.listdir', return_value=["session1.json", "other.txt"]):
            with patch('os.path.exists', return_value=True):
                result = list_session_files()
                self.assertEqual(result, ["session1.json"])

    def test_load_session_from_file_success(self):
        test_file = os.path.join(self.test_dir, "session.json")
        messages = [{"role": "user", "content": "Hello"}]
        with open(test_file, 'w') as f:
            json.dump(messages, f)
        data, success = load_session_from_file(test_file)
        self.assertTrue(success)
        self.assertEqual(data, messages)

    def test_load_session_from_file_invalid_json(self):
        test_file = os.path.join(self.test_dir, "invalid.json")
        with open(test_file, 'w') as f:
            f.write("invalid json")
        data, success = load_session_from_file(test_file)
        self.assertFalse(success)
        self.assertIsNone(data)

    def test_delete_session_file_success(self):
        test_file = os.path.join(self.test_dir, "delete.json")
        with open(test_file, 'w') as f:
            f.write("test")
        success, message = delete_session_file(test_file)
        self.assertTrue(success)
        self.assertFalse(os.path.exists(test_file))
        self.assertIn("deleted successfully", message)

    def test_delete_session_file_not_found(self):
        test_file = os.path.join(self.test_dir, "nonexistent.json")
        success, message = delete_session_file(test_file)
        self.assertFalse(success)
        self.assertIn("not found", message)

    @patch('pygeai.chat.ui.get_settings')
    def test_get_alias_list_success(self, mock_get_settings):
        mock_settings = MagicMock()
        mock_settings.list_aliases.return_value = {"alias1": {}, "alias2": {}}
        mock_get_settings.return_value = mock_settings
        result = get_alias_list()
        self.assertEqual(result, ["-", "alias1", "alias2"])

    @patch('pygeai.chat.ui.logger')
    def test_save_recent_agents(self, mock_logger):
        # Set up session_state.recent_agents as an attribute on the mock
        self.session_state_mock.recent_agents = []
        save_recent_agents("agent1")
        self.assertEqual(self.session_state_mock.recent_agents, ["agent1"])
        with open("recent_agents.json", "r") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data, ["agent1"])

    @patch('pygeai.chat.ui.logger')
    def test_load_recent_agents_from_file(self, mock_logger):
        with open("recent_agents.json", "w") as f:
            json.dump(["agent1", "agent2"], f)
        # Ensure session_state is initialized before the call
        self.session_state_mock.recent_agents = []
        result = load_recent_agents()
        self.assertEqual(result, ["agent1", "agent2"])
        self.assertEqual(self.session_state_mock.recent_agents, ["agent1", "agent2"])

    def test_get_session_file_path_with_custom_filename(self):
        agent_name = "test-agent"
        custom_filename = "custom_session"
        expected_path = os.path.join("chats", "custom_session.json")

        result = get_session_file_path(agent_name, custom_filename)

        self.assertEqual(result, expected_path)

    def test_list_session_files_with_exception(self):
        with patch('os.path.exists', return_value=True), \
                patch('os.listdir', side_effect=Exception("Access denied")):
            result = list_session_files()

            self.assertEqual(result, [])

    def test_save_recent_agents_with_exception(self):
        self.session_state_mock.recent_agents = []
        new_agent = "agent1"

        with patch('builtins.open', side_effect=Exception("Write error")), \
                patch('pygeai.chat.ui.logger.error') as mock_logger:
            save_recent_agents(new_agent)

            self.assertEqual(self.session_state_mock.recent_agents, ["agent1"])
            mock_logger.assert_called_once()

    def test_load_recent_agents_empty_file(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = load_recent_agents()

            self.assertEqual(result, [])
            self.assertEqual(self.session_state_mock.recent_agents, [])

    @patch('pygeai.chat.ui.get_settings')
    def test_get_alias_list_with_exception(self, mock_get_settings):
        mock_get_settings.side_effect = Exception("Settings error")

        with patch('pygeai.chat.ui.logger.error') as mock_logger:
            result = get_alias_list()

            self.assertEqual(result, ["-"])
            mock_logger.assert_called_once()

    @patch('pygeai.chat.ui.AILabManager')
    def test_get_agent_list_with_exception(self, mock_ai_lab_manager):
        alias = "test_alias"
        project_id = "proj_123"
        mock_ai_lab_manager.side_effect = Exception("Manager error")

        with patch('pygeai.chat.ui.logger.error') as mock_logger:
            result = get_agent_list(alias, project_id)

            self.assertEqual(result, ["-"])
            mock_logger.assert_called_once()