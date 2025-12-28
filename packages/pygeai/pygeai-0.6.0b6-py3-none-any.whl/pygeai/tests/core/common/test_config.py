import unittest
from unittest import TestCase
from unittest.mock import patch, mock_open
import os
from pathlib import Path
from pygeai.core.common.config import SettingsManager, get_settings


class TestSettingsManager(TestCase):
    """
    python -m unittest pygeai.tests.core.common.test_config.TestSettingsManager
    """

    def setUp(self):
        # Mock the credentials file path to use a sample file for testing
        self.sample_creds_path = Path("pygeai/tests/core/common/data/credentials")
        self.creds_content = """
[default]
GEAI_API_KEY = test_api_key
GEAI_API_BASE_URL = https://api.test.com
GEAI_API_EVAL_URL = https://eval.test.com

[alias1]
GEAI_API_KEY = alias1_key
GEAI_API_BASE_URL = https://api.alias1.com
"""
        # Mock file existence and content to avoid touching real filesystem
        self.file_patch = patch('pathlib.Path.exists', return_value=True)
        self.file_patch.start()
        self.open_patch = patch('pathlib.Path.open', mock_open(read_data=self.creds_content))
        self.open_patch.start()
        self.touch_patch = patch('pathlib.Path.touch', return_value=None)
        self.touch_patch.start()

        # Mock configparser read to enforce our test content
        self.config_read_patch = patch('configparser.ConfigParser.read')
        self.mock_config_read = self.config_read_patch.start()
        self.mock_config_read.return_value = None  # We'll set up config manually in tests if needed

        # Mock environment variables to be empty initially
        self.env_patch = patch.dict('os.environ', {}, clear=True)
        self.env_patch.start()

        # Mock sys.stdout.write to capture output
        self.stdout_patch = patch('sys.stdout.write')
        self.mock_stdout = self.stdout_patch.start()

        # Initialize SettingsManager with mocked settings dir and creds file
        self.settings = SettingsManager()

        # Manually set up config with test content for consistency
        self.settings.config.clear()
        self.settings.config.read_string(self.creds_content)

    def tearDown(self):
        self.file_patch.stop()
        self.open_patch.stop()
        self.touch_patch.stop()
        self.env_patch.stop()
        self.stdout_patch.stop()
        self.config_read_patch.stop()

    def test_init_with_existing_file(self):
        self.assertTrue("default" in self.settings.config)
        self.assertTrue("alias1" in self.settings.config)
        self.assertEqual(self.settings.config["default"]["GEAI_API_KEY"], "test_api_key")
        self.mock_stdout.assert_not_called()  # No message since file exists

    def test_init_with_non_existing_file(self):
        with patch('pathlib.Path.exists', return_value=False):
            settings = SettingsManager()
            self.assertEqual(len(settings.config.sections()), 0)  # No sections in empty config
            self.mock_stdout.assert_called()
            self.assertTrue(any("Credentials file not found" in str(call) for call in self.mock_stdout.call_args_list))

    def test_has_value_existing(self):
        result = self.settings.has_value("GEAI_API_KEY", "default")
        self.assertTrue(result)

    def test_has_value_non_existing_key(self):
        result = self.settings.has_value("INVALID_KEY", "default")
        self.assertFalse(result)

    def test_has_value_non_existing_alias(self):
        result = self.settings.has_value("GEAI_API_KEY", "invalid_alias")
        self.assertFalse(result)

    def test_get_setting_value_existing(self):
        value = self.settings.get_setting_value("GEAI_API_KEY", "default")
        self.assertEqual(value, "test_api_key")

    def test_get_setting_value_non_existing_alias(self):
        value = self.settings.get_setting_value("GEAI_API_KEY", "invalid_alias")
        self.assertIsNone(value)

    def test_get_setting_value_non_existing_key(self):
        with patch('sys.stdout.write') as mock_write:
            value = self.settings.get_setting_value("INVALID_KEY", "default")
            self.assertEqual(value, "")
            mock_write.assert_called()
            self.assertIn("'INVALID_KEY' not found in alias 'default'", str(mock_write.call_args))

    def test_get_setting_value_non_existing_key_eval_url(self):
        with patch('sys.stdout.write') as mock_write:
            with patch.object(self.settings, 'set_eval_url') as mock_set_eval:
                value = self.settings.get_setting_value("GEAI_API_EVAL_URL", "default")
                self.assertEqual(value, "https://eval.test.com")  # From mocked content
                mock_write.assert_not_called()  # No message since it's in creds file
                mock_set_eval.assert_not_called()  # Not called since value exists

    def test_set_setting_value_new_alias(self):
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            self.settings.set_setting_value("NEW_KEY", "new_value", "new_alias")
            self.assertTrue("new_alias" in self.settings.config)
            self.assertEqual(self.settings.config["new_alias"]["NEW_KEY"], "new_value")
            mock_file.assert_called_once()

    def test_set_setting_value_existing_alias(self):
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            self.settings.set_setting_value("GEAI_API_KEY", "updated_key", "default")
            self.assertEqual(self.settings.config["default"]["GEAI_API_KEY"], "updated_key")
            mock_file.assert_called_once()

    def test_get_api_key_from_env(self):
        with patch.dict('os.environ', {'GEAI_API_KEY': 'env_api_key'}, clear=True):
            api_key = self.settings.get_api_key("default")
            self.assertEqual(api_key, "env_api_key")

    def test_get_api_key_from_file(self):
        api_key = self.settings.get_api_key("default")
        self.assertEqual(api_key, "test_api_key")

    def test_get_api_key_alias(self):
        api_key = self.settings.get_api_key("alias1")
        self.assertEqual(api_key, "alias1_key")

    def test_set_api_key(self):
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            self.settings.set_api_key("new_api_key", "default")
            self.assertEqual(self.settings.config["default"]["GEAI_API_KEY"], "new_api_key")
            mock_file.assert_called_once()

    def test_get_base_url_from_env(self):
        with patch.dict('os.environ', {'GEAI_API_BASE_URL': 'https://env.test.com'}, clear=True):
            base_url = self.settings.get_base_url("default")
            self.assertEqual(base_url, "https://env.test.com")

    def test_get_base_url_from_file(self):
        base_url = self.settings.get_base_url("default")
        self.assertEqual(base_url, "https://api.test.com")

    def test_get_base_url_alias(self):
        base_url = self.settings.get_base_url("alias1")
        self.assertEqual(base_url, "https://api.alias1.com")

    def test_set_base_url(self):
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            self.settings.set_base_url("https://new.test.com", "default")
            self.assertEqual(self.settings.config["default"]["GEAI_API_BASE_URL"], "https://new.test.com")
            mock_file.assert_called_once()

    def test_get_eval_url_from_env(self):
        with patch.dict('os.environ', {'GEAI_API_EVAL_URL': 'https://env.eval.test.com'}, clear=True):
            eval_url = self.settings.get_eval_url("default")
            self.assertEqual(eval_url, "https://env.eval.test.com")

    def test_get_eval_url_from_file(self):
        eval_url = self.settings.get_eval_url("default")
        self.assertEqual(eval_url, "https://eval.test.com")

    def test_set_eval_url(self):
        with patch('pathlib.Path.open', mock_open()) as mock_file:
            self.settings.set_eval_url("https://new.eval.test.com", "default")
            self.assertEqual(self.settings.config["default"]["GEAI_API_EVAL_URL"], "https://new.eval.test.com")
            mock_file.assert_called_once()

    def test_list_aliases(self):
        aliases = self.settings.list_aliases()
        self.assertEqual(len(aliases), 2)
        self.assertEqual(aliases["default"], "https://api.test.com")
        self.assertEqual(aliases["alias1"], "https://api.alias1.com")

    def test_get_settings_lru_cache(self):
        settings1 = get_settings()
        settings2 = get_settings()
        self.assertIs(settings1, settings2)  # Should return the same instance due to lru_cache
