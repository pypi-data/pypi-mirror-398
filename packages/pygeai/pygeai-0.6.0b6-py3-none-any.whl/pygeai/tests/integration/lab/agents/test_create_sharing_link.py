from unittest import TestCase
import unittest
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import SharingLink
from pygeai.core.common.exceptions import APIError, MissingRequirementException

ai_lab_manager: AILabManager

class TestAILabCreateSharingLinkIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.agent_id = "0026e53d-ea78-4cac-af9f-12650e5bb6d9" 

    def __create_sharing_link(self, agent_id=None):
        return self.ai_lab_manager.create_sharing_link(
            agent_id=self.agent_id if agent_id is None else agent_id
        )
    
    @unittest.skip("Endpoint is not found. Validate if it was deleted")
    def test_create_sharing_link(self):    
        shared_link = self.__create_sharing_link()        
        self.assertIsInstance(shared_link, SharingLink, "Expected response to be an instance of SharingLink")
       
        self.assertEqual(
            shared_link.agent_id,
            self.agent_id,
            "Returned agentId should match the requested agent_id"
        )
        self.assertTrue(
            shared_link.api_token.startswith("shared-"),
            "apiToken should start with 'shared-'"
        )
        self.assertTrue(
            shared_link.shared_link.startswith("https://"),
            "sharedLink should be a valid URL"
        )
        self.assertIn(
            f"agentId={self.agent_id}",
            shared_link.shared_link,
            "sharedLink should contain the agentId as a query parameter"
        )
        self.assertIn(
            f"sharedToken={shared_link.api_token}",
            shared_link.shared_link,
            "sharedLink should contain the apiToken as sharedToken"
        )


    @unittest.skip("Endpoint is not found. Validate if it was deleted")
    def test_create_sharing_link_no_agent_id(self):
        with self.assertRaises(MissingRequirementException) as context:
            self.__create_sharing_link(agent_id="")
        self.assertEqual(
            str(context.exception),
            "agent_id must be specified in order to create sharing link",
            "Expected exception for missing agent_id"
        )


    @unittest.skip("Endpoint is not found. Validate if it was deleted")
    def test_create_sharing_link_invalid_agent_id(self):
        with self.assertRaises(APIError) as exception:
            invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
            self.__create_sharing_link(agent_id=invalid_id)
        self.assertIn(
            f"Agent not found [IdOrName= {invalid_id}].",
            str(exception.exception),
            "Expected error message for invalid agent id"
        )