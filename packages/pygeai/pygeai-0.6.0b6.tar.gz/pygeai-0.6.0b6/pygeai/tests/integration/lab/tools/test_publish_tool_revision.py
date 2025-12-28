from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool
from pygeai.core.common.exceptions import APIError

ai_lab_manager: AILabManager

class TestAILabPublishToolRevisionIntegration(TestCase):   

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.tool_id = "c77e1f2e-0322-4dd0-b6ec-aff217f1cb32"


    def __publish_tool_revision(self, revision: str, tool_id=None):
        return self.ai_lab_manager.publish_tool_revision(
            tool_id=self.tool_id if tool_id is None else tool_id,
            revision=revision
        )

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
        tool = self.__load_tool()
        return self.ai_lab_manager.update_tool(
            tool = tool,
            automatic_publish=False, 
            upsert=False
        )
    

    def test_publish_tool_revision(self):
        updated_tool = self.__update_tool()
        new_revision = updated_tool.revision

        published_tool = self.__publish_tool_revision(revision=str(new_revision))

        self.assertFalse(published_tool.is_draft, "Expected draft to be false after publishing the revision") 
        self.assertEqual(published_tool.revision, new_revision, "Expected last revision to be published") 
 

    def test_publish_tool_earlier_revision_with_newer_revision_published(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_tool_revision(revision="1")
        self.assertIn(
            "There are newer published revisions.",
            str(exception.exception),
            "Expected error when trying to send a earlier revision"
        )

    
    def test_publish_tool_earlier_revision(self):
        earlier_revision = (self.__update_tool()).revision
        #update the tool to create a newer revision
        self.__update_tool()

        published_tool = self.__publish_tool_revision(revision=earlier_revision)

        self.assertFalse(published_tool.is_draft, "Expected draft to be false after publishing the revision") 
        self.assertEqual(published_tool.revision, earlier_revision, "Expected last revision to be published") 


    def test_publish_tool_invalid_revision(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_tool_revision(revision="10000000")
        self.assertIn(
            "Invalid revision [rev=10000000]",
            str(exception.exception),
            "Expected error when trying to send a revision that does not exist"
        )


    def test_publish_tool_string_revision(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_tool_revision(revision="revision")
        self.assertIn("Bad Request", str(exception.exception))
        self.assertIn("400", str(exception.exception))


    def test_publish_tool_invalid_tool_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(APIError) as exception:
            self.__publish_tool_revision(revision="103", tool_id=invalid_id)
        self.assertIn(
            f"Tool not found [IdOrName= {invalid_id}].",
            str(exception.exception),
            "Expected error when sending and invalid agent id"
        )

    
    def test_publish_tool_no_tool_id(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_tool_revision(revision="103", tool_id="")
        self.assertIn("Not Found", str(exception.exception))
        self.assertIn("404", str(exception.exception))