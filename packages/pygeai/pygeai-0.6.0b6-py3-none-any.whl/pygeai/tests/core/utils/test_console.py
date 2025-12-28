import unittest
from unittest import TestCase
from unittest.mock import MagicMock
from pygeai.core.utils.console import Console, StreamWriter


class TestConsole(TestCase):
    """
    python -m unittest pygeai.tests.core.utils.test_console.TestConsole
    """

    def setUp(self):
        # Reset the Console writer to a mock before each test
        self.mock_writer = MagicMock(spec=StreamWriter)
        Console.set_writer(self.mock_writer)

    def test_write_stdout_default(self):
        message = "Test message"
        Console.write_stdout(message)
        self.mock_writer.write_stdout.assert_called_once_with(message, "\n")

    def test_write_stdout_custom_end(self):
        message = "Test message"
        custom_end = " "
        Console.write_stdout(message, end=custom_end)
        self.mock_writer.write_stdout.assert_called_once_with(message, custom_end)

    def test_write_stderr_default(self):
        message = "Error message"
        Console.write_stderr(message)
        self.mock_writer.write_stderr.assert_called_once_with(message, "\n")

    def test_write_stderr_custom_end(self):
        message = "Error message"
        custom_end = " "
        Console.write_stderr(message, end=custom_end)
        self.mock_writer.write_stderr.assert_called_once_with(message, custom_end)

    def test_set_writer(self):
        new_writer = MagicMock(spec=StreamWriter)
        Console.set_writer(new_writer)
        Console.write_stdout("Test")
        new_writer.write_stdout.assert_called_once_with("Test", "\n")

    def test_console_meta_getattr_valid_method(self):
        # Test that a valid method from the writer is accessible via Console
        self.mock_writer.test_method = MagicMock()
        method = getattr(Console, "test_method")
        method("arg1", kwarg="value")
        self.mock_writer.test_method.assert_called_once_with("arg1", kwarg="value")

    def test_console_meta_getattr_invalid_method(self):
        # Test that accessing a non-existent method returns a noop function
        noop_method = getattr(Console, "non_existent_method")
        result = noop_method("arg1", kwarg="value")
        self.assertIsNone(result)
        self.mock_writer.write_stdout.assert_not_called()
        self.mock_writer.write_stderr.assert_not_called()

    def test_default_stream_writer_stdout(self):
        # Test the DefaultStreamWriter directly (though not typically used in isolation)
        from io import StringIO
        import sys
        default_writer = Console.DefaultStreamWriter()
        captured_output = StringIO()
        sys.stdout = captured_output
        default_writer.write_stdout("Default test", end=" ")
        sys.stdout = sys.__stdout__  # Restore stdout
        self.assertEqual(captured_output.getvalue(), "Default test ")

    def test_default_stream_writer_stderr(self):
        # Test the DefaultStreamWriter directly for stderr
        from io import StringIO
        import sys
        default_writer = Console.DefaultStreamWriter()
        captured_output = StringIO()
        sys.stderr = captured_output
        default_writer.write_stderr("Default error", end=" ")
        sys.stderr = sys.__stderr__  # Restore stderr
        self.assertEqual(captured_output.getvalue(), "Default error ")