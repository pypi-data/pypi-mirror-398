import unittest
from unittest.mock import patch, Mock
import requests
import importlib.metadata

from pygeai.cli.commands.version import get_latest_version, get_installed_version, check_new_version


class TestVersion(unittest.TestCase):
    """
    python -m unittest pygeai.tests.cli.commands.test_version.TestVersion
    """
    def test_get_latest_version_success(self):
        package_name = "test-package"
        mock_response = Mock()
        mock_response.text = '{"info": {"version": "1.2.3"}}'
        mock_response.raise_for_status.return_value = None

        with patch('requests.get', return_value=mock_response):
            result = get_latest_version(package_name)
            self.assertEqual(result, "1.2.3")

    def test_get_latest_version_request_exception(self):
        package_name = "test-package"
        with patch('requests.get', side_effect=requests.RequestException("Connection error")):
            result = get_latest_version(package_name)
            self.assertIsNone(result)

    def test_get_installed_version_success(self):
        package_name = "test-package"
        with patch('importlib.metadata.version', return_value="1.0.0"):
            result = get_installed_version(package_name)
            self.assertEqual(result, "1.0.0")

    def test_get_installed_version_not_installed(self):
        package_name = "test-package"
        with patch('importlib.metadata.version', side_effect=importlib.metadata.PackageNotFoundError):
            result = get_installed_version(package_name)
            self.assertEqual(result, "Not installed")

    def test_get_installed_version_unknown(self):
        package_name = "test-package"
        with patch('importlib.metadata.version', side_effect=ModuleNotFoundError):
            result = get_installed_version(package_name)
            self.assertEqual(result, "Unknown")

    def test_check_new_version_latest_greater(self):
        package_name = "test-package"
        with patch('pygeai.cli.commands.version.get_latest_version', return_value="2.0.0"):
            with patch('pygeai.cli.commands.version.get_installed_version', return_value="1.0.0"):
                result = check_new_version(package_name)
                self.assertIn("There's a new version available: 2.0.0", result)

    def test_check_new_version_same_version(self):
        package_name = "test-package"
        with patch('pygeai.cli.commands.version.get_latest_version', return_value="1.0.0"):
            with patch('pygeai.cli.commands.version.get_installed_version', return_value="1.0.0"):
                result = check_new_version(package_name)
                self.assertIn("You have the latest version 1.0.0", result)

    def test_check_new_version_not_installed(self):
        package_name = "test-package"
        with patch('pygeai.cli.commands.version.get_latest_version', return_value="2.0.0"):
            with patch('pygeai.cli.commands.version.get_installed_version', return_value="Not installed"):
                result = check_new_version(package_name)
                self.assertIn("not installed, but the latest version available is 2.0.0", result)

    def test_check_new_version_unknown_version(self):
        package_name = "test-package"
        with patch('pygeai.cli.commands.version.get_latest_version', return_value="2.0.0"):
            with patch('pygeai.cli.commands.version.get_installed_version', return_value="Unknown"):
                result = check_new_version(package_name)
                self.assertEqual(result, "Could not determine version information.")

    def test_check_new_version_latest_none(self):
        package_name = "test-package"
        with patch('pygeai.cli.commands.version.get_latest_version', return_value=None):
            with patch('pygeai.cli.commands.version.get_installed_version', return_value="1.0.0"):
                result = check_new_version(package_name)
                self.assertEqual(result, "Could not determine version information.")

