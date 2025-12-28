from unittest import TestCase
import unittest
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, FilterSettings
from pygeai.core.common.exceptions import APIResponseError
import copy

ai_lab_manager: AILabManager

class TestAILabGetToolIntegration(TestCase):   

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.tool_id = "e3e4d64f-ce52-467e-90a9-aa4d08425e82"
        self.filter_settings = FilterSettings(
            revision="0",
            version="0"
        )

    def __get_tool(self, tool_id=None, filter_settings: FilterSettings = None):
        return self.ai_lab_manager.get_tool(
            tool_id=self.tool_id if tool_id is None else tool_id,
            filter_settings=self.filter_settings if filter_settings is None else filter_settings
        )

    def test_get_tool(self):
        tool = self.__get_tool()
        self.assertIsInstance(tool, Tool, "Expected a tool") 
 

    @unittest.skip("Skipped: Validate that when no tool_id is provided, the complete tool list is returned")
    def test_get_tool_no_tool_id(self):
        with self.assertRaises(Exception) as context:
            self.__get_tool(tool_id="")
         
    
    def test_get_tool_invalid_tool_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(APIResponseError) as context:
            self.__get_tool(tool_id=invalid_id)
        self.assertIn(
            f"Tool not found [IdOrName= {invalid_id}].",
            str(context.exception),
            "Expected an error for invalid tool id"
        )


    def test_get_tool_no_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = None
        tool = self.__get_tool(filter_settings=filter_settings)

        self.assertIsInstance(tool, Tool, "Expected a tool")
        self.assertGreaterEqual(tool.revision, 1, "Expected tool revision to be the latest")

    
    def test_get_tool_by_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = "6"
        tool = self.__get_tool(filter_settings=filter_settings)

        self.assertEqual(6, tool.revision, "Expected agent revision to be 6")


    def test_get_tool_by_earlier_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = "2"
        with self.assertRaises(APIResponseError) as context:
            self.__get_tool(filter_settings=filter_settings)
        self.assertIn(
            f"Requested revision not found [revision={filter_settings.revision}].",
            str(context.exception),
            "Expected an error for revision not found"
        )

    #TODO: The API is returning the version of the tool, but the sdk does not
    def test_get_tool_no_version(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = None
        tool = self.__get_tool(filter_settings=filter_settings)

        self.assertIsInstance(tool, Tool, "Expected a tool") 


    #TODO: The API is returning the version of the tool, but the sdk does not      
    def test_get_tool_by_version(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = "1"
        tool = self.__get_tool(filter_settings=filter_settings)
        
        self.assertIsInstance(tool, Tool, "Expected a tool") 