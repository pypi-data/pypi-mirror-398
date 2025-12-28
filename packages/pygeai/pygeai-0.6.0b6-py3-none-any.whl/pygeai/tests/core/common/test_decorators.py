import unittest
import io
import sys
from unittest.mock import patch
from pygeai.core.common.decorators import measure_execution_time, handler_server_error
from pygeai.core.common.exceptions import ServerResponseError


class TestDecorators(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.common.test_decorators.TestDecorators
    """

    def test_measure_execution_time_success(self):
        @measure_execution_time
        def sample_function():
            return "Success"

        # Capture stdout to verify printed messages
        captured_output = io.StringIO()
        sys.stdout = captured_output

        result = sample_function()

        sys.stdout = sys.__stdout__  # Restore stdout
        output = captured_output.getvalue()
        self.assertIn("Measuring execution time for: sample_function", output)
        self.assertIn("Function sample_function executed in", output)
        self.assertEqual(result, "Success")

    def test_measure_execution_time_with_exception(self):
        @measure_execution_time
        def failing_function():
            raise ValueError("Test error")

        # Capture stdout to verify printed messages
        captured_output = io.StringIO()
        sys.stdout = captured_output

        result = None
        try:
            result = failing_function()
        except ValueError:
            pass  # The decorator catches the exception, so this won't be reached

        sys.stdout = sys.__stdout__  # Restore stdout
        output = captured_output.getvalue()
        self.assertIn("Measuring execution time for: failing_function", output)
        self.assertIn("Error measuring execution time: Test error", output)
        self.assertIsNone(result)  # No return value since exception was caught

    def test_handler_server_error_no_error(self):
        @handler_server_error
        def successful_function():
            return {"data": "Success"}

        result = successful_function()
        self.assertEqual(result, {"data": "Success"})

    def test_handler_server_error_with_error(self):
        @handler_server_error
        def error_function():
            return {"error": "Server error message"}

        with self.assertRaises(ServerResponseError) as context:
            error_function()

        self.assertIn("There was an error communicating with the server: Server error message", str(context.exception))

