from unittest import TestCase
import uuid
from pygeai.core.common.exceptions import APIResponseError
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, ToolParameter


class TestAILabUpdateToolIntegration(TestCase):  
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.tool_to_update = self.__load_tool()

    
    def __load_tool(self):
        self.random_str = str(uuid.uuid4())
        return Tool(
            id="c77e1f2e-0322-4dd0-b6ec-aff217f1cb32",
            name=f"sdk_project_updated_tool_{self.random_str}",
            description=f"Tool updated for sdk testing purposes {self.random_str}",
            scope="builtin",
            openApi="https://raw.usercontent.com//openapi.json",
            openApiJson={"openapi": "3.0.0","info": {"title": f"Simple API overview {self.random_str}","version": "3.0.0"}},
            accessScope="private",
            reportEvents="None",
            parameters=[{
                "key": "param", 
                "description": f"param description {self.random_str}",
                "type":"app", 
                "value": f"value {self.random_str}",
                "data_type": "String",
                "isRequired": False
            }]
        )
    

    def __update_tool(self, tool: Tool = None, automatic_publish: bool = False, upsert: bool = False):
        """
        Helper method to update a tool.
        """
        return self.ai_lab_manager.update_tool(
            tool = self.tool_to_update if tool is None else tool,
            automatic_publish=automatic_publish,
            upsert=upsert
        )


    def test_update_tool_all_fields_success(self):
        updated_tool = self.__update_tool()
        self.assertEqual(updated_tool.name, self.tool_to_update.name)
        self.assertEqual(updated_tool.description, self.tool_to_update.description)
        self.assertEqual(updated_tool.open_api_json, self.tool_to_update.open_api_json)
        self.assertEqual(updated_tool.parameters[0].description, self.tool_to_update.parameters[0].description)
        self.assertEqual(updated_tool.parameters[0].value, self.tool_to_update.parameters[0].value)
        self.assertTrue(updated_tool.is_draft, "Expected tool to be in draft state after update")


    def test_update_tool_invalid_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                tool = self.__load_tool()
                tool2 = self.__load_tool()

                with self.assertRaises(APIResponseError) as exception:
                    tool.name = f"{tool.name}:invalid"
                    self.__update_tool(tool=tool, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (: is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (:) in tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

                with self.assertRaises(APIResponseError) as exception:
                    tool2.name = f"{tool2.name}/invalid"
                    self.__update_tool(tool=tool2, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (/ is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (/) in tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_duplicated_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.tool_to_update.name = "sdk_project_gemini_tool"
                with self.assertRaises(APIResponseError) as exception:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool already exists",
                    str(exception.exception),                    
                    f"Expected an error about duplicated tool name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_no_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.tool_to_update.name = ""
                with self.assertRaises(APIResponseError) as exception:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool name cannot be empty",
                    str(exception.exception),                    
                    f"Expected an error when tool name is not provided with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_invalid_id(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
                self.tool_to_update.id = invalid_id
                with self.assertRaises(APIResponseError) as exception:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    f"Tool not found [IdOrName= {invalid_id}",
                    str(exception.exception),                    
                    f"Expected an error when tool id is invalid and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_scope(self):
        for scope in ["builtin", "external", "api"]:
            tool = self.__load_tool()
            tool.scope = scope
            result = self.__update_tool(tool=tool)
            self.assertEqual(result.scope, scope)

        
    def test_update_tool_invalid_scope(self):
        test_params = [ True, False ]
        self.tool_to_update.scope = "project"
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):                
                with self.assertRaises(ValueError) as exception:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    f"Scope must be one of builtin, external, api, proxied",
                    str(exception.exception),                    
                    f"Expected an error when tool scope is invalid and autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_access_scope(self):
        for access_scope in ["public", "private"]:
            tool = self.__load_tool()
            tool.access_scope = access_scope

            if access_scope == "public":
                tool.public_name = f"com.sdk.testing.{self.random_str}"

            updated_tool = self.__update_tool(tool=tool)
            self.assertEqual(updated_tool.access_scope, access_scope)


    def test_update_tool_invalid_public_name(self):
        test_params = [ True, False ]
        self.tool_to_update.access_scope = "public"
        self.tool_to_update.public_name = "invalid#name"
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):                
                with self.assertRaises(APIResponseError) as exception:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid public name, it can only contain lowercase letters, numbers, periods (.), dashes (-), and underscores (_). Please remove any other characters.",
                    str(exception.exception),                    
                    f"Expected error when invalid public name is sent and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    def test_update_tool_duplicate_public_name(self):
        test_params = [ True, False ]
        self.tool_to_update.access_scope = "public"
        self.tool_to_update.public_name = "test.sdk.beta.tool"
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):   
                with self.assertRaises(Exception) as exc:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool already exists",
                    str(exc.exception),
                    f"Expected error when public name is duplicated and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )


    def test_update_tool_no_public_name(self):
        test_params = [ True, False ]
        self.tool_to_update.access_scope = "public"
        self.tool_to_update.public_name = ""

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):  
                with self.assertRaises(Exception) as exc:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Tool publicName is required for tools with accessScope=public.",
                    str(exc.exception),
                    f"Expected error when public name is not provided and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )
   

    def test_update_tool_no_open_api_nor_json(self):
        test_params = [ True, False ]
        self.tool_to_update.scope = "api"
        self.tool_to_update.open_api = ""
        self.tool_to_update.open_api_json = None

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):  
                with self.assertRaises(APIResponseError) as exc:
                    self.__update_tool(automatic_publish=auto_publish)
                self.assertIn(
                    "Either openApi (URL with the OpenAPI definition) or the openApiJson (with the conent) are required for api-tools.",
                    str(exc.exception),
                    f"Expected error when no openApi or openApiJson are provided and autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_update_tool_parameters(self):
        self.tool_to_update.parameters = [
            ToolParameter(key="paramA", data_type="String", description="descA", is_required=True),
            ToolParameter(key="paramB", data_type="String", description="descB", is_required=False)
        ]
        result = self.__update_tool()
        self.assertEqual(len(result.parameters), 2)
        self.assertEqual(result.parameters[0].key, "paramA")
        self.assertEqual(result.parameters[1].key, "paramB")


    def test_update_tool_automatic_publish(self):
        result = self.__update_tool(automatic_publish=True)
        self.assertFalse(result.is_draft, "Expected tool to be published after update with automatic_publish=True")

   
    def test_update_tool_upsert(self):
        self.tool_to_update.id = str(uuid.uuid4())
        self.tool_to_update.name = str(uuid.uuid4())
        result = self.__update_tool(upsert=True)

        if isinstance(result, Tool):
            self.ai_lab_manager.delete_tool(result.id)

        self.assertEqual(result.name,  self.tool_to_update.name)


    def test_update_tool_upsert_false_not_exists(self):
        new_id = str(uuid.uuid4())
        self.tool_to_update.id = new_id
        with self.assertRaises(Exception) as exc:
            self.__update_tool(upsert=False)
        self.assertIn(f"Tool not found [IdOrName= {new_id}]", str(exc.exception))

    
    
    
