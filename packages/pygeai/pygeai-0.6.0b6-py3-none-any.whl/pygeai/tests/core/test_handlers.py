import unittest
from unittest.mock import MagicMock
from pygeai.core.handlers import ErrorHandler
from pygeai.core.base.mappers import ErrorMapper


class TestErrorHandler(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.test_handlers.TestErrorHandler
    """

    def setUp(self):
        # Mock the ErrorMapper methods to avoid actual mapping logic in tests
        self.error_mapper_map_to_error_list_response = MagicMock(return_value={"error_list": "mapped_errors"})
        self.error_mapper_map_to_error = MagicMock(return_value={"single_error": "mapped_error"})
        ErrorMapper.map_to_error_list_response = self.error_mapper_map_to_error_list_response
        ErrorMapper.map_to_error = self.error_mapper_map_to_error

    def test_has_errors_with_errors_key(self):
        response = {"errors": [{"code": "123", "message": "Error message"}]}

        result = ErrorHandler.has_errors(response)

        self.assertTrue(result)

    def test_has_errors_with_error_key(self):
        response = {"error": {"code": "456", "message": "Single error"}}

        result = ErrorHandler.has_errors(response)

        self.assertTrue(result)

    def test_has_errors_without_error_keys(self):
        response = {"data": "some data"}

        result = ErrorHandler.has_errors(response)

        self.assertFalse(result)

    def test_extract_error_with_errors_key(self):
        response = {"errors": [{"code": "123", "message": "Error message"}]}

        result = ErrorHandler.extract_error(response)

        self.error_mapper_map_to_error_list_response.assert_called_once_with(response)
        self.assertEqual(result, {"error_list": "mapped_errors"})
        self.error_mapper_map_to_error.assert_not_called()

    def test_extract_error_with_error_key(self):
        response = {"error": {"code": "456", "message": "Single error"}}

        result = ErrorHandler.extract_error(response)

        self.error_mapper_map_to_error.assert_called_once_with(response.get('error'))
        self.assertEqual(result, {"single_error": "mapped_error"})
        self.error_mapper_map_to_error_list_response.assert_not_called()

    def test_extract_error_without_error_keys(self):
        response = {"data": "some data"}

        result = ErrorHandler.extract_error(response)

        self.assertEqual(result, response)
        self.error_mapper_map_to_error_list_response.assert_not_called()
        self.error_mapper_map_to_error.assert_not_called()

