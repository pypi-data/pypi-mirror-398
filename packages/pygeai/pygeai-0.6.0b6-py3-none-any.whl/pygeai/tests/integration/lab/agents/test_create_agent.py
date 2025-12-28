from unittest import TestCase
import unittest
import uuid
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput
from pydantic import ValidationError
from pygeai.core.common.exceptions import APIError, InvalidAPIResponseException 


class TestAILabCreateAgentIntegration(TestCase):    
    def setUp(self):
        """
        Set up the test environment.
        """
        self.ai_lab_manager = AILabManager()
        self.new_agent = self.__load_agent()
        self.created_agent: Agent = None


    def tearDown(self):
        """
        Clean up after each test if necessary.
        This can be used to delete the created agent or reset the state.
        """
        if isinstance(self.created_agent, Agent):
            self.ai_lab_manager.delete_agent(self.created_agent.id)


    def __load_agent(self):
        random_str = str(uuid.uuid4())
        return Agent(
            name=random_str,
            access_scope="public",
            public_name=f"public_{random_str}",
            job_description="Translator",
            description="Agent that translates from any language to english.",
            agent_data=AgentData(
                prompt=Prompt(
                    instructions="the user will provide a text, you must return the same text translated to english",
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
                models=[Model(name="gpt-4o")]
            )
        )


    def __create_agent(self, agent=None, automatic_publish=False):
        """
        Helper to create an agent with the current project_id and ai_lab_manager.
        If automatic_publish is None, do not pass it (useful for tests that omit it).
        """
        return self.ai_lab_manager.create_agent(
            agent=self.new_agent if agent is None else agent,
            automatic_publish=automatic_publish
        )


    def test_create_agent_full_data(self):
        self.created_agent = self.__create_agent()
        created_agent = self.created_agent
        agent = self.new_agent

        self.assertTrue(isinstance(created_agent, Agent), "Expected a created agent")

        # Assert the main fields of the created agent
        self.assertIsNotNone(created_agent.id)
        self.assertEqual(created_agent.name, agent.name)
        self.assertEqual(created_agent.access_scope, agent.access_scope)
        self.assertEqual(created_agent.public_name, agent.public_name)
        self.assertEqual(created_agent.avatar_image, agent.avatar_image)
        self.assertEqual(created_agent.description, agent.description)
        self.assertEqual(created_agent.job_description, agent.job_description)

        # Assert agentData fields
        agent_data = created_agent.agent_data
        self.assertIsNotNone(agent_data)
        self.assertEqual(agent_data.llm_config.max_tokens, agent.agent_data.llm_config.max_tokens)
        self.assertEqual(agent_data.llm_config.timeout, agent.agent_data.llm_config.timeout)
        self.assertEqual(agent_data.llm_config.sampling.temperature, agent.agent_data.llm_config.sampling.temperature)
        self.assertEqual(agent_data.llm_config.sampling.top_k, agent.agent_data.llm_config.sampling.top_k)
        self.assertEqual(agent_data.llm_config.sampling.top_p, agent.agent_data.llm_config.sampling.top_p)
        self.assertEqual(agent_data.models[0].name, agent.agent_data.models[0].name)

        # Assert prompt fields
        prompt = agent_data.prompt
        self.assertEqual(prompt.instructions, agent.agent_data.prompt.instructions)
        self.assertEqual(prompt.inputs, agent.agent_data.prompt.inputs)
        self.assertEqual(prompt.outputs[0].key, agent.agent_data.prompt.outputs[0].key)
        self.assertEqual(prompt.outputs[0].description, agent.agent_data.prompt.outputs[0].description)

        # Assert prompt examples
        self.assertEqual(prompt.examples[0].input_data, agent.agent_data.prompt.examples[0].input_data)
        self.assertEqual(prompt.examples[0].output, agent.agent_data.prompt.examples[0].output)


    def test_create_agent_minimum_required_data(self):
        self.new_agent = Agent(
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
        self.created_agent = self.__create_agent()
        agent = self.new_agent

        self.assertIsNotNone(self.created_agent.id)
        self.assertEqual(self.created_agent.name, agent.name)
        self.assertEqual(self.created_agent.description, agent.description)

         # Assert agentData fields
        agent_data = self.created_agent.agent_data
        self.assertIsNotNone(agent_data)
        self.assertEqual(agent_data.llm_config.max_tokens, agent.agent_data.llm_config.max_tokens)
        self.assertEqual(agent_data.llm_config.timeout, agent.agent_data.llm_config.timeout)
        self.assertEqual(agent_data.models[0].name, agent.agent_data.models[0].name)

        # Assert prompt fields
        prompt = agent_data.prompt
        self.assertEqual(prompt.instructions, agent.agent_data.prompt.instructions)
        self.assertEqual(prompt.inputs, agent.agent_data.prompt.inputs)


    def test_create_agent_without_required_data(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            
            with self.subTest(input=auto_publish):
                self.new_agent = Agent(
                    name=str(uuid.uuid4())
                )
                if auto_publish:
                    
                    with self.assertRaises(APIError) as exception:
                        self.__create_agent(automatic_publish=auto_publish)

                    #TODO: Change validation error to a more specific one
                    self.assertIn(
                        "A valid prompt is required. To be valid, it must provide clear instructions to the model",
                        str(exception.exception)
                    )   
                else:
                    created_agent = self.__create_agent(automatic_publish=auto_publish)
                    self.assertTrue(isinstance(created_agent, Agent), "Expected a created agent")


    def test_create_agent_no_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                self.new_agent.name = ""
                with self.assertRaises(APIError) as exception:
                    self.__create_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Agent name cannot be empty.",
                    str(exception.exception),
                    f"Expected an error about the missing agent name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_create_agent_duplicated_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.new_agent.name = "AritmeticaExpert"
                with self.assertRaises(APIError) as exception:
                    self.__create_agent(automatic_publish=auto_publish)
                self.assertIn(
                    "Agent cannot be created as it already exists [name=AritmeticaExpert].",
                    str(exception.exception),                    
                    f"Expected an error about duplicated agent name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )


    def test_create_agent_invalid_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                new_agent = self.__load_agent()
                new_agent2 = self.__load_agent()

                with self.assertRaises(APIError) as exception:
                    new_agent.name = f"{new_agent.name}:invalid"
                    self.__create_agent(agent=new_agent, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (: is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (:) in agent name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

                with self.assertRaises(APIError) as exception:
                    new_agent2.name = f"{new_agent2.name}/invalid"
                    self.__create_agent(agent=new_agent2, automatic_publish=auto_publish)
                self.assertIn(
                    "Invalid character in name (/ is not allowed).",
                    str(exception.exception),                    
                    f"Expected an error about invalid character (/) in agent name with autopublish {'enabled' if auto_publish else 'disabled'}"
                )
        

    def test_create_agent_invalid_scope(self):
        self.new_agent.access_scope = "project" 
        with self.assertRaises(ValueError) as exc:
            self.__create_agent()
        self.assertEqual(
            str(exc.exception),
            "Access scope must be one of public, private.",
            "Expected a ValueError exception for invalid access scope"
        )


    def test_create_agent_default_scope(self):
        self.new_agent.access_scope = None
        self.created_agent = self.__create_agent()

        self.assertEqual(self.created_agent.access_scope, "private", "Expected the default access scope to be 'private' when not specified")


    def test_create_agent_no_public_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:

            with self.subTest(input=auto_publish):
                self.new_agent.public_name = None
                with self.assertRaises(APIError) as exception:
                    self.__create_agent(automatic_publish=auto_publish)
                self.assertIn(
                    "Agent publicName is required for agents with accessScope=public.",
                    str(exception.exception),                    
                    f"Expected an error about missing publicName for public access scope with autopublish {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_agent_invalid_public_name(self):
        test_params = [ True, False ]

        for auto_publish in test_params:
            with self.subTest(input=auto_publish): 
                self.new_agent.public_name = self.new_agent.public_name.replace("_", "#")  # Add invalid character to public name
                with self.assertRaises(APIError) as exception:
                    self.__create_agent(automatic_publish=auto_publish)

                self.assertIn(
                    "Invalid public name, it can only contain lowercase letters, numbers, periods (.), dashes (-), and underscores (_). Please remove any other characters.",
                    str(exception.exception),                    
                    f"The expected error about invalid publicName was not returned when autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_agent_duplicated_public_name(self):
        test_params = [ True, False ]
        self.created_agent = self.__create_agent()

        for auto_publish in test_params:
            with self.subTest(input=auto_publish):
                duplicated_pn_agent = self.__load_agent()
                duplicated_pn_agent.public_name = self.created_agent.public_name

                with self.assertRaises(APIError) as exception:
                    self.__create_agent(agent=duplicated_pn_agent, automatic_publish=auto_publish)
                self.assertIn(
                    f"Agent already exists [publicName={self.created_agent.public_name}].",
                    str(exception.exception),                   
                    f"Expected an error about the duplicated public name when autopublish is {'enabled' if auto_publish else 'disabled'}"
                )

    
    def test_create_agent_no_prompt_instructions(self):
        self.new_agent.agent_data.prompt.instructions = ""
        self.created_agent = self.__create_agent()

        self.assertTrue(
            isinstance(self.created_agent, Agent),
            "Expected a created agent"
        )
        
        self.assertIsNone(
            self.created_agent.agent_data.prompt.instructions,
            "Expected the created agent to not have prompt instructions"
        )

    
    def test_create_agent_autopublish(self): 
        self.created_agent = self.__create_agent(automatic_publish=True)
        self.assertFalse(self.created_agent.is_draft, "Expected the agent to be published automatically")
    
    
    def test_create_agent_autopublish_private_scope(self):
        self.new_agent.access_scope = "private"

        self.created_agent = self.__create_agent(automatic_publish=True)
        self.assertFalse(self.created_agent.is_draft, "Expected the agent to be published automatically even with private scope")