import unittest
from unittest.mock import MagicMock

from pygeai.core.base.responses import ErrorListResponse, EmptyResponse
from pygeai.core.base.models import Error


class TestCoreBaseResponses(unittest.TestCase):
    """
    python -m unittest pygeai.tests.core.base.test_responses.TestCoreBaseResponses
    """

    def test_error_list_response_to_dict(self):
        error1 = MagicMock(spec=Error)
        error1.to_dict.return_value = {"code": "E001", "message": "Error 1"}
        error2 = MagicMock(spec=Error)
        error2.to_dict.return_value = {"code": "E002", "message": "Error 2"}
        
        response = ErrorListResponse(errors=[error1, error2])
        result = response.to_dict()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], {"code": "E001", "message": "Error 1"})
        self.assertEqual(result[1], {"code": "E002", "message": "Error 2"})

    def test_empty_response_with_dict_content(self):
        response = EmptyResponse(content={"key": "value"})
        result = response.to_dict()
        
        self.assertEqual(result, {"content": {"key": "value"}})

    def test_empty_response_with_string_content(self):
        response = EmptyResponse(content="test message")
        result = response.to_dict()
        
        self.assertEqual(result, {"content": "test message"})

    def test_empty_response_with_none_content(self):
        response = EmptyResponse(content=None)
        result = response.to_dict()
        
        self.assertEqual(result, {})

    def test_empty_response_str(self):
        response = EmptyResponse(content={"test": "data"})
        result = str(response)
        
        self.assertIn("content", result)
        self.assertIn("test", result)


if __name__ == '__main__':
    unittest.main()
