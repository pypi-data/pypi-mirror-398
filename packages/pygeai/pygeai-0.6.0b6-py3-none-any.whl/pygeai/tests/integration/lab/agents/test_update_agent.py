from unittest import TestCase
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput
from pydantic import ValidationError
from pygeai.core.common.exceptions import APIError


class TestAILabUpdateAgentIntegration(TestCase):    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()

        load_agent = self.__load_agent()
        self.agent_to_update = load_agent["agent"]
        self.random_str = load_agent["random_str"]

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

        return { 
            "agent": agent,
            "random_str": random_str 
        }


    def __update_agent(self, agent=None, automatic_publish=False, upsert=False):
        """
        Helper to create an agent with the current project_id and ai_lab_manager.
        If automatic_publish is None, do not pass it (useful for tests that omit it).
        """
        return self.ai_lab_manager.update_agent(
            agent=self.agent_to_update if agent is None else agent,
            automatic_publish=automatic_publish, 
            upsert=upsert
        )
    

    def test_update_agent(self):
        self.agent_to_update.agent_data.models[0].name = "gemini/gemini-1.5-flash-8b-exp-0827"
        self.agent_to_update.access_scope = "private"
        updated_agent = self.__update_agent()

        self.assertTrue(isinstance(updated_agent, Agent), "Expected a created agent")
       
        self.assertEqual(updated_agent.name, f"UpdatedAgent{self.random_str}")
        self.assertEqual(updated_agent.access_scope, "private")
        self.assertEqual(updated_agent.public_name, f"public_{self.random_str}")
        self.assertEqual(updated_agent.job_description, f"SummarizerAgent{self.random_str}",)
        self.assertEqual(updated_agent.description, f"Agent that summarized documents. {self.random_str}")

        self.assertEqual(updated_agent.agent_data.models[0].name, "gemini/gemini-1.5-flash-8b-exp-0827")
        self.assertTrue(updated_agent.is_draft, "gemini/gemini-1.5-flash-8b-exp-0827")

        self.agent_to_update.agent_data.models[0].name = "openai/gpt-4o"
        self.__update_agent()

    
    def test_update_agent_no_name(self):
        test_params = [ True, False ]
        self.agent_to_update.name = ""
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)
                
                self.assertIn(
                    "Error received while updating agent: errors=[Error(id=2007, description='Agent name cannot be empty.')]",
                    str(exception.exception),
                    f"Expected error about missing agent name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )


    def test_update_agent_duplicated_name(self):
        test_params = [ True, False ]
        self.agent_to_update.name = "AritmeticaExpert"

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)
                
                self.assertIn(
                    "Agent already exists [name=AritmeticaExpert].",
                    str(exception.exception),
                    f"Expected error about duplicated agent name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )

    
    def test_update_agent_invalid_name(self):
        test_params = [ True, False ]
        self.agent_to_update.name = f"{self.agent_to_update.name}:/"

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):

                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Invalid character in name (: is not allowed).",
                    str(exception.exception),
                    f"Expected error about invalid character (:) in name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )
                self.assertIn(
                    "Invalid character in name (/ is not allowed).",
                    str(exception.exception),
                    f"Expected error about invalid character (/) in name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )


    def test_update_agent_no_public_name(self):        
        test_params = [ True, False ]
        self.agent_to_update.public_name = ""

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Agent publicName is required for agents with accessScope=public.",
                    str(exception.exception),
                    f"Expected error about missing public name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )


    def test_update_agent_duplicated_public_name(self):               
        test_params = [ True, False ]
        self.agent_to_update.public_name = "com.testing.geai.googlesummarizer"

        for auto_publish in test_params:
            with self.subTest(input=auto_publish): 
                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Agent already exists [publicName=com.testing.geai.googlesummarizer].",
                    str(exception.exception),
                    f"Expected error about duplicated public name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )

    
    def test_update_agent_invalid_public_name(self):        
        test_params = [ True, False ]
        self.agent_to_update.public_name = self.agent_to_update.public_name.replace("_", "/")

        for auto_publish in test_params:
            with self.subTest(input=auto_publish): 
                with self.assertRaises(APIError) as exception:
                    self.__update_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Invalid public name, it can only contain lowercase letters, numbers, periods (.), dashes (-), and underscores (_). Please remove any other characters.",
                    str(exception.exception),
                    f"Expected error about invalid public name when autopublish is {'enabled' if auto_publish else 'disabled'} was not returned."
                )


    def test_update_agent_no_prompt_instructions(self):
        test_params = [ True, False ]
        self.agent_to_update.agent_data.prompt.instructions = ""

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                if auto_publish == True:
                    with self.assertRaises(ValidationError) as exception:
                        self.__update_agent(automatic_publish=auto_publish)
                    self.assertIn(
                        "agent_data.prompt must have at least instructions for publication",
                        str(exception.exception),
                        f"Expected a validation error about allowed values for instructions when autopublish is {'enabled' if auto_publish else 'disabled'}"
                    )
                else:
                    updated_agent = self.__update_agent(automatic_publish=auto_publish)
                    self.assertTrue(isinstance(updated_agent, Agent))


    def test_update_agent_no_model(self):
        test_params = [ True, False ]
        self.agent_to_update.agent_data.models[0].name = ""
        
        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                
                # If the agent is not published, the API returns a warning message for invalid model name. However, the sdk mapping is not returning it.
                if auto_publish == False:                    
                    updated_agent = self.__update_agent(automatic_publish=auto_publish)
                    
                    self.assertTrue(isinstance(updated_agent, Agent))
                else:                 
                    with self.assertRaises(APIError) as exception:
                        self.__update_agent(automatic_publish=auto_publish)
                    error_msg = str(exception.exception)
                    self.assertIn(
                        "description='Model not found [name=]",
                        error_msg,
                        "Expected a validation error about allowed values for model name" 
                    )

    
    def test_update_agent_autopublish(self):        
        updated_agent = self.__update_agent(automatic_publish=True)

        self.assertEqual(
            updated_agent.name, 
            f"UpdatedAgent{self.random_str}",
            "Expected agent name to remain unchanged after update."
        )
        self.assertFalse(
            updated_agent.is_draft,
            "Expected agent to be published when autopublish is True, but it is still a draft."
        )


    def test_update_agent_autopublish_private_scope(self):
        self.agent_to_update.access_scope = "private"

        updated_agent = self.__update_agent(automatic_publish=True)
        self.assertFalse(updated_agent.is_draft, "Expected the agent to be published automatically even with private scope")
    