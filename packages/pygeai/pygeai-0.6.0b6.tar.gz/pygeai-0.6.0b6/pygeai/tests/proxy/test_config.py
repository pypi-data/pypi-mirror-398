import unittest
from unittest.mock import patch, MagicMock
import uuid
import os
from pygeai.proxy.config import ProxySettingsManager


class TestProxySettingsManager(unittest.TestCase):
    """
    python -m unittest pygeai.tests.proxy.test_config.TestProxySettingsManager
    """

    def setUp(self):
        """Set up test fixtures."""
        patcher = patch('pygeai.core.common.config.SettingsManager.__init__', lambda x: None)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.settings = ProxySettingsManager()
        self.settings.config = MagicMock()  # Mock configparser
        self.test_uuid = uuid.uuid4()
        self.test_alias = "test_alias"

    def test_default_alias(self):
        self.assertEqual(self.settings.DEFAULT_ALIAS, "default")
        self.assertEqual(self.settings.get_current_alias(), "default")

    def test_set_current_alias(self):
        self.settings.set_current_alias(self.test_alias)
        self.assertEqual(self.settings.get_current_alias(), self.test_alias)

    def test_get_proxy_id_none(self):
        self.settings.get_setting_value = MagicMock(return_value=None)
        result = self.settings.get_proxy_id()
        self.assertIsNone(result)

    def test_set_and_get_proxy_id(self):
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=str(self.test_uuid))
        self.settings.set_proxy_id(self.test_uuid)
        result = self.settings.get_proxy_id()
        self.assertEqual(result, self.test_uuid)

    def test_set_and_get_proxy_id_with_alias(self):
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=str(self.test_uuid))
        self.settings.set_proxy_id(self.test_uuid, self.test_alias)
        result = self.settings.get_proxy_id(self.test_alias)
        self.assertEqual(result, self.test_uuid)

    def test_get_proxy_name_none(self):
        self.settings.get_setting_value = MagicMock(return_value=None)
        result = self.settings.get_proxy_name()
        self.assertIsNone(result)

    def test_set_and_get_proxy_name(self):
        test_name = "Test Proxy"
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=test_name)
        self.settings.set_proxy_name(test_name)
        result = self.settings.get_proxy_name()
        self.assertEqual(result, test_name)

    def test_set_and_get_proxy_name_with_alias(self):
        test_name = "Test Proxy"
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=test_name)
        self.settings.set_proxy_name(test_name, self.test_alias)
        result = self.settings.get_proxy_name(self.test_alias)
        self.assertEqual(result, test_name)

    def test_get_proxy_description_none(self):
        self.settings.get_setting_value = MagicMock(return_value=None)
        result = self.settings.get_proxy_description()
        self.assertIsNone(result)

    def test_set_and_get_proxy_description(self):
        test_description = "Test Description"
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=test_description)
        self.settings.set_proxy_description(test_description)
        result = self.settings.get_proxy_description()
        self.assertEqual(result, test_description)

    def test_set_and_get_proxy_description_with_alias(self):
        test_description = "Test Description"
        self.settings.set_setting_value = MagicMock()
        self.settings.get_setting_value = MagicMock(return_value=test_description)
        self.settings.set_proxy_description(test_description, self.test_alias)
        result = self.settings.get_proxy_description(self.test_alias)
        self.assertEqual(result, test_description)

    def test_get_proxy_affinity_default(self):
        self.settings.has_value = MagicMock(return_value=False)
        result = self.settings.get_proxy_affinity()
        self.assertEqual(result, uuid.UUID(int=0))

    def test_set_and_get_proxy_affinity(self):
        self.settings.set_setting_value = MagicMock()
        self.settings.has_value = MagicMock(return_value=True)
        self.settings.get_setting_value = MagicMock(return_value=str(self.test_uuid))
        self.settings.set_proxy_affinity(self.test_uuid)
        result = self.settings.get_proxy_affinity()
        self.assertEqual(result, self.test_uuid)

    def test_set_and_get_proxy_affinity_with_alias(self):
        self.settings.set_setting_value = MagicMock()
        self.settings.has_value = MagicMock(return_value=True)
        self.settings.get_setting_value = MagicMock(return_value=str(self.test_uuid))
        self.settings.set_proxy_affinity(self.test_uuid, self.test_alias)
        result = self.settings.get_proxy_affinity(self.test_alias)
        self.assertEqual(result, self.test_uuid)

    @patch.dict(os.environ, {'PROXY_ID': 'test-uuid'})
    def test_get_setting_value_from_env(self):
        result = self.settings.get_setting_value("PROXY_ID", "default")
        self.assertEqual(result, 'test-uuid')

    @patch.dict(os.environ, {'PROXY_NAME': 'test-name'})
    def test_get_setting_value_from_env_with_alias(self):
        result = self.settings.get_setting_value("PROXY_NAME", "custom_alias")
        self.assertIsNone(result)

    def test_get_proxy_config(self):
        test_name = "Test Proxy"
        test_description = "Test Description"
        self.settings.get_proxy_id = MagicMock(return_value=self.test_uuid)
        self.settings.get_proxy_name = MagicMock(return_value=test_name)
        self.settings.get_proxy_description = MagicMock(return_value=test_description)
        self.settings.get_proxy_affinity = MagicMock(return_value=self.test_uuid)
        result = self.settings.get_proxy_config()
        expected = {
            "id": str(self.test_uuid),
            "name": test_name,
            "description": test_description,
            "affinity": str(self.test_uuid)
        }
        self.assertEqual(result, expected)

    def test_get_proxy_config_with_alias(self):
        test_name = "Test Proxy"
        test_description = "Test Description"
        self.settings.get_proxy_id = MagicMock(return_value=self.test_uuid)
        self.settings.get_proxy_name = MagicMock(return_value=test_name)
        self.settings.get_proxy_description = MagicMock(return_value=test_description)
        self.settings.get_proxy_affinity = MagicMock(return_value=self.test_uuid)
        result = self.settings.get_proxy_config(self.test_alias)
        expected = {
            "id": str(self.test_uuid),
            "name": test_name,
            "description": test_description,
            "affinity": str(self.test_uuid)
        }
        self.assertEqual(result, expected)

    def test_get_proxy_config_with_none_values(self):
        self.settings.get_proxy_id = MagicMock(return_value=None)
        self.settings.get_proxy_name = MagicMock(return_value=None)
        self.settings.get_proxy_description = MagicMock(return_value=None)
        self.settings.get_proxy_affinity = MagicMock(return_value=uuid.UUID(int=0))
        result = self.settings.get_proxy_config()
        expected = {
            "id": None,
            "name": None,
            "description": None,
            "affinity": str(uuid.UUID(int=0))
        }
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 