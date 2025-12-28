from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool
from pygeai.core.common.exceptions import APIResponseError, MissingRequirementException, InvalidAPIResponseException

ai_lab_manager: AILabManager

class TestAILabDeleteToolIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        

    def __create_tool(self):
        """
        Helper to create a tool
        """
        tool = Tool(
            name=str(uuid.uuid4()),
            description="Agent that translates from any language to english.",
            scope="builtin"
        )


        return self.ai_lab_manager.create_tool(
            tool=tool
        )

    def __delete_tool(self, tool_id: str = None, tool_name: str = None):
        return self.ai_lab_manager.delete_tool(tool_id=tool_id, tool_name=tool_name)
    

    def test_delete_tool_by_id(self):         
        created_tool = self.__create_tool()     
        deleted_tool = self.__delete_tool(tool_id=created_tool.id)

        self.assertEqual(
            deleted_tool.content,
            "Tool deleted successfully",
            "Expected confirmation message after deletion"            
        )


    def test_delete_tool_by_name(self):         
        created_tool = self.__create_tool()     
        deleted_tool = self.__delete_tool(tool_name=created_tool.name)

        self.assertEqual(
            deleted_tool.content,
            "Tool deleted successfully",
            "Expected confirmation message after deletion"            
        )


    def test_delete_tool_no_id_nor_name(self):
        with self.assertRaises(MissingRequirementException) as exception:
            self.__delete_tool()   
        self.assertIn(
            "Either tool_id or tool_name must be provided",
            str(exception.exception),
            "Expected error message when neither tool_id nor tool_name is provided"
        )


    def test_delete_tool_invalid_id_valid_name(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        created_tool = self.__create_tool() 
        with self.assertRaises(APIResponseError) as exception:
            self.__delete_tool(tool_name=created_tool.name, tool_id=invalid_id)

        self.assertIn(
            f"Tool not found [IdOrName= {invalid_id}].",
            str(exception.exception),
            "Expected error message for valid tool name and invalid tool id"
        )


    def test_delete_tool_invalid_name_valid_id(self):
        created_tool = self.__create_tool()     
        deleted_tool = self.__delete_tool(tool_id=created_tool.id, tool_name="toolName")
        
        self.assertEqual(
            deleted_tool.content,
            "Tool deleted successfully",
            "Expected confirmation message after deletion"            
        )