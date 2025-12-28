from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, PromptOutput, PromptExample, LlmConfig, Sampling, Model
from pygeai.core.common.exceptions import APIError

ai_lab_manager: AILabManager

class TestAILabPublishAgentRevisionIntegration(TestCase):  

    def setUp(self):
        self.ai_lab_manager = AILabManager()
        self.agent_id = "b4b09935-2ad2-42c0-bd55-1ee6fa4b6034"

    
    def __publish_agent_revision(self,  revision: str, agent_id=None):
        return self.ai_lab_manager.publish_agent_revision(
            agent_id=self.agent_id if agent_id is None else agent_id,
            revision=revision
        )
    

    def __load_agent(self):
        random_str = str(uuid.uuid4())
        agent = Agent(
            id="b4b09935-2ad2-42c0-bd55-1ee6fa4b6034",
            name=f"UpdatedAgent{random_str}",
            access_scope="public",
            public_name=f"public_{random_str}",
            job_description=f"SummarizerAgent{random_str}",
            description=f"Agent that summarized documents. {random_str}",
            agent_data=AgentData(
                prompt=Prompt(
                    instructions="the user will provide a document, you must return a summary of the document.",
                    inputs=["text", "avoid slang indicator"],
                    outputs=[
                        PromptOutput(key="translated_text", description="translated text, with slang or not depending on the indication. in plain text.")
                    ],
                    examples=[
                        PromptExample(input_data="hola mundo [no-slang]", output='{"translated_text":"hello world"}'),
                        PromptExample(input_data="esto es una prueba pincheguey [keep-slang]", output='{"translated_text":"this is a test pal"}')
                    ]
                ),
                llm_config=LlmConfig(
                    max_tokens=1800,
                    timeout=0,
                    sampling=Sampling(temperature=0.3, top_k=0, top_p=0)
                ),
                models=[Model(name="openai/gpt-4o")]
            )
        )

        return agent


    def __update_agent(self):
        """
        Helper method to update agent and generate a new revision of it
        """
        agent = self.__load_agent()
        return self.ai_lab_manager.update_agent(
            agent=agent,
            automatic_publish=False, 
            upsert=False
        )    


    def test_publish_agent_revision(self):
        new_revision = (self.__update_agent()).revision
        published_agent = self.__publish_agent_revision(revision=new_revision)

        self.assertFalse(published_agent.is_draft, "Expected draft to be false after publishing the revision") 
        self.assertEqual(published_agent.revision, new_revision, "Expected last revision to be published") 

    
    def test_publish_agent_earlier_revision_with_newer_revision_published(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_agent_revision(revision="1")
        self.assertIn(
            "There are newer published revisions.",
            str(exception.exception),
            "Expected error when trying to send a earlier revision"
        )


    def test_publish_agent_earlier_revision(self):
        earlier_revision = (self.__update_agent()).revision
        self.__update_agent()
        published_agent = self.__publish_agent_revision(revision=earlier_revision)

        self.assertFalse(published_agent.is_draft, "Expected draft to be false after publishing the revision") 
        self.assertEqual(published_agent.revision, earlier_revision, "Expected last revision to be published") 


    def test_publish_agent_invalid_revision(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_agent_revision(revision="10000000")
        self.assertIn(
            "Invalid revision [rev=10000000]",
            str(exception.exception),
            "Expected error when trying to send a revision that does not exist"
        )


    def test_publish_agent_string_revision(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_agent_revision(revision="revision")
        self.assertIn("Bad Request", str(exception.exception))
        self.assertIn("400", str(exception.exception))


    def test_publish_agent_invalid_agent_id(self):
        invalid_id = "0026e53d-ea78-4cac-af9f-12650invalid"
        with self.assertRaises(APIError) as exception:
            self.__publish_agent_revision(revision="103", agent_id=invalid_id)
        self.assertIn(
            f"Agent not found [IdOrName= {invalid_id}].",
            str(exception.exception),
            "Expected error when sending and invalid agent id"
        )

    
    def test_publish_agent_no_agent_id(self):
        with self.assertRaises(APIError) as exception:
            self.__publish_agent_revision(revision="103", agent_id="")
        self.assertIn("Not Found", str(exception.exception))
        self.assertIn("404", str(exception.exception))