from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model
from pygeai.core.common.exceptions import InvalidAPIResponseException

ai_lab_manager: AILabManager

class TestAILabDeleteAgentIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        

    def __create_agent(self):
        """
        Helper to create an agent with the current project_id and ai_lab_manager.
        If automatic_publish is None, do not pass it (useful for tests that omit it).
        """
        agent = Agent(
            name=str(uuid.uuid4()),
            description="Agent that translates from any language to english.",
            agent_data=AgentData(
                prompt=Prompt(
                    instructions="the user will provide a text, you must return the same text translated to english",
                    inputs=["text", "avoid slang indicator"]
                ),
                llm_config=LlmConfig(
                    max_tokens=1800,
                    timeout=0
                ),
                models=[Model(name="gpt-4o")]
            )
        )


        return self.ai_lab_manager.create_agent(
            agent=agent
        )

    def __delete_agent(self, agent_id: str):
        return self.ai_lab_manager.delete_agent(
            agent_id=agent_id
        )
    

    def test_delete_agent(self):         
        create_agent = self.__create_agent()     
        deleted_agent = self.__delete_agent(agent_id=create_agent.id)

        self.assertEqual(
            deleted_agent.content,
            "Agent deleted successfully",
            "Expected confirmation message after deletion"            
        )


    def test_delete_agent_no_agent_id(self):
        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__delete_agent(agent_id="")

        self.assertIn("405",str(exception.exception))    
        self.assertIn("Method Not Allowed",str(exception.exception))


    def test_delete_agent_invalid_agent_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(InvalidAPIResponseException) as exception:
            self.__delete_agent(agent_id=invalid_id)

        self.assertIn(
            f"Agent not found [IdOrName= {invalid_id}].",
            str(exception.exception),
            "Expected error message for invalid agent id"
        )