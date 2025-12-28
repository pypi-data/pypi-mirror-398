import unittest
from unittest import TestCase
import tempfile
import os
from pathlib import Path
from pygeai.lab.spec.loader import JSONLoader
from pygeai.core.common.exceptions import InvalidPathException, InvalidJSONException


class TestJSONLoader(TestCase):
    """
    python -m unittest pygeai.tests.lab.spec.test_loader.TestJSONLoader
    """

    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.valid_file_path = os.path.join(self.temp_dir.name, 'valid_file.json')
        self.invalid_file_path = os.path.join(self.temp_dir.name, 'invalid_file.json')

        # Create valid JSON file
        with open(self.valid_file_path, 'w') as f:
            f.write('{"key": "value"}')

        # Create invalid JSON file
        with open(self.invalid_file_path, 'w') as f:
            f.write('{key: value}')  # Invalid JSON: missing quotes around key

    def tearDown(self):
        # Clean up temporary directory and files
        self.temp_dir.cleanup()

    def test_load_data_valid_json(self):
        """Test loading a valid JSON file."""
        data = JSONLoader.load_data(self.valid_file_path)
        self.assertIsInstance(data, dict)
        self.assertEqual(data, {"key": "value"})

    def test_load_data_invalid_json(self):
        """Test loading an invalid JSON file."""
        with self.assertRaises(InvalidJSONException) as cm:
            JSONLoader.load_data(self.invalid_file_path)
        self.assertIn(f"File {self.invalid_file_path} doesn't contain valid JSON.", str(cm.exception))

    def test_load_data_non_existent_file(self):
        """Test loading a non-existent file."""
        non_existent_path = os.path.join(self.temp_dir.name, 'non_existent.json')
        with self.assertRaises(InvalidPathException) as cm:
            JSONLoader.load_data(non_existent_path)
        self.assertIn(f"File {non_existent_path} doesn't exist", str(cm.exception))

    def test_load_data_empty_file(self):
        """Test loading an empty JSON file."""
        empty_file_path = os.path.join(self.temp_dir.name, 'empty_file.json')
        with open(empty_file_path, 'w') as f:
            f.write('')
        with self.assertRaises(InvalidJSONException) as cm:
            JSONLoader.load_data(empty_file_path)
        self.assertIn(f"File {empty_file_path} doesn't contain valid JSON.", str(cm.exception))