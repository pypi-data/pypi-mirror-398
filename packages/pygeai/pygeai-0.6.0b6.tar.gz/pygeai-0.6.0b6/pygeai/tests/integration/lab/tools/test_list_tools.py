from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ToolList, FilterSettings
import copy

ai_lab_manager: AILabManager

class TestAILabListToolsIntegration(TestCase):    

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.filter_settings = FilterSettings(
            allow_external=False,
            allow_drafts=True,
            access_scope="private"
        )


    def __list_tools(self, filter_settings: FilterSettings = None):
        filter_settings = filter_settings if filter_settings != None else self.filter_settings
        return self.ai_lab_manager.list_tools(filter_settings=filter_settings)
    
    
    def test_private_list_tools(self):
        result = self.__list_tools()
        self.assertIsInstance(result, ToolList , "Expected a list of tools") 

        for tool in result.tools:
            self.assertTrue(tool.access_scope == "private", "Expected all tools to be private")


    def test_public_list_tools(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.access_scope = "public"

        result = self.__list_tools(filter_settings=filter_settings)
        self.assertIsInstance(result, ToolList , "Expected a list of tools") 

        for tool in result.tools:
            self.assertTrue(tool.access_scope == "public", "Expected all tools to be public")

     
    def test_list_tools_small_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 2

        result = self.__list_tools(filter_settings=filter_settings)
        self.assertIsInstance(result, ToolList , "Expected a list of tools") 
        
        self.assertEqual(len(result), 2, "Expected list of tools returned to be 2")  


    def test_list_tools_big_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 500

        result = self.__list_tools(filter_settings=filter_settings)
        self.assertIsInstance(result, ToolList , "Expected a list of tools") 
        
        self.assertLessEqual(len(result), 500, "Expected list of tools returned to be 500 or less")


    def test_list_tools_allowing_draft(self):
        result = self.__list_tools()
        validated = any(tool.is_draft == True for tool in result.tools)        
        self.assertTrue(
            validated,
            "Expected at least one tool to be a draft"
        )

    
    def test_list_tools_no_draft(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = False
        result = self.__list_tools(filter_settings=filter_settings)
        
        validated = any(tool.is_draft == True for tool in result.tools)        
        self.assertFalse(
            validated,
            "Expected no draft tools in the list"
        )


    def test_list_tools_invalid_scope(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.scope = "project"
        
        with self.assertRaises(ValueError) as exception:
           self.__list_tools(filter_settings=filter_settings)

        self.assertIn(
            "Scope must be one of builtin, external, api, proxied.",
            str(exception.exception),                    
            f"The expected error about invalid scope was not returned"
        )


    def test_list_tools_allowing_external(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_external = False
        
        result = self.__list_tools(filter_settings=filter_settings)
        self.assertIsInstance(result, ToolList , "Expected a list of tools") 
        


