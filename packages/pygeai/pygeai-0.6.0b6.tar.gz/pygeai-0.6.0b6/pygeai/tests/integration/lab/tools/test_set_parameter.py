from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ToolParameter
from pygeai.core.common.exceptions import MissingRequirementException, InvalidAPIResponseException

ai_lab_manager: AILabManager

class TestAILabSetParameterIntegration(TestCase):
    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.tool_id = "42610b61-cb47-49bf-9475-36ee652f31f3"
        self.tool_parameters = self.__load_parameters()


    def __set_parameter(self, tool_id: str = None, tool_public_name: str = None, parameters: list = None):        
        return self.ai_lab_manager.set_parameter(
            tool_id = self.tool_id if tool_id is None else tool_id,
            tool_public_name = tool_public_name,
            parameters = self.tool_parameters if parameters is None else parameters,
        )
    
    
    def __load_parameters(self):
        random_str = str(uuid.uuid4())
        return [
            ToolParameter(
                key="param3",
                data_type="String",
                description=f"{random_str}_config",
                is_required=True,
                type="config",
                value=random_str
            )
        ]
        

    def test_set_parameter(self):  
        result = self.__set_parameter()
        self.assertEqual(
            result.content, 
            "Parameter set successfully",
            "Expected successful parameter update"
        )


    def test_set_parameter_invalid_tool_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.__set_parameter(tool_id=invalid_id)

        self.assertIn(
            f"Unable to set parameter for tool {invalid_id}",
            str(context.exception),
            "Expected error for invalid tool ID"
        )

    
    def test_set_parameter_no_tool_id(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.__set_parameter(tool_id="")

        self.assertIn(
            "Either tool_id or tool_public_name must be provided.",
            str(context.exception),
            "Expected error for invalid tool ID"
        )


    def test_set_parameter_by_tool_public_name(self):
        self.tool_parameters[0].key = "Param1"

        result = self.__set_parameter(tool_id = "", tool_public_name="test.sdk.beta.tool")
        self.assertEqual(
            result.content, 
            "Parameter set successfully",
            "Expected successful parameter update"
        )


    def test_set_parameter_by_invalid_public_name(self):
        invalid_public_name = "test.sdk.beta.tool.invalid"

        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__set_parameter(tool_id = "", tool_public_name=invalid_public_name)
        self.assertIn(
            f"Unable to set parameter for tool {invalid_public_name}",
            str(exception.exception),
            "Expected error when trying to send a request without tool_id"
        )


    def test_set_parameter_no_parameters(self):
        self.tool_parameters = []

        with self.assertRaises(MissingRequirementException) as exception:
            self.__set_parameter()
        self.assertIn(
            "Parameters list must be provided and non-empty.",
            str(exception.exception),
            "Expected error when trying to send a request without parameters"
        )


    def test_set_parameter_not_added_parameters(self):
        #param3 set on self.tool_parameters, does not exist in the public tool
        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__set_parameter(tool_id = "", tool_public_name = "test.sdk.beta.tool")
        self.assertIn(
            "Parameter param3 not found in this tool",
            str(exception.exception),
            "Expected error when trying to send a request without parameters"
        )