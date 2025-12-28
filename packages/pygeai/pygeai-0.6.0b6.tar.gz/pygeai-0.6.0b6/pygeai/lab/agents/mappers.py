from typing import Optional, List

from pygeai.lab.models import Agent, AgentList, SharingLink, AgentData, Prompt, PromptOutput, PromptExample, LlmConfig, \
    Sampling, ModelList, Model, ResourcePoolList, ResourcePool, ResourcePoolAgent, ResourcePoolTool


class AgentMapper:
    """
        A utility class for mapping agent-related data structures.
    """

    @classmethod
    def map_to_agent_list(cls, data: dict) -> AgentList:
        """
        Maps an API response dictionary to an `AgentList` object.

        This method extracts agents from the given data, converts them into a list of `Agent` objects,
        and returns an `AgentList` containing the list.

        :param data: dict - The dictionary containing agent response data.
        :return: AgentList - A structured response containing a list of agents.
        """
        agent_list = list()
        agents = data.get('agents')
        if agents is not None and any(agents):
            for agent_data in agents:
                agent = cls.map_to_agent(agent_data)
                agent_list.append(agent)

        return AgentList(agents=agent_list)

    @classmethod
    def map_to_agent(cls, data: dict) -> Agent:
        """
        Maps a dictionary to an `Agent` object.

        :param data: dict - The dictionary containing agent details.
        :return: Agent - The mapped `Agent` object.
        """
        agent_data_data = data.get("agentData")
        return Agent(
            id=data.get("id"),
            status=data.get("status"),
            name=data.get("name"),
            access_scope=data.get("accessScope", "private"),
            public_name=data.get("publicName"),
            avatar_image=data.get("avatarImage"),
            description=data.get("description"),
            job_description=data.get("jobDescription"),
            is_draft=data.get("isDraft"),
            is_readonly=data.get("isReadonly"),
            revision=data.get("revision"),
            version=data.get("version"),
            agent_data=cls._map_agent_data(agent_data_data) if agent_data_data else None
        )

    @classmethod
    def _map_agent_data(cls, data: dict) -> Optional[AgentData]:
        """
        Maps a dictionary to an `AgentData` object.

        :param data: dict - The dictionary containing agentData details (prompt, llmConfig, models).
        :return: Optional[AgentData] - The mapped `AgentData` object or None if data is absent.
        """
        prompt_data = data.get("prompt")
        llm_config_data = data.get("llmConfig")
        models_list = data.get("models")
        strategy_name = data.get("strategyName")
        resource_pool_list = data.get("resourcePools")
        return AgentData(
            prompt=cls._map_to_prompt(prompt_data) if prompt_data else None,
            llm_config=cls._map_to_llm_config(llm_config_data) if llm_config_data else None,
            strategy_name=strategy_name,
            models=cls._map_to_model_list(models_list) if models_list else None,
            resource_pools=cls._map_to_resource_pool_list(resource_pool_list) if resource_pool_list else None
        )

    @classmethod
    def _map_to_resource_pool_list(cls, data: List[dict]) -> ResourcePoolList:
        """
        Maps a list of dictionaries to a `ResourcePoolList` object.

        :param data: List[dict] - The list of dictionaries containing resource pool details.
        :return: ResourcePoolList - The mapped `ResourcePoolList` object.
        """
        return ResourcePoolList(
            resource_pools=[cls._map_to_resource_pool(pool) for pool in data] if data else []
        )

    @classmethod
    def _map_to_resource_pool(cls, data: dict) -> ResourcePool:
        """
        Maps a dictionary to a `ResourcePool` object.

        :param data: dict - The dictionary containing resource pool details.
        :return: ResourcePool - The mapped `ResourcePool` object.
        """
        tools_data = data.get("tools")
        agents_data = data.get("agents")
        return ResourcePool(
            name=data.get("name"),
            tools=cls._map_to_resource_pool_tools(tools_data) if tools_data else None,
            agents=cls._map_to_resource_pool_agents(agents_data) if agents_data else None
        )

    @classmethod
    def _map_to_resource_pool_agents(cls, data: List[dict]) -> List[ResourcePoolAgent]:
        """
        Maps a list of dictionaries to a list of `ResourcePoolAgent` objects.

        :param data: List[dict] - The list of dictionaries containing resource pool agent details.
        :return: List[ResourcePoolAgent] - The mapped list of `ResourcePoolAgent` objects.
        """
        return [ResourcePoolAgent(
            name=agent.get("name"),
            revision=agent.get("revision")
        ) for agent in data] if data else []

    @classmethod
    def _map_to_resource_pool_tools(cls, data: List[dict]) -> List[ResourcePoolTool]:
        """
        Maps a list of dictionaries to a list of `ResourcePoolTool` objects.

        :param data: List[dict] - The list of dictionaries containing resource pool tool details.
        :return: List[ResourcePoolTool] - The mapped list of `ResourcePoolTool` objects.
        """
        return [ResourcePoolTool(
            name=tool.get("name"),
            revision=tool.get("revision")
        ) for tool in data] if data else []

    @classmethod
    def _map_to_prompt(cls, data: dict) -> Prompt:
        """
        Maps a dictionary to a `Prompt` object.

        :param data: dict - The dictionary containing prompt details.
        :return: Prompt - The mapped `Prompt` object.
        """
        outputs_list = data.get("outputs", [])
        examples_list = data.get("examples", [])
        return Prompt(
            instructions=data.get("instructions"),
            inputs=data.get("inputs", []),
            outputs=cls._map_to_prompt_output_list(outputs_list) if outputs_list else None,
            examples=cls._map_to_prompt_example_list(examples_list) if examples_list else None
        )

    @classmethod
    def _map_to_prompt_output_list(cls, data: List[dict]) -> List[PromptOutput]:
        """
        Maps a list of dictionaries to a list of `PromptOutput` objects.

        :param data: List[dict] - The list of dictionaries containing prompt output details.
        :return: List[PromptOutput] - The mapped list of `PromptOutput` objects.
        """
        return [cls._map_to_prompt_output(output) for output in data]

    @classmethod
    def _map_to_prompt_output(cls, data: dict) -> PromptOutput:
        """
        Maps a dictionary to a `PromptOutput` object.

        :param data: dict - The dictionary containing prompt output details.
        :return: PromptOutput - The mapped `PromptOutput` object.
        """
        return PromptOutput(
            key=data.get("key"),
            description=data.get("description")
        )

    @classmethod
    def _map_to_prompt_example_list(cls, data: List[dict]) -> List[PromptExample]:
        """
        Maps a list of dictionaries to a list of `PromptExample` objects.

        :param data: List[dict] - The list of dictionaries containing prompt example details.
        :return: List[PromptExample] - The mapped list of `PromptExample` objects.
        """
        return [cls._map_to_prompt_example(example) for example in data]

    @classmethod
    def _map_to_prompt_example(cls, data: dict) -> PromptExample:
        """
        Maps a dictionary to a `PromptExample` object.

        :param data: dict - The dictionary containing prompt example details.
        :return: PromptExample - The mapped `PromptExample` object.
        """
        return PromptExample(
            input_data=data.get("inputData"),
            output=data.get("output")
        )

    @classmethod
    def _map_to_llm_config(cls, data: dict) -> LlmConfig:
        """
        Maps a dictionary to an `LlmConfig` object.

        :param data: dict - The dictionary containing llmConfig details.
        :return: LlmConfig - The mapped `LlmConfig` object.
        """
        sampling_data = data.get("sampling", {})
        return LlmConfig(
            max_tokens=data.get("maxTokens"),
            timeout=data.get("timeout"),
            sampling=cls._map_to_sampling(sampling_data) if sampling_data else None
        )

    @classmethod
    def _map_to_sampling(cls, data: dict) -> Sampling:
        """
        Maps a dictionary to a `Sampling` object.

        :param data: dict - The dictionary containing sampling details.
        :return: Sampling - The mapped `Sampling` object.
        """
        return Sampling(
            temperature=data.get("temperature", 0.7),
            top_k=data.get("topK", 50),
            top_p=data.get("topP", 0.9)
        )

    @classmethod
    def _map_to_model_list(cls, data: List[dict]) -> ModelList:
        """
        Maps a list of dictionaries to a `ModelList` object.

        :param data: List[dict] - The list of dictionaries containing model details.
        :return: ModelList - The mapped `ModelList` object.
        """
        return ModelList(models=cls._map_to_model_list_items(data))

    @classmethod
    def _map_to_model_list_items(cls, data: List[dict]) -> List[Model]:
        """
        Maps a list of dictionaries to a list of `Model` objects.

        :param data: List[dict] - The list of dictionaries containing model details.
        :return: List[Model] - The mapped list of `Model` objects.
        """
        return [cls._map_to_model(model) for model in data]

    @classmethod
    def _map_to_model(cls, data: dict) -> Model:
        """
        Maps a dictionary to a `Model` object.

        :param data: dict - The dictionary containing model details.
        :return: Model - The mapped `Model` object.
        """
        llm_config_data = data.get("llmConfig")
        return Model(
            name=data.get("name"),
            llm_config=cls._map_to_llm_config(llm_config_data) if llm_config_data else None,
            prompt=data.get("prompt")
        )

    @classmethod
    def map_to_sharing_link(cls, data: dict) -> SharingLink:
        """
        Maps a dictionary response to a SharingLink object.

        :param data: dict - The raw response data containing agentId, apiToken, and sharedLink.
        :return: SharingLink - A SharingLink object representing the sharing link details.
        """
        return SharingLink(
            agent_id=data.get('agentId'),
            api_token=data.get('apiToken'),
            shared_link=data.get('sharedLink'),
        )
