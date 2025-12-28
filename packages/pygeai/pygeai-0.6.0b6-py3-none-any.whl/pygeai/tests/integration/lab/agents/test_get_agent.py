from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, FilterSettings
from pygeai.core.common.exceptions import MissingRequirementException, APIError
import copy

ai_lab_manager: AILabManager

class TestAILabGetAgentIntegration(TestCase):    
    __required_attrs = [
        'id', 'status', 'name', 'access_scope', 'public_name',
        'avatar_image', 'description', 'job_description',
        'is_draft', 'is_readonly', 'revision', 'version', 'agent_data'
    ]

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.agent_id = "0026e53d-ea78-4cac-af9f-12650e5bb6d9"
        self.filter_settings = FilterSettings(
            revision="0",
            version="0"
        )

    def __get_agent(self, agent_id=None, filter_settings: FilterSettings = None):
        return self.ai_lab_manager.get_agent(
            agent_id=self.agent_id if agent_id is None else agent_id,
            filter_settings=self.filter_settings if filter_settings is None else filter_settings
        )

    def test_get_agent(self):
        agent = self.__get_agent()

        self.assertIsInstance(agent, Agent, "Expected an agent") 
        for attr in self.__required_attrs:
                self.assertTrue(
                    hasattr(agent, attr),
                    f"Agent should have an '{attr}' attribute"
                )
 

    def test_get_agent_no_agent_id(self):
        with self.assertRaises(Exception) as context:
            self.__get_agent(agent_id="")
        self.assertIn(
            "agent_id must be specified in order to retrieve the agent",
            str(context.exception),
            "Expected exception for missing agent_id"
        )


    def test_get_agent_invalid_agent_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(APIError) as context:
            self.__get_agent(agent_id=invalid_id)
        self.assertIn(
            f"Agent not found [IdOrName= {invalid_id}].",
            str(context.exception),
            "Expected an error for invalid agent id"
        )


    def test_get_agent_no_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = None
        agent = self.__get_agent(filter_settings=filter_settings)

        self.assertIsInstance(agent, Agent, "Expected an agent")
        self.assertGreater(agent.revision, 1, "Expected agent revision to be the latest")

    
    def test_get_agent_by_revision(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.revision = "5"
        agent = self.__get_agent(filter_settings=filter_settings)

        self.assertEqual(5, agent.revision, "Expected agent revision to be 5")
        self.assertIn("Version 2", agent.description, "Expected agent description to match the one in revision 5")


    def test_get_agent_no_version(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = None
        agent = self.__get_agent(filter_settings=filter_settings)

        self.assertGreater(agent.version, 1, "Expected agent version to be the latest")
        self.assertIn("Latest version", agent.description, "Expected agent description to contain 'Latest version'")


    def test_get_agent_by_version(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.version = "1"
        agent = self.__get_agent(filter_settings=filter_settings)

        self.assertNotIn("Latest version", agent.description, "Expected agent description to not contain 'Latest version'")