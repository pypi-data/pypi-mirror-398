from unittest import TestCase

from pygeai.lab.agents.mappers import AgentMapper


class TestAgentMapper(TestCase):
    """
    python -m unittest pygeai.tests.lab.agents.test_mappers.TestAgentMapper
    """

    def test_map_to_agent_list(self):
        """Test mapping to AgentList with non-empty agents"""
        data = {
            "agents": [
                {"id": "agent1", "name": "Agent1", "status": "active"},
                {"id": "agent2", "name": "Agent2", "status": "pending"}
            ]
        }
        agent_list = AgentMapper.map_to_agent_list(data)
        self.assertEqual(len(agent_list.agents), 2)
        self.assertEqual(agent_list.agents[0].id, "agent1")
        self.assertEqual(agent_list.agents[0].name, "Agent1")
        self.assertEqual(agent_list.agents[1].id, "agent2")
        self.assertEqual(agent_list.agents[1].name, "Agent2")
        self.assertEqual(agent_list.to_list(), [a.to_dict() for a in agent_list.agents])

    def test_map_to_agent_list_empty(self):
        """Test mapping to AgentList with empty agents"""
        data = {"agents": []}
        agent_list = AgentMapper.map_to_agent_list(data)
        self.assertEqual(len(agent_list.agents), 0)
        self.assertEqual(agent_list.to_list(), [])

    def test_map_to_agent_list_null_agents(self):
        """Test mapping to AgentList with null agents"""
        data = {}
        agent_list = AgentMapper.map_to_agent_list(data)
        self.assertEqual(len(agent_list.agents), 0)
        self.assertEqual(agent_list.to_list(), [])

    def test_map_to_agent(self):
        """Test mapping to Agent with complete data"""
        data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent",
            "accessScope": "public",
            "publicName": "PublicAgent",
            "avatarImage": "avatar.png",
            "description": "Test description",
            "jobDescription": "Test job",
            "isDraft": False,
            "isReadonly": True,
            "revision": 1,
            "version": 1,
            "agentData": {
                "prompt": {"instructions": "Test prompt"},
                "llmConfig": {"maxTokens": 100},
                "models": [{"name": "model1"}],
                "resourcePools": [{"name": "pool1"}]
            }
        }
        agent = AgentMapper.map_to_agent(data)
        self.assertEqual(agent.id, data["id"])
        self.assertEqual(agent.status, data["status"])
        self.assertEqual(agent.name, data["name"])
        self.assertEqual(agent.access_scope, data["accessScope"])
        self.assertEqual(agent.public_name, data["publicName"])
        self.assertEqual(agent.avatar_image, data["avatarImage"])
        self.assertEqual(agent.description, data["description"])
        self.assertEqual(agent.job_description, data["jobDescription"])
        self.assertEqual(agent.is_draft, data["isDraft"])
        self.assertEqual(agent.is_readonly, data["isReadonly"])
        self.assertEqual(agent.revision, data["revision"])
        self.assertEqual(agent.version, data["version"])
        self.assertIsNotNone(agent.agent_data)
        self.assertEqual(agent.agent_data.prompt.instructions, "Test prompt")
        self.assertEqual(agent.agent_data.llm_config.max_tokens, 100)
        self.assertEqual(agent.agent_data.models.models[0].name, "model1")
        self.assertEqual(agent.agent_data.resource_pools[0].name, "pool1")

    def test_map_to_agent_no_agent_data(self):
        """Test mapping to Agent without agentData"""
        data = {
            "id": "agent123",
            "status": "active",
            "name": "TestAgent"
        }
        agent = AgentMapper.map_to_agent(data)
        self.assertEqual(agent.id, data["id"])
        self.assertEqual(agent.status, data["status"])
        self.assertEqual(agent.name, data["name"])
        self.assertIsNone(agent.agent_data)

    def test_map_to_resource_pool_list(self):
        """Test mapping to ResourcePoolList"""
        data = [
            {"name": "pool1", "tools": [{"name": "tool1", "revision": 1}]},
            {"name": "pool2", "agents": [{"name": "agent1", "revision": 2}]}
        ]
        pool_list = AgentMapper._map_to_resource_pool_list(data)
        self.assertEqual(len(pool_list.resource_pools), 2)
        self.assertEqual(pool_list.resource_pools[0].name, "pool1")
        self.assertEqual(pool_list.resource_pools[0].tools[0].name, "tool1")
        self.assertEqual(pool_list.resource_pools[1].name, "pool2")
        self.assertEqual(pool_list.resource_pools[1].agents[0].name, "agent1")

    def test_map_to_resource_pool_list_empty(self):
        """Test mapping to ResourcePoolList with empty data"""
        data = []
        pool_list = AgentMapper._map_to_resource_pool_list(data)
        self.assertEqual(len(pool_list.resource_pools), 0)

    def test_map_to_resource_pool_list_null(self):
        """Test mapping to ResourcePoolList with null data"""
        pool_list = AgentMapper._map_to_resource_pool_list(None)
        self.assertEqual(len(pool_list.resource_pools), 0)

    def test_map_to_resource_pool(self):
        """Test mapping to ResourcePool"""
        data = {
            "name": "pool1",
            "tools": [{"name": "tool1", "revision": 1}],
            "agents": [{"name": "agent1", "revision": 2}]
        }
        pool = AgentMapper._map_to_resource_pool(data)
        self.assertEqual(pool.name, data["name"])
        self.assertEqual(pool.tools[0].name, "tool1")
        self.assertEqual(pool.tools[0].revision, 1)
        self.assertEqual(pool.agents[0].name, "agent1")
        self.assertEqual(pool.agents[0].revision, 2)

    def test_map_to_resource_pool_agents(self):
        """Test mapping to ResourcePoolAgent list"""
        data = [
            {"name": "agent1", "revision": 1},
            {"name": "agent2", "revision": 2}
        ]
        agents = AgentMapper._map_to_resource_pool_agents(data)
        self.assertEqual(len(agents), 2)
        self.assertEqual(agents[0].name, "agent1")
        self.assertEqual(agents[0].revision, 1)
        self.assertEqual(agents[1].name, "agent2")
        self.assertEqual(agents[1].revision, 2)

    def test_map_to_resource_pool_agents_empty(self):
        """Test mapping to ResourcePoolAgent with empty data"""
        data = []
        agents = AgentMapper._map_to_resource_pool_agents(data)
        self.assertEqual(len(agents), 0)

    def test_map_to_resource_pool_agents_null(self):
        """Test mapping to ResourcePoolAgent with null data"""
        agents = AgentMapper._map_to_resource_pool_agents(None)
        self.assertEqual(len(agents), 0)

    def test_map_to_resource_pool_tools(self):
        """Test mapping to ResourcePoolTool list"""
        data = [
            {"name": "tool1", "revision": 1},
            {"name": "tool2", "revision": 2}
        ]
        tools = AgentMapper._map_to_resource_pool_tools(data)
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].name, "tool1")
        self.assertEqual(tools[0].revision, 1)
        self.assertEqual(tools[1].name, "tool2")
        self.assertEqual(tools[1].revision, 2)

    def test_map_to_resource_pool_tools_empty(self):
        """Test mapping to ResourcePoolTool with empty data"""
        data = []
        tools = AgentMapper._map_to_resource_pool_tools(data)
        self.assertEqual(len(tools), 0)

    def test_map_to_resource_pool_tools_null(self):
        """Test mapping to ResourcePoolTool with null data"""
        tools = AgentMapper._map_to_resource_pool_tools(None)
        self.assertEqual(len(tools), 0)

    def test_map_to_prompt(self):
        """Test mapping to Prompt"""
        data = {
            "instructions": "Test prompt",
            "inputs": ["input1"],
            "outputs": [{"key": "output1", "description": "desc1"}],
            "examples": [{"inputData": "data1", "output": "result1"}]
        }
        prompt = AgentMapper._map_to_prompt(data)
        self.assertEqual(prompt.instructions, data["instructions"])
        self.assertEqual(prompt.inputs, data["inputs"])
        self.assertEqual(prompt.outputs[0].key, "output1")
        self.assertEqual(prompt.examples[0].input_data, "data1")

    def test_map_to_prompt_output_list(self):
        """Test mapping to PromptOutput list"""
        data = [
            {"key": "output1", "description": "desc1"},
            {"key": "output2", "description": "desc2"}
        ]
        outputs = AgentMapper._map_to_prompt_output_list(data)
        self.assertEqual(len(outputs), 2)
        self.assertEqual(outputs[0].key, "output1")
        self.assertEqual(outputs[0].description, "desc1")
        self.assertEqual(outputs[1].key, "output2")
        self.assertEqual(outputs[1].description, "desc2")

    def test_map_to_prompt_output_list_empty(self):
        """Test mapping to PromptOutput list with empty data"""
        data = []
        outputs = AgentMapper._map_to_prompt_output_list(data)
        self.assertEqual(len(outputs), 0)

    def test_map_to_prompt_output(self):
        """Test mapping to PromptOutput"""
        data = {"key": "output1", "description": "desc1"}
        output = AgentMapper._map_to_prompt_output(data)
        self.assertEqual(output.key, data["key"])
        self.assertEqual(output.description, data["description"])

    def test_map_to_prompt_example_list(self):
        """Test mapping to PromptExample list"""
        data = [
            {"inputData": "data1", "output": "result1"},
            {"inputData": "data2", "output": "result2"}
        ]
        examples = AgentMapper._map_to_prompt_example_list(data)
        self.assertEqual(len(examples), 2)
        self.assertEqual(examples[0].input_data, "data1")
        self.assertEqual(examples[0].output, "result1")
        self.assertEqual(examples[1].input_data, "data2")
        self.assertEqual(examples[1].output, "result2")

    def test_map_to_prompt_example_list_empty(self):
        """Test mapping to PromptExample list with empty data"""
        data = []
        examples = AgentMapper._map_to_prompt_example_list(data)
        self.assertEqual(len(examples), 0)

    def test_map_to_prompt_example(self):
        """Test mapping to PromptExample"""
        data = {"inputData": "data1", "output": "result1"}
        example = AgentMapper._map_to_prompt_example(data)
        self.assertEqual(example.input_data, data["inputData"])
        self.assertEqual(example.output, data["output"])

    def test_map_to_llm_config(self):
        """Test mapping to LlmConfig"""
        data = {
            "maxTokens": 100,
            "timeout": 30,
            "sampling": {"temperature": 0.7, "topK": 40, "topP": 0.9}
        }
        llm_config = AgentMapper._map_to_llm_config(data)
        self.assertEqual(llm_config.max_tokens, data["maxTokens"])
        self.assertEqual(llm_config.timeout, data["timeout"])
        self.assertEqual(llm_config.sampling.temperature, data["sampling"]["temperature"])
        self.assertEqual(llm_config.sampling.top_k, data["sampling"]["topK"])
        self.assertEqual(llm_config.sampling.top_p, data["sampling"]["topP"])

    def test_map_to_sampling(self):
        """Test mapping to Sampling"""
        data = {"temperature": 0.7, "topK": 40, "topP": 0.9}
        sampling = AgentMapper._map_to_sampling(data)
        self.assertEqual(sampling.temperature, data["temperature"])
        self.assertEqual(sampling.top_k, data["topK"])
        self.assertEqual(sampling.top_p, data["topP"])

    def test_map_to_model_list(self):
        """Test mapping to ModelList"""
        data = [
            {"name": "model1", "prompt": {"prompt1": "test"}, "llmConfig": {"maxTokens": 100}},
            {"name": "model2", "prompt": {"prompt2": "test"}}
        ]
        model_list = AgentMapper._map_to_model_list(data)
        self.assertEqual(len(model_list.models), 2)
        self.assertEqual(model_list.models[0].name, "model1")
        self.assertEqual(model_list.models[0].prompt, {"prompt1": "test"})
        self.assertEqual(model_list.models[0].llm_config.max_tokens, 100)
        self.assertEqual(model_list.models[1].name, "model2")
        self.assertEqual(model_list.models[1].prompt, {"prompt2": "test"})
        self.assertIsNone(model_list.models[1].llm_config)

    def test_map_to_model_list_empty(self):
        """Test mapping to ModelList with empty data"""
        data = []
        model_list = AgentMapper._map_to_model_list(data)
        self.assertEqual(len(model_list.models), 0)

    def test_map_to_model(self):
        """Test mapping to Model"""
        data = {
            "name": "model1",
            "prompt": {"prompt1": "test"},
            "llmConfig": {"maxTokens": 100, "sampling": {"temperature": 0.7}}
        }
        model = AgentMapper._map_to_model(data)
        self.assertEqual(model.name, data["name"])
        self.assertEqual(model.prompt, data["prompt"])
        self.assertEqual(model.llm_config.max_tokens, 100)
        self.assertEqual(model.llm_config.sampling.temperature, 0.7)

    def test_map_to_sharing_link(self):
        """Test mapping to SharingLink"""
        data = {
            "agentId": "agent123",
            "apiToken": "token123",
            "sharedLink": "http://share.link"
        }
        sharing_link = AgentMapper.map_to_sharing_link(data)
        self.assertEqual(sharing_link.agent_id, data["agentId"])
        self.assertEqual(sharing_link.api_token, data["apiToken"])
        self.assertEqual(sharing_link.shared_link, data["sharedLink"])