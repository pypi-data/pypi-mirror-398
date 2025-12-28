from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, ToolParameter
from pygeai.core.common.exceptions import APIResponseError, MissingRequirementException
import copy

ai_lab_manager: AILabManager

class TestAILabGetParameterIntegration(TestCase):   

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.tool_id = "42610b61-cb47-49bf-9475-36ee652f31f3"
        self.filter_settings = FilterSettings(
            revision="0",
            version="0",
            allow_drafts=True
        )


    def __get_parameter(self, tool_id: str = None, tool_public_name: str = None, filter_settings: FilterSettings = None):
        return self.ai_lab_manager.get_parameter(
            tool_id=self.tool_id if tool_id is None else tool_id,
            tool_public_name=tool_public_name,
            filter_settings=self.filter_settings if filter_settings is None else filter_settings
        )   
    

    def test_get_parameter(self):
        tool_parameters = self.__get_parameter()
       
        for param in tool_parameters:
            self.assertIsInstance(param, ToolParameter, "Expected a tool parameter")
 

    def test_get_parameter_invalid_tool_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"

        with self.assertRaises(APIResponseError) as exception:
            self.__get_parameter(tool_id=invalid_id)
        self.assertIn(
            f"Tool not found [IdOrName= {invalid_id}]",
            str(exception.exception),
            "Expected error when trying to send an invalid tool id"
        )

  
    def test_get_parameter_no_tool_id(self):
        with self.assertRaises(MissingRequirementException) as exception:
            self.__get_parameter(tool_id="")
        self.assertIn(
            "Either tool_id or tool_public_name must be provided.",
            str(exception.exception),
            "Expected error when trying to send a request without tool_id"
        )


    def test_get_parameter_by_tool_public_name(self):
        tool_parameters = self.__get_parameter(tool_public_name="test.sdk.beta.tool")

        for param in tool_parameters:
            self.assertIsInstance(param, ToolParameter, "Expected a tool parameter")


    def test_get_parameter_by_invalid_public_name(self):
        invalid_public_name = "test.sdk.beta.tool.invalid"

        with self.assertRaises(APIResponseError) as exception:
            self.__get_parameter(tool_public_name=invalid_public_name)
        self.assertIn(
             f"Tool not found [IdOrName= {invalid_public_name}]",
            str(exception.exception),
            "Expected error when trying to send a request without tool_id"
        )


    def test_get_parameter_by_past_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = "3"

        with self.assertRaises(APIResponseError) as exception:
            self.__get_parameter(filter_settings=filter_settings)
        self.assertIn(
            "Requested revision not found [revision=3].",
            str(exception.exception),
            "Expected error when trying to send a request without tool_id"
        )

    
    def test_get_parameter_by_draft_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = "10"
        tool_parameters = self.__get_parameter(filter_settings=filter_settings)

        for param in tool_parameters:
            self.assertIsInstance(param, ToolParameter, "Expected a tool parameter")

    