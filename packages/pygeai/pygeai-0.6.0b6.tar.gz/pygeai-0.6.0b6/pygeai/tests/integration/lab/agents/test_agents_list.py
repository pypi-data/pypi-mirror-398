from unittest import TestCase
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgentList, FilterSettings
import copy

ai_lab_manager: AILabManager

class TestAILabAgentsListIntegration(TestCase):    
    __required_attrs = [
        'id', 'status', 'name', 'access_scope', 'public_name',
        'avatar_image', 'description', 'job_description',
        'is_draft', 'is_readonly', 'revision', 'version', 'agent_data'
    ]

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.filter_settings = FilterSettings(
            allow_external=False,
            allow_drafts=True,
            access_scope="private",
        )


    def __get_agent_list(self, filter_settings: FilterSettings = None):
        return self.ai_lab_manager.get_agent_list(
            filter_settings= self.filter_settings if filter_settings is None else filter_settings
        )
    
    def test_get_public_agent_list(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.access_scope = "public"
        result = self.__get_agent_list(filter_settings=filter_settings)

        self.assertIsInstance(result, AgentList, "Expected a list of agents")        
        for agent in result.agents:            
            for attr in self.__required_attrs:
                self.assertTrue(
                    hasattr(agent, attr),
                    f"Agent should have an '{attr}' attribute"
                )   
            self.assertEqual(agent.access_scope, "public", "Expected all agents to be public")


    def test_get_private_agent_list(self):        
        result = self.__get_agent_list()

        self.assertIsInstance(result, AgentList, "Expected a list of agents")        
        for agent in result.agents:            
            for attr in self.__required_attrs:
                self.assertTrue(
                    hasattr(agent, attr),
                    f"Agent should have an '{attr}' attribute"
                )   
            self.assertEqual(agent.access_scope, "private", "Expected all agents to be private")

    
    def test_get_agent_list_by_invalid_status(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.status = "status_active"
        result = self.__get_agent_list(filter_settings=filter_settings)       
    
        self.assertEqual(len(result.agents), 0, "Expected no agents with invalid status")

    
    def test_get_agent_list_including_draft(self):
        result = self.__get_agent_list()

        validated = any(agent.is_draft == True for agent in result.agents)        
        self.assertTrue(
            validated,
            "Expected at least one agent to be a draft"
        )

    
    def test_get_agent_list_no_draft(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.allow_drafts = False

        result = self.__get_agent_list(filter_settings=filter_settings)
        
        for agent in result.agents: 
            self.assertFalse(agent.is_draft, "Expected no agents to be drafts")

    
    def test_get_agent_list_start_over_offset(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.start = 50

        result = self.__get_agent_list(filter_settings=filter_settings)        
        self.assertEqual(len(result.agents), 0, "Expected no agents when starting at offset over total count")

    
    def test_get_agent_list_small_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 2

        result = self.__get_agent_list(filter_settings=filter_settings)        
        self.assertEqual(len(result.agents), filter_settings.count, "Expected number of agents to match the count filter")

    
    def test_get_agent_list_big_count(self):
        filter_settings = copy.deepcopy(self.filter_settings)
        filter_settings.count = 50

        result = self.__get_agent_list(filter_settings=filter_settings)        
        self.assertLessEqual(len(result.agents), filter_settings.count, "Expected number of agents to be less than or equal to the count filter")