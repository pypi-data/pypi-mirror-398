from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, ToolParameter
from pygeai.core.common.exceptions import APIResponseError


class TestAILabCreateToolIntegration(TestCase):    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.new_tool = self.__load_tool()
        self.created_tool: Tool = None


    def tearDown(self):
        """
        Clean up after each test if necessary.
        This can be used to delete the created tool
        """
        if isinstance(self.created_tool, Tool):

            self.ai_lab_manager.delete_tool(self.created_tool.id)

    
    def __load_tool(self):
        return Tool(
            name=str(uuid.uuid4()),
            description="Tool created for sdk testing purposes",
            scope="builtin",
            openApi="https://raw.usercontent.com//openapi.json",
            openApiJson={"openapi": "3.0.0","info": {"title": "Simple API overview","version": "2.0.0"}},
            accessScope="private",
            reportEvents="None",
            parameters=[{"key": "param", "description": "param description", "type":"app", "value":"param value", "data_type": "String", "isRequired": False}],
        )
    

    def __create_tool(self, tool=None, automatic_publish=False):
        """
        Helper to create a tool using ai_lab_manager.
        """
        return self.ai_lab_manager.create_tool(
            tool=self.new_tool if tool is None else tool,
            automatic_publish=automatic_publish
        )


    def test_create_tool_full_data(self):
        self.created_tool = self.__create_tool()
        created_tool = self.created_tool
        tool = self.new_tool
        self.assertTrue(isinstance(created_tool, Tool), "Expected a created tool")

        # Assert the main fields of the created tool
        self.assertIsNotNone(created_tool.id)
        self.assertEqual(created_tool.name, tool.name)
        self.assertEqual(created_tool.description, tool.description)
        self.assertEqual(created_tool.scope, tool.scope)
        self.assertEqual(created_tool.access_scope, tool.access_scope)
        self.assertEqual(created_tool.open_api, tool.open_api)
        self.assertEqual(created_tool.status, "active")

        # Assert agentData fields
        tool_param = created_tool.parameters[0]
        self.assertTrue(isinstance(tool_param, ToolParameter), "Expected parameters to be of type ToolParameter")
        self.assertEqual(tool_param.key, tool.parameters[0].key)
        self.assertEqual(tool_param.data_type, tool.parameters[0].data_type)
        self.assertEqual(tool_param.description, tool.parameters[0].description)
        self.assertEqual(tool_param.is_required, tool.parameters[0].is_required)
        self.assertEqual(tool_param.type, tool.parameters[0].type)
        self.assertEqual(tool_param.value, tool.parameters[0].value)        


    def test_create_tool_minimum_required_data(self):
        self.new_tool = Tool(
            name=str(uuid.uuid4()),
            description="Tool created for sdk testing purposes",
            scope="builtin"
        )
        self.created_tool = self.__create_tool()
        tool = self.new_tool

        self.assertIsNotNone(self.created_tool.id)
        self.assertEqual(self.created_tool.name, tool.name)
        self.assertEqual(self.created_tool.description, tool.description)


    def test_create_tool_without_required_data(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            
            with self.subTest(input=auto_publish): 
                self.new_tool = Tool(
                        name=str(uuid.uuid4())
                    )
                created_tool = self.__create_tool(automatic_publish=auto_publish)
                self.assertTrue(isinstance(created_tool, Tool), "Expected a created tool")    


    def test_create_tool_no_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.new_tool.name = ""
                with self.assertRaises(APIResponseError) as exception:
                    self.__create_tool(automatic_publish=auto_publish)

                self.assertIn(
                    "Tool name cannot be empty.",
                    str(exception.exception),
                    f"Expected an error about the missing tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_create_tool_duplicated_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.new_tool.name = "sdk_project_gemini_tool"
                with self.assertRaises(APIResponseError) as exception:
                    self.__create_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool already exists [name=sdk_project_gemini_tool]..",
                    str(exception.exception),                    
                    f"Expected an error about duplicated tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_create_tool_invalid_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                new_tool = self.__load_tool()
                new_tool2 = self.__load_tool()

                with self.assertRaises(APIResponseError) as exception:
                    new_tool.name = f"{new_tool.name}:invalid"
                    self.__create_tool(tool=new_tool, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (: is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (:) in tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

                with self.assertRaises(APIResponseError) as exception:
                    new_tool2.name = f"{new_tool2.name}/invalid"
                    self.__create_tool(tool=new_tool2, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (/ is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (/) in tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )
        

    def test_create_tool_invalid_access_scope(self):
        self.new_tool.access_scope = "project" 
        with self.assertRaises(ValueError) as exc:
            self.__create_tool()
        self.assertEqual(
            str(exc.exception),
            "Access scope must be one of public, private.",
            "Expected a ValueError exception for invalid access scope"
        )   


    def test_create_tool_default_scope(self):
        self.new_tool.access_scope = None
        self.created_tool = self.__create_tool()

        self.assertEqual(self.created_tool.access_scope, "private", "Expected the default access scope to be 'private' when not specified")


    def test_create_tool_no_public_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.new_tool.access_scope = "public"
                self.new_tool.public_name = None
                with self.assertRaises(APIResponseError) as exception:
                    self.__create_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool publicName is required for tools with accessScope=public.",
                    str(exception.exception),                    
                    f"Expected an error about missing publicName for public access scope with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

   
    def test_create_tool_invalid_public_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish): 
                self.new_tool.access_scope = "public"
                self.new_tool.public_name = "com.sdk.testing#"  # Add invalid character to public name
                with self.assertRaises(APIResponseError) as exception:
                    self.__create_tool(automatic_publish=auto_publish)

                self.assertIn(
                    "Invalid public name, it can only contain lowercase letters, numbers, periods (.), dashes (-), and underscores (_). Please remove any other characters.",
                    str(exception.exception),                    
                    f"The expected error about invalid publicName was not returned when autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_tool_duplicated_public_name(self):
        test_params = [ True, False ]

        # Set the scope as public and assign a public name
        self.new_tool.access_scope = "public"
        self.new_tool.public_name=f"public_{self.new_tool.name}"
        self.created_tool = self.__create_tool()

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):

                # Create a new with the same public name of created_tool
                duplicated_pn_tool = self.__load_tool()
                duplicated_pn_tool.access_scope = "public"
                duplicated_pn_tool.public_name = self.created_tool.public_name
                
                with self.assertRaises(APIResponseError) as exception:
                    self.__create_tool(tool=duplicated_pn_tool, automatic_publish=auto_publish)
                self.assertIn(
                    f"Tool already exists [publicName={self.created_tool.public_name}].",
                    str(exception.exception),                   
                    f"Expected an error about the duplicated public name when autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_tool_api_scope_with_no_open_api(self):
        self.new_tool.scope = "api"
        with self.assertRaises(ValueError) as exception:
            self.new_tool.openApi = ""
        self.assertIn(
            '"Tool" object has no field "openApi"',
            str(exception.exception),
            "Expected a validation error when openApi is not provided for api scope"
        )

    
    def test_create_tool_api_scope_with_no_open_api_json(self):
        self.new_tool.scope = "api"
        with self.assertRaises(ValueError) as exception:
            self.new_tool.openApiJson = ""
            
        self.assertIn(
            '"Tool" object has no field "openApiJson"',
            str(exception.exception),
            "Expected a validation error when openApiJson is not provided for api scope"
        )

    
    def test_create_tool_invalid_scope(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish): 
                
                with self.assertRaises(ValueError) as exception:
                    self.new_tool.scope = "source"
                    self.__create_tool()
                self.assertIn(
                    'Scope must be one of builtin, external, api, proxied',
                    str(exception.exception),
                    "Expected a validation error about allowed values for instructions"
                )


    def test_create_tool_autopublish(self): 
        self.created_tool = self.__create_tool(automatic_publish=True)
        self.assertFalse(self.created_tool.is_draft, "Expected the tool to be published automatically")
    
    
    def test_create_tool_autopublish_private_scope(self):
        self.new_tool.access_scope = "private"

        self.created_tool = self.__create_tool(automatic_publish=True)
        self.assertFalse(self.created_tool.is_draft, "Expected the tool to be published automatically even with private scope")