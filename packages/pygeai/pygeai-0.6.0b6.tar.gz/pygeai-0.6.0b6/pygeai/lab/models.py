import re
from typing import Literal, Optional, List, Dict, Any, Union, Iterator

from pydantic import model_validator, Field, field_validator

from pygeai.core import CustomBaseModel


class FilterSettings(CustomBaseModel):
    """
    Represents filter settings for querying or filtering data.

    :param id: str - The ID to filter by (e.g., an agent's ID), defaults to an empty string.
    :param name: str - The name to filter by (e.g., reasoning strategy name), defaults to an empty string.
    :param status: str - Status filter, defaults to None.
    :param start: int - Starting index for pagination, defaults to None.
    :param count: int - Number of items to return, defaults to None.
    :param is_active: bool - If it's active. Defaults to false.
    :param access_scope: str - Access scope filter, defaults to "private".
    :param allow_drafts: bool - Whether to include draft items, defaults to True.
    :param allow_external: bool - Whether to include external items, defaults to False.
    :param revision: str - Revision of the agent, defaults to 0.
    :param version: str - Version of the agent, defaults to 0
    :param scope: Optional[str] - Filter by scope (e.g., "builtin", "external", "api").
    """
    id: Optional[str] = Field(default=None, description="The ID to filter by (e.g., an agent's ID)")
    name: Optional[str] = Field(default=None, description="The name to filter by (e.g., a reasoning strategy name)")
    status: Optional[str] = Field(default=None, description="Status filter")
    start: Optional[int] = Field(default=None, description="Starting index for pagination")
    count: Optional[int] = Field(default=None, description="Number of items to return")
    access_scope: Optional[str] = Field(default="private", alias="accessScope", description="Access scope filter")
    allow_drafts: Optional[bool] = Field(default=True, alias="allowDrafts", description="Whether to include draft items")
    allow_external: Optional[bool] = Field(default=False, alias="allowExternal", description="Whether to include external items")
    is_active: Optional[bool] = Field(default=False, alias="isActive", description="Whether it's active")
    revision: Optional[str] = Field(default=None, description="Revision of the agent")
    version: Optional[int] = Field(default=None, description="Version of the agent")
    scope: Optional[str] = Field(None, description="Filter by scope (e.g., 'builtin', 'external', 'api')")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class Sampling(CustomBaseModel):
    """
    Represents sampling configuration for an LLM.

    :param temperature: float - Temperature value for sampling, controlling randomness.
    :param top_k: int - Top-K sampling parameter, limiting to the top K probable tokens.
    :param top_p: float - Top-P (nucleus) sampling parameter, limiting to the smallest set of tokens whose cumulative probability exceeds P.
    """
    temperature: float = Field(1.0, alias="temperature")
    top_k: int = Field(50, alias="topK")
    top_p: float = Field(1.0, alias="topP")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class LlmConfig(CustomBaseModel):
    """
    Represents the configuration parameters for an LLM.

    :param max_tokens: int - Maximum number of tokens the LLM can generate.
    :param timeout: int - Timeout value in seconds (0 means no timeout).
    :param sampling: Sampling - Sampling configuration for the LLM.
    """
    max_tokens: int = Field(..., alias="maxTokens")
    timeout: Optional[int] = Field(60, alias="timeout")
    sampling: Optional[Sampling] = Field(Sampling(), alias="sampling")

    def to_dict(self):
        result = {
            "maxTokens": self.max_tokens,
            "timeout": self.timeout,
            "sampling": self.sampling.to_dict() if self.sampling else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class Model(CustomBaseModel):
    """
    Represents a language model configuration used by an agent.

    :param name: str - The unique name identifying the model.
    :param llm_config: Optional[LlmConfig] - Overrides default agent LLM settings.
    :param prompt: Optional[dict] - A tailored prompt specific to this model.
    """
    name: Optional[str] = Field(None, alias="name")
    llm_config: Optional[LlmConfig] = Field(None, alias="llmConfig")
    prompt: Optional[Dict[str, Any]] = Field(None, alias="prompt")

    @field_validator("llm_config", mode="before")
    @classmethod
    def normalize_llm_config(cls, value):
        if isinstance(value, dict):
            return LlmConfig.model_validate(value)
        return value

    def to_dict(self):
        result = {"name": self.name}
        if self.llm_config is not None:
            result["llmConfig"] = self.llm_config.to_dict()
        if self.prompt is not None:
            result["prompt"] = self.prompt
        return result

    def __str__(self):
        return str(self.to_dict())


class PromptExample(CustomBaseModel):
    """
    Represents an example for the prompt configuration.

    :param input_data: str - Example input data provided to the agent.
    :param output: str - Example output in JSON string format.
    """
    input_data: str = Field(..., alias="inputData")
    output: str = Field(..., alias="output")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class PromptOutput(CustomBaseModel):
    """
    Represents an output definition for the prompt configuration.

    :param key: str - Key identifying the output.
    :param description: str - Description of the output's purpose and format.
    """
    key: str = Field(..., alias="key")
    description: str = Field(..., alias="description")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class Prompt(CustomBaseModel):
    """
    Represents the prompt configuration for an agent.

    :param instructions: str - Instructions for the agent's behavior.
    :param inputs: List[str] - List of input parameters the agent expects.
    :param outputs: List[PromptOutput] - List of output definitions the agent produces.
    :param context: Optional[str] - Background context for the agent # NOT IMPLEMENTED YET
    :param examples: List[PromptExample] - List of example input-output pairs.
    """
    instructions: Optional[str] = Field(None, alias="instructions")
    inputs: Optional[List[str]] = Field(None, alias="inputs")
    outputs: Optional[List[PromptOutput]] = Field([], alias="outputs")
    context: Optional[str] = Field(None, alias="context", description="Background context for the agent")
    examples: Optional[List[PromptExample]] = Field(None, alias="examples")

    '''
    @field_validator("instructions")
    @classmethod
    def validate_instructions(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("instructions cannot be blank")

        return value
    '''

    @field_validator("outputs", mode="before")
    @classmethod
    def normalize_outputs(cls, value):
        if isinstance(value, list):
            return [PromptOutput.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("examples", mode="before")
    @classmethod
    def normalize_examples(cls, value):
        if isinstance(value, list):
            return [PromptExample.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "instructions": self.instructions,
            "context": self.context,
            "inputs": self.inputs,
            "outputs": [output.to_dict() for output in self.outputs] if self.outputs else None,
            "examples": [example.to_dict() for example in self.examples] if self.examples else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ModelList(CustomBaseModel):
    models: List[Model] = Field(..., alias="models")

    @field_validator("models", mode="before")
    @classmethod
    def normalize_models(cls, value):
        if isinstance(value, list):
            return [Model.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [model.to_dict() for model in self.models]

    def __getitem__(self, index: int) -> Model:
        if self.models is None:
            raise IndexError("ModelList is empty")
        return self.models[index]

    def __len__(self) -> int:
        return len(self.models) if self.models else 0

    def __iter__(self):
        """Make ModelList iterable over its models."""
        if self.models is None:
            return iter([])
        return iter(self.models)

    def append(self, item: Model) -> None:
        """Append a Model instance to the models list."""
        if self.models is None:
            self.models = []
        self.models.append(item)


class ResourcePoolTool(CustomBaseModel):
    """
    Represents a tool within a resource pool.

    :param name: str - The ID or name of the tool.
    :param revision: Optional[int] - Specific revision of the tool; if None, uses latest published version.
    """
    name: str = Field(..., alias="name", description="The ID or name of the tool")
    revision: Optional[int] = Field(None, alias="revision", description="Specific revision of the tool; if None, uses latest published version")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        return value

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class ResourcePoolAgent(CustomBaseModel):
    """
    Represents a helper agent within a resource pool.

    :param name: str - The ID or name of the agent.
    :param revision: Optional[int] - Specific revision of the agent; if None, uses latest published version.
    """
    name: str = Field(..., alias="name", description="The ID or name of the agent")
    revision: Optional[int] = Field(None, alias="revision", description="Specific revision of the agent; if None, uses latest published version")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        return value

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class ResourcePool(CustomBaseModel):
    """
    Represents a resource pool organizing tools and helper agents.

    :param name: str - The name of the resource pool.
    :param tools: Optional[List[ResourcePoolTool]] - List of tools in the pool.
    :param agents: Optional[List[ResourcePoolAgent]] - List of helper agents in the pool.
    """
    name: str = Field(..., alias="name", description="The name of the resource pool")
    tools: Optional[List[ResourcePoolTool]] = Field(None, alias="tools", description="List of tools in the pool")
    agents: Optional[List[ResourcePoolAgent]] = Field(None, alias="agents", description="List of helper agents in the pool")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        return value

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, value):
        if isinstance(value, list):
            return [ResourcePoolTool.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("agents", mode="before")
    @classmethod
    def normalize_agents(cls, value):
        if isinstance(value, list):
            return [ResourcePoolAgent.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "name": self.name,
            "tools": [tool.to_dict() for tool in self.tools] if self.tools else None,
            "agents": [agent.to_dict() for agent in self.agents] if self.agents else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ResourcePoolList(CustomBaseModel):
    """
    Represents a list of resource pools for an agent.

    :param resource_pools: List[ResourcePool] - The list of resource pools.
    """
    resource_pools: List[ResourcePool] = Field(..., alias="resourcePools", description="The list of resource pools")

    @field_validator("resource_pools", mode="before")
    @classmethod
    def normalize_resource_pools(cls, value):
        if isinstance(value, list):
            return [ResourcePool.model_validate(item) if isinstance(item, dict) else item for item in value]
        raise ValueError("resource_pools must be a list of ResourcePool instances or dictionaries")

    def to_dict(self):
        """
        Serializes the ResourcePoolList to a list of dictionaries.

        :return: List[Dict] - A list of dictionary representations of the resource pools.
        """
        return [pool.to_dict() for pool in self.resource_pools]

    def __str__(self):
        return str(self.to_dict())

    def __getitem__(self, index: int) -> ResourcePool:
        if self.resource_pools is None:
            raise IndexError("ResourcePoolList is empty")
        return self.resource_pools[index]

    def __len__(self) -> int:
        return len(self.resource_pools) if self.resource_pools else 0

    def __iter__(self) -> Iterator[ResourcePool]:
        """Make ResourcePoolList iterable over its resource pools."""
        if self.resource_pools is None:
            return iter([])
        return iter(self.resource_pools)

    def append(self, item: ResourcePool) -> None:
        """Append a ResourcePool instance to the resource_pools list."""
        if self.resource_pools is None:
            self.resource_pools = []
        self.resource_pools.append(item)


class AgentData(CustomBaseModel):
    """
    Represents the detailed configuration data for an agent.

    :param prompt: dict - Prompt instructions, inputs, outputs, and examples for the agent.
    :param llm_config: dict - Configuration parameters for the LLM (e.g., max tokens, timeout, temperature).
    :param strategy_name: str - Strategy name used for the agent (e.g., Dynamic Prompting, Chain of Thought, Question Refinement, etc)
    :param models: ModelList - List of models available for the agent.
    :param resource_pools: Optional[List[ResourcePool]] - List of resource pools organizing tools and helper agents.
    """
    prompt: Prompt = Field(..., alias="prompt")
    llm_config: LlmConfig = Field(..., alias="llmConfig")
    strategy_name: Optional[str] = Field("Dynamic Prompting", alias="strategyName")
    models: Optional[Union[ModelList, List[Model]]] = Field(None, alias="models")
    resource_pools: Optional[ResourcePoolList] = Field(None, alias="resourcePools", description="List of resource pools organizing tools and helper agents")

    @field_validator("prompt", mode="before")
    @classmethod
    def normalize_prompt(cls, value):
        if isinstance(value, dict):
            return Prompt.model_validate(value)
        return value

    @field_validator("llm_config", mode="before")
    @classmethod
    def normalize_llm_config(cls, value):
        if isinstance(value, dict):
            return LlmConfig.model_validate(value)
        return value

    @field_validator("models", mode="before")
    @classmethod
    def normalize_models(cls, value):
        if isinstance(value, ModelList):
            return value
        elif isinstance(value, list):
            return ModelList(models=[Model.model_validate(item) if isinstance(item, dict) else item for item in value])
        raise ValueError("models must be a ModelList or a list of Model instances/dictionaries")

    @field_validator("resource_pools", mode="before")
    @classmethod
    def normalize_resource_pools(cls, value):
        if isinstance(value, ResourcePoolList):
            return value
        elif isinstance(value, list):
            return ResourcePoolList(resource_pools=[ResourcePool.model_validate(item) if isinstance(item, dict) else item for item in value])
        return value

    @model_validator(mode="after")
    def validate_resource_pools_unique_names(self):
        if self.resource_pools:
            pools = self.resource_pools.resource_pools if isinstance(self.resource_pools, ResourcePoolList) else self.resource_pools
            names = [pool.name for pool in pools]
            if len(names) != len(set(names)):
                raise ValueError("Resource pool names must be unique within agentData")
        return self

    def to_dict(self):
        """
        Serializes the AgentData instance to a dictionary, ensuring each Model in models calls its to_dict method.

        :return: dict - A dictionary representation of the agent data with aliases.
        """
        result = {
            "prompt": self.prompt.to_dict(),
            "llmConfig": self.llm_config.to_dict(),
            "models": self.models.to_dict(),
            "resourcePools": [pool.to_dict() for pool in self.resource_pools] if self.resource_pools else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class Agent(CustomBaseModel):
    """
    Represents an agent configuration returned by the API.

    :param id: str - Unique identifier for the agent.
    :param status: Literal["active", "inactive"] - Current status of the agent.
    :param name: str - Name of the agent.
    :param access_scope: Literal["public", "private"] - Access scope of the agent.
    :param public_name: Optional[str] - Public identifier for the agent, required if access_scope is "public".
    :param avatar_image: Optional[str] - URL to the agent's avatar image.
    :param description: str - Description of the agent's purpose.
    :param job_description: Optional[str] - Detailed job description of the agent.
    :param is_draft: bool - Indicates if the agent is in draft mode.
    :param is_readonly: bool - Indicates if the agent is read-only.
    :param revision: int - Revision number of the agent.
    :param version: Optional[int] - Version number of the agent, if applicable.
    :param agent_data: AgentData - Detailed configuration data for the agent.
    """
    id: str = Field(None, alias="id")
    status: Optional[Literal["active", "inactive", "pending"]] = Field("active", alias="status")
    name: str = Field(..., alias="name")
    access_scope: Literal["public", "private"] = Field("private", alias="accessScope")
    public_name: Optional[str] = Field(None, alias="publicName")
    avatar_image: Optional[str] = Field(None, alias="avatarImage")
    description: Optional[str] = Field(None, alias="description")
    job_description: Optional[str] = Field(None, alias="jobDescription")
    is_draft: Optional[bool] = Field(True, alias="isDraft")
    is_readonly: Optional[bool] = Field(False, alias="isReadonly")
    revision: Optional[int] = Field(None, alias="revision")
    version: Optional[Union[int | float]] = Field(None, alias="version")
    agent_data: Optional[AgentData] = Field(None, alias="agentData")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        return value

    @field_validator("public_name")
    @classmethod
    def validate_public_name_format(cls, value: Optional[str], values: dict) -> Optional[str]:
        access_scope = values.data.get("access_scope", "private")
        if access_scope == "public" and not value:
            raise ValueError("public_name is required if access_scope is 'public'")
        if value and not all(c.isalnum() or c in ".-_" for c in value):
            raise ValueError("public_name must contain only letters, numbers, periods, dashes, or underscores")
        return value

    @model_validator(mode="after")
    def validate_agent_data_for_publication(self):
        if self.is_draft is False and self.agent_data:
            if not self.agent_data.models or len(self.agent_data.models) == 0:
                raise ValueError("At least one valid model must be provided in agent_data.models for publication")
            # if not (self.agent_data.prompt.instructions or self.agent_data.prompt.context): # TODO -> Review implementation of context vs instructions
            if not self.agent_data.prompt.instructions:
                raise ValueError("agent_data.prompt must have at least instructions for publication")
        return self

    @field_validator("agent_data", mode="before")
    @classmethod
    def normalize_agent_data(cls, value):
        if isinstance(value, dict):
            return AgentData.model_validate(value)
        return value

    @model_validator(mode="after")
    def check_public_name(self):
        """
        Validates that public_name is provided if access_scope is set to "public".

        :raises ValueError: If access_scope is "public" but public_name is missing.
        """
        if self.access_scope == "public" and not self.public_name:
            raise ValueError("public_name is required if access_scope is public")
        return self

    def to_dict(self):
        result = {
            "id": self.id,
            "status": self.status,
            "name": self.name,
            "accessScope": self.access_scope,
            "publicName": self.public_name,
            "avatarImage": self.avatar_image,
            "description": self.description,
            "jobDescription": self.job_description,
            "isDraft": self.is_draft,
            "isReadonly": self.is_readonly,
            "revision": self.revision,
            "version": self.version,
            "agentData": self.agent_data.to_dict() if self.agent_data else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class AgentList(CustomBaseModel):
    """
    Represents a list of agents returned by the API.

    :param agents: List[Agent] - List of agent configurations.
    """
    agents: List[Agent] = Field(..., alias="agents")

    @field_validator("agents", mode="before")
    @classmethod
    def normalize_agents(cls, value):
        if isinstance(value, list):
            return [Agent.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_list(self):
        return [agent.to_dict() for agent in self.agents] if self.agents else []

    def __getitem__(self, index: int) -> Agent:
        if self.agents is None:
            raise IndexError("AgentList is empty")
        return self.agents[index]

    def __len__(self) -> int:
        return len(self.agents) if self.agents else 0

    def __iter__(self):
        """Make AgentList iterable over its agents."""
        if self.agents is None:
            return iter([])
        return iter(self.agents)

    def append(self, item: Agent) -> None:
        """Append an Agent instance to the agents list."""
        if self.agents is None:
            self.agents = []
        self.agents.append(item)


class SharingLink(CustomBaseModel):
    """
    Represents a sharing link for an agent.

    :param agent_id: str - Unique identifier of the agent.
    :param api_token: str - API token associated with the sharing link.
    :param shared_link: str - The full URL of the sharing link.
    """
    agent_id: str = Field(..., alias="agentId", description="Unique identifier of the agent")
    api_token: str = Field(..., alias="apiToken", description="API token associated with the sharing link")
    shared_link: str = Field(..., alias="sharedLink", description="The full URL of the sharing link")

    def to_dict(self):
        """
        Serializes the SharingLink instance to a dictionary.

        :return: dict - A dictionary representation of the sharing link with aliases.
        """
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class ToolParameter(CustomBaseModel):
    """
    Represents a parameter for a tool.

    :param key: str - The identifier of the parameter.
    :param data_type: str - The data type of the parameter (e.g., "String").
    :param description: str - Description of the parameter's purpose.
    :param is_required: bool - Whether the parameter is required.
    :param type: Optional[str] - Type of parameter (e.g., "config"), defaults to None.
    :param from_secret: Optional[bool] - Whether the value comes from a secret manager, defaults to None.
    :param value: Optional[str] - The static value of the parameter, defaults to None.
    """
    key: str = Field(..., alias="key", description="The identifier of the parameter")
    data_type: str = Field(..., alias="dataType", description="The data type of the parameter (e.g., 'String')")
    description: str = Field(..., alias="description", description="Description of the parameter's purpose")
    is_required: bool = Field(..., alias="isRequired", description="Whether the parameter is required")
    type: Optional[Literal["config", "app", "context"]] = Field("app", alias="type", description="Type of parameter (e.g., 'config')")
    from_secret: Optional[bool] = Field(None, alias="fromSecret", description="Whether the value comes from a secret manager")
    value: Optional[str] = Field(None, alias="value", description="The static value of the parameter")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class ToolMessage(CustomBaseModel):
    """
    Represents a message (e.g., warning or error) in the tool response.

    :param description: str - Description of the message.
    :param type: str - Type of the message (e.g., "warning", "error").
    """
    description: str = Field(..., alias="description", description="Description of the message")
    type: str = Field(..., alias="type", description="Type of the message (e.g., 'warning', 'error')")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class Tool(CustomBaseModel):
    """
    Represents a tool configuration, used for both input and output.

    :param name: str - The name of the tool.
    :param description: str - Description of the tool's purpose.
    :param scope: str - The scope of the tool (e.g., "builtin", "external", "api").
    :param parameters: List[ToolParameter] - List of parameters required by the tool.
    :param access_scope: Optional[str] - The access scope of the tool ("public" or "private"), defaults to None.
    :param public_name: Optional[str] - Public name of the tool, required if access_scope is "public", defaults to None.
    :param icon: Optional[str] - URL for the tool's icon or avatar, defaults to None.
    :param open_api: Optional[str] - URL where the OpenAPI specification can be loaded, defaults to None.
    :param open_api_json: Optional[dict] - OpenAPI specification as a dictionary, defaults to None.
    :param report_events: Optional[str] - Event reporting mode ("None", "All", "Start", "Finish", "Progress"), defaults to None.
    :param id: Optional[str] - Unique identifier of the tool, defaults to None.
    :param is_draft: Optional[bool] - Whether the tool is in draft mode, defaults to None.
    :param messages: Optional[List[ToolMessage]] - List of messages (e.g., warnings or errors), defaults to None.
    :param revision: Optional[int] - Revision number of the tool, defaults to None.
    :param status: Optional[str] - Current status of the tool (e.g., "active"), defaults to None.
    """
    name: str = Field(..., alias="name", description="The name of the tool")
    description: Optional[str] = Field(None, alias="description", description="Description of the tool's purpose")
    scope: str = Field("builtin", alias="scope", description="The scope of the tool (e.g., 'builtin', 'external', 'api')")
    parameters: Optional[List[ToolParameter]] = Field(None, alias="parameters", description="List of parameters required by the tool")
    access_scope: Optional[str] = Field(None, alias="accessScope", description="The access scope of the tool ('public' or 'private')")
    public_name: Optional[str] = Field(None, alias="publicName", description="Public name of the tool, required if access_scope is 'public'")
    icon: Optional[str] = Field(None, alias="icon", description="URL for the tool's icon or avatar")
    open_api: Optional[str] = Field(None, alias="openApi", description="URL where the OpenAPI specification can be loaded")
    open_api_json: Optional[dict] = Field(None, alias="openApiJson", description="OpenAPI specification as a dictionary")
    report_events: Optional[Literal['None', 'All', 'Start', 'Finish', 'Progress']] = Field("None", alias="reportEvents", description="Event reporting mode ('None', 'All', 'Start', 'Finish', 'Progress')")
    id: Optional[str] = Field(None, alias="id", description="Unique identifier of the tool")
    is_draft: Optional[bool] = Field(None, alias="isDraft", description="Whether the tool is in draft mode")
    messages: Optional[List[ToolMessage]] = Field(None, alias="messages", description="List of messages (e.g., warnings or errors)")
    revision: Optional[int] = Field(None, alias="revision", description="Revision number of the tool")
    status: Optional[str] = Field(None, alias="status", description="Current status of the tool (e.g., 'active')")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        if not re.match(r'^[A-Za-z0-9_-]{1,64}$', value):
            raise ValueError(
                "name must contain only letters, numbers, underscores, or hyphens, and be 1-64 characters long")
        return value

    @field_validator("public_name")
    @classmethod
    def validate_public_name_format(cls, value: Optional[str], values: dict) -> Optional[str]:
        access_scope = values.data.get("access_scope", "private")
        if access_scope == "public" and not value:
            raise ValueError("public_name is required if access_scope is 'public'")
        if value and not all(c.isalnum() or c in ".-_" for c in value):
            raise ValueError("public_name must contain only letters, numbers, periods, dashes, or underscores")
        return value

    @model_validator(mode="after")
    def check_public_name(self):
        if self.access_scope == "public" and not self.public_name:
            raise ValueError("public_name is required if access_scope is 'public'")
        return self

    '''
    @model_validator(mode="after")
    def validate_api_tool_requirements(self):
        if self.scope == "api" and not (self.open_api or self.open_api_json):
            raise ValueError("For scope='api', either open_api or open_api_json must be provided")
        if self.parameters:
            param_keys = [p.key for p in self.parameters]
            if len(param_keys) != len(set(param_keys)):
                raise ValueError("All parameter keys must be unique within the tool")
        return self
    '''

    @field_validator("parameters", mode="before")
    @classmethod
    def normalize_parameters(cls, value):
        if isinstance(value, list):
            return [ToolParameter.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("messages", mode="before")
    @classmethod
    def normalize_messages(cls, value):
        if isinstance(value, list):
            return [ToolMessage.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "name": self.name,
            "description": self.description,
            "scope": self.scope,
            "parameters": [param.to_dict() for param in self.parameters] if self.parameters else None,
            "accessScope": self.access_scope,
            "publicName": self.public_name,
            "icon": self.icon,
            "openApi": self.open_api,
            "openApiJson": self.open_api_json,
            "reportEvents": self.report_events,
            "id": self.id,
            "isDraft": self.is_draft,
            "messages": [msg.to_dict() for msg in self.messages] if self.messages else None,
            "revision": self.revision,
            "status": self.status
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class ToolList(CustomBaseModel):
    """
    Represents a list of Tool objects retrieved from an API response.

    :param tools: List[Tool] - The list of tools.
    """
    tools: List[Tool] = Field(..., alias="tools", description="The list of tools")

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, value):
        if isinstance(value, list):
            return [Tool.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return {"tools": [tool.to_dict() for tool in self.tools]}

    def __str__(self):
        return str(self.to_dict())

    def __getitem__(self, index: int) -> Tool:
        if self.tools is None:
            raise IndexError("ToolList is empty")
        return self.tools[index]

    def __len__(self) -> int:
        return len(self.tools) if self.tools else 0

    def __iter__(self):
        """Make ToolList iterable over its tools."""
        if self.tools is None:
            return iter([])
        return iter(self.tools)

    def append(self, item: Tool) -> None:
        """Append a Tool instance to the tools list."""
        if self.tools is None:
            self.tools = []
        self.tools.append(item)


class LocalizedDescription(CustomBaseModel):
    """
    Represents a localized description for a reasoning strategy.

    :param language: str - The language of the description (e.g., "english", "spanish").
    :param description: str - The description text in the specified language.
    """
    language: str = Field(..., description="The language of the description")
    description: str = Field(..., description="The description text in the specified language")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class ReasoningStrategy(CustomBaseModel):
    """
    Represents a reasoning strategy configuration.

    :param name: str - The name of the reasoning strategy.
    :param system_prompt: str - The system prompt for the reasoning strategy.
    :param access_scope: str - The access scope of the strategy (e.g., "private", "public").
    :param type: str - The type of the reasoning strategy (e.g., "addendum").
    :param localized_descriptions: List[LocalizedDescription] - List of localized descriptions.
    :param id: Optional[str] - Unique identifier of the strategy, set by the API on creation.
    """
    name: str = Field(..., description="The name of the reasoning strategy")
    system_prompt: Optional[str] = Field(None, alias="systemPrompt", description="The system prompt for the reasoning strategy")
    access_scope: str = Field(..., alias="accessScope", description="The access scope of the strategy (e.g., 'private', 'public')")
    type: str = Field(..., description="The type of the reasoning strategy (e.g., 'addendum')")
    localized_descriptions: Optional[List[LocalizedDescription]] = Field(None, alias="localizedDescriptions", description="List of localized descriptions")
    id: Optional[str] = Field(None, description="Unique identifier of the strategy, set by the API on creation")

    @field_validator("localized_descriptions", mode="before")
    @classmethod
    def normalize_localized_descriptions(cls, value):
        if isinstance(value, list):
            return [LocalizedDescription.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "name": self.name,
            "systemPrompt": self.system_prompt,
            "accessScope": self.access_scope,
            "type": self.type,
            "localizedDescriptions": [desc.to_dict() for desc in self.localized_descriptions] if isinstance(self.localized_descriptions, list) else None,
            "id": self.id
        }
        return {k: v for k, v in result.items() if v is not None}


class ReasoningStrategyList(CustomBaseModel):
    strategies: List[ReasoningStrategy] = Field(..., alias="strategies", description="The list of reasoning strategies")

    @field_validator("strategies", mode="before")
    @classmethod
    def normalize_strategies(cls, value):
        if isinstance(value, list):
            return [ReasoningStrategy.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [strategy.to_dict() for strategy in self.strategies]

    def __str__(self):
        return str(self.to_dict())

    def __getitem__(self, index: int) -> ReasoningStrategy:
        if self.strategies is None:
            raise IndexError("ReasoningStrategyList is empty")
        return self.strategies[index]

    def __len__(self) -> int:
        return len(self.strategies) if self.strategies else 0

    def __iter__(self):
        """Make ReasoningStrategyList iterable over its strategies."""
        if self.strategies is None:
            return iter([])
        return iter(self.strategies)

    def append(self, item: ReasoningStrategy) -> None:
        """Append a ReasoningStrategy instance to the strategies list."""
        if self.strategies is None:
            self.strategies = []
        self.strategies.append(item)


class KnowledgeBase(CustomBaseModel):
    id: Optional[str] = Field(None, description="Unique identifier of the knowledge base, set by API")
    name: str = Field(..., description="Name of the knowledge base")
    artifact_type_name: Optional[List[str]] = Field(None, alias="artifactTypeName", description="List of artifact type names")
    artifacts: Optional[List[str]] = Field(None, description="List of artifact identifiers")
    metadata: Optional[List[str]] = Field(None, description="List of metadata identifiers")

    @field_validator("artifacts")
    @classmethod
    def validate_artifacts(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None:
            for artifact in value:
                if not artifact.strip():
                    raise ValueError("Artifact identifiers cannot be empty")
        return value

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, value: Optional[List[str]]) -> Optional[List[str]]:
        if value is not None:
            for meta in value:
                if not meta.strip():
                    raise ValueError("Metadata identifiers cannot be empty")
        return value

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class KnowledgeBaseList(CustomBaseModel):
    knowledge_bases: List[KnowledgeBase] = Field(..., alias="knowledgeBases")

    @field_validator("knowledge_bases", mode="before")
    @classmethod
    def normalize_knowledge_bases(cls, value):
        if isinstance(value, list):
            return [KnowledgeBase.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [kb.to_dict() for kb in self.knowledge_bases]

    def __getitem__(self, index: int) -> KnowledgeBase:
        if self.knowledge_bases is None:
            raise IndexError("KnowledgeBaseList is empty")
        return self.knowledge_bases[index]

    def __len__(self) -> int:
        return len(self.knowledge_bases) if self.knowledge_bases else 0

    def __iter__(self):
        """Make KnowledgeBaseList iterable over its knowledge bases."""
        if self.knowledge_bases is None:
            return iter([])
        return iter(self.knowledge_bases)

    def append(self, item: KnowledgeBase) -> None:
        """Append a KnowledgeBase instance to the knowledge_bases list."""
        if self.knowledge_bases is None:
            self.knowledge_bases = []
        self.knowledge_bases.append(item)


class AgenticActivity(CustomBaseModel):
    key: str = Field(..., description="Unique key for the activity")
    name: str = Field(..., description="Name of the activity")
    task_name: str = Field(..., alias="taskName", description="Name of the task")
    agent_name: str = Field(..., alias="agentName", description="Name of the agent")
    agent_revision_id: int = Field(..., alias="agentRevisionId", description="Revision ID of the agent")
    agent_id: Optional[str] = Field(None, alias="agentId", description="Unique identifier of the agent, set by API")
    task_id: Optional[str] = Field(None, alias="taskId", description="Unique identifier of the task, set by API")
    task_revision_id: Optional[int] = Field(None, alias="taskRevisionId", description="Revision ID of the task, set by API")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class ArtifactSignal(CustomBaseModel):
    key: str = Field(..., description="Unique key for the artifact signal")
    name: str = Field(..., description="Name of the artifact signal")
    handling_type: str = Field(..., alias="handlingType", description="Handling type (e.g., 'C')")
    artifact_type_name: List[str] = Field(..., alias="artifactTypeName", description="List of artifact type names")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class UserSignal(CustomBaseModel):
    key: str = Field(..., description="Unique key for the user signal")
    name: str = Field(..., description="Name of the user signal")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class Event(CustomBaseModel):
    key: str = Field(..., description="Unique key for the event")
    name: str = Field(..., description="Name of the event")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class SequenceFlow(CustomBaseModel):
    key: str = Field(..., description="Unique key for the sequence flow")
    source_key: str = Field(..., alias="sourceKey", description="Key of the source event/activity/signal")
    target_key: str = Field(..., alias="targetKey", description="Key of the target event/activity/signal")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class Variable(CustomBaseModel):
    key: str = Field(..., description="Key of the variable")
    value: str = Field(..., description="Value of the variable")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)


class VariableList(CustomBaseModel):
    variables: Optional[List[Variable]] = Field(None, description="List of variables")

    @field_validator("variables", mode="before")
    @classmethod
    def normalize_variables(cls, value):
        if isinstance(value, list):
            return [Variable.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [var.to_dict() for var in self.variables] if self.variables else None

    def __getitem__(self, index: int) -> Variable:
        if self.variables is None:
            raise IndexError("VariableList is empty")
        return self.variables[index]

    def __len__(self) -> int:
        return len(self.variables) if self.variables else 0

    def __iter__(self) -> Iterator[Variable]:
        """Make VariableList iterable over its variables."""
        if self.variables is None:
            return iter([])
        return iter(self.variables)

    def append(self, item: Variable) -> None:
        """Append a Variable instance to the variables list."""
        if self.variables is None:
            self.variables = []
        self.variables.append(item)


class AgenticProcess(CustomBaseModel):
    key: Optional[str] = Field(None, description="Unique key for the process")
    name: str = Field(..., description="Name of the process")
    description: Optional[str] = Field(None, description="Description of the process")
    kb: Optional[KnowledgeBase] = Field(None, description="Knowledge base configuration")
    agentic_activities: Optional[List[AgenticActivity]] = Field(None, alias="agenticActivities", description="List of agentic activities")
    artifact_signals: Optional[List[ArtifactSignal]] = Field(None, alias="artifactSignals", description="List of artifact signals")
    user_signals: Optional[List[UserSignal]] = Field(None, alias="userSignals", description="List of user signals")
    start_event: Optional[Event] = Field(None, alias="startEvent", description="Start event of the process")
    end_event: Optional[Event] = Field(None, alias="endEvent", description="End event of the process")
    sequence_flows: Optional[List[SequenceFlow]] = Field(None, alias="sequenceFlows", description="List of sequence flows")
    variables: Optional[VariableList] = Field(None, alias="variables", description="List of variables")
    id: Optional[str] = Field(None, description="Unique identifier of the process, set by API")
    status: Optional[str] = Field(None, alias="status", description="Status of the process (e.g., 'active')")
    version_id: Optional[int] = Field(None, alias="versionId", description="Version ID of the process")
    is_draft: Optional[bool] = Field(None, alias="isDraft", description="Whether the process is a draft")
    revision: Optional[int] = Field(None, description="Revision number of the process")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("name cannot contain ':' or '/'")
        return value

    @field_validator("kb", mode="before")
    @classmethod
    def normalize_kb(cls, value):
        if isinstance(value, dict):
            return KnowledgeBase.model_validate(value)
        return value

    @field_validator("agentic_activities", mode="before")
    @classmethod
    def normalize_agentic_activities(cls, value):
        if isinstance(value, list):
            return [AgenticActivity.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("artifact_signals", mode="before")
    @classmethod
    def normalize_artifact_signals(cls, value):
        if isinstance(value, list):
            return [ArtifactSignal.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("user_signals", mode="before")
    @classmethod
    def normalize_user_signals(cls, value):
        if isinstance(value, list):
            return [UserSignal.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("start_event", mode="before")
    @classmethod
    def normalize_start_event(cls, value):
        if isinstance(value, dict):
            return Event.model_validate(value)
        return value

    @field_validator("end_event", mode="before")
    @classmethod
    def normalize_end_event(cls, value):
        if isinstance(value, dict):
            return Event.model_validate(value)
        return value

    @field_validator("sequence_flows", mode="before")
    @classmethod
    def normalize_sequence_flows(cls, value):
        if isinstance(value, list):
            return [SequenceFlow.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("variables", mode="before")
    @classmethod
    def normalize_variables(cls, value):
        """
        Normalizes the variables input to a VariableList instance.

        :param value: Union[VariableList, List[Variable]] - The input value for variables.
        :return: VariableList - A VariableList instance containing the models.
        """
        if isinstance(value, VariableList):
            return value
        elif isinstance(value, (list, tuple)):
            return VariableList(variables=[Variable.model_validate(item) if isinstance(item, dict) else item for item in value])
        elif value is None:
            return VariableList(variables=[])

        raise ValueError("variables must be a VariableList or a list of Variable instances")

    def to_dict(self):
        """
        Serializes the AgenticProcess instance to a dictionary, explicitly mapping fields to their aliases
        and invoking to_dict for nested objects in lists.

        :return: dict - A dictionary representation of the process with aliases, excluding None values.
        """
        result = {
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "kb": self.kb.to_dict() if self.kb else None,
            "agenticActivities": [activity.to_dict() for activity in self.agentic_activities] if self.agentic_activities else None,
            "artifactSignals": [signal.to_dict() for signal in self.artifact_signals] if self.artifact_signals else None,
            "userSignals": [signal.to_dict() for signal in self.user_signals] if self.user_signals else None,
            "startEvent": self.start_event.to_dict() if self.start_event else None,
            "endEvent": self.end_event.to_dict() if self.end_event else None,
            "sequenceFlows": [flow.to_dict() for flow in self.sequence_flows] if self.sequence_flows else None,
            "variables": self.variables.to_dict() if self.variables else None,
            "id": self.id,
            "status": self.status,
            "versionId": self.version_id,
            "isDraft": self.is_draft,
            "revision": self.revision
        }
        return {k: v for k, v in result.items() if v is not None}


class ArtifactType(CustomBaseModel):
    """
    Represents an artifact type configuration for a task.

    :param name: str - Name of the artifact type.
    :param description: str - Description of the artifact type.
    :param is_required: bool - Whether the artifact is required.
    :param usage_type: str - Usage type of the artifact (e.g., 'input', 'output').
    :param artifact_variable_key: str - Variable key for the artifact in the task.
    """
    name: str = Field(..., alias="name", description="Name of the artifact type")
    description: Optional[str] = Field(None, alias="description", description="Description of the artifact type")
    is_required: Optional[bool] = Field(False, alias="isRequired", description="Whether the artifact is required")
    usage_type: str = Field(..., alias="usageType", description="Usage type of the artifact (e.g., 'input', 'output')")
    artifact_variable_key: Optional[str] = Field(None, alias="artifactVariableKey", description="Variable key for the artifact in the task")

    def to_dict(self):
        """
        Serializes the ArtifactType instance to a dictionary.

        :return: dict - A dictionary representation of the artifact type with aliases.
        """
        return self.model_dump(by_alias=True, exclude_none=True)


class ArtifactTypeList(CustomBaseModel):
    """
    Represents a list of ArtifactType objects.

    :param artifact_types: List[ArtifactType] - The list of artifact types.
    """
    artifact_types: Optional[List[ArtifactType]] = Field(None, description="List of artifact types")

    @field_validator("artifact_types", mode="before")
    @classmethod
    def normalize_artifact_types(cls, value):
        if isinstance(value, list):
            return [ArtifactType.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        """
        Serializes the ArtifactTypeList instance to a list of dictionaries.

        :return: List[dict] - A list of dictionary representations of the artifact types.
        """
        return [artifact.to_dict() for artifact in self.artifact_types] if self.artifact_types else None

    def __getitem__(self, index: int) -> ArtifactType:
        if self.artifact_types is None:
            raise IndexError("ArtifactTypeList is empty")
        return self.artifact_types[index]

    def __len__(self) -> int:
        return len(self.artifact_types) if self.artifact_types else 0

    def __iter__(self) -> Iterator[ArtifactType]:
        """Make ArtifactTypeList iterable over its artifact_types."""
        if self.artifact_types is None:
            return iter([])
        return iter(self.artifact_types)

    def append(self, item: ArtifactType) -> None:
        """Append an ArtifactType instance to the artifact_types list."""
        if self.artifact_types is None:
            self.artifact_types = []
        self.artifact_types.append(item)


class Task(CustomBaseModel):
    """
    Represents a task configuration used for both input and output.

    :param name: str - Required name of the task, must be unique within the project and exclude ':' or '/'.
    :param description: Optional[str] - Description of what the task does, for user understanding (not used by agents).
    :param title_template: Optional[str] - Template for naming task instances (e.g., 'specs for {{issue}}').
    :param id: Optional[str] - Unique identifier of the task, set by API or provided in insert mode for custom ID.
    :param prompt_data: Optional[Prompt] - Prompt configuration (same structure as AgentData prompt), combined with agent prompt during execution.
    :param artifact_types: Optional[List[dict]] - List of artifact types with 'name', 'description', 'isRequired', 'usageType', and 'artifactVariableKey'.
    :param is_draft: Optional[bool] - Whether the task is in draft mode.
    :param revision: Optional[int] - Revision number of the task.
    :param status: Optional[str] - Current status of the task (e.g., 'active').
    """
    name: str = Field(..., description="Name of the task")
    description: Optional[str] = Field(None, description="Description of the task")
    title_template: Optional[str] = Field(None, alias="titleTemplate", description="Title template for the task")
    id: Optional[str] = Field(None, description="Unique identifier of the task, set by API")
    prompt_data: Optional[Prompt] = Field(None, alias="promptData", description="Prompt configuration for the task, combined with agent prompt during execution")
    artifact_types: Optional[Union[List[Dict[str, Any]], List[ArtifactType], ArtifactTypeList]] = Field(None, alias="artifactTypes", description="List of artifact types for the task")
    is_draft: Optional[bool] = Field(None, alias="isDraft", description="Whether the task is a draft")
    revision: Optional[int] = Field(None, description="Revision number of the task")
    status: Optional[str] = Field(None, description="Status of the task (e.g., 'active')")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Ensures the task name does not contain forbidden characters ':' or '/'.

        :param value: str - The name to validate.
        :return: str - The validated name.
        :raises ValueError: If the name contains ':' or '/'.
        """
        if not value.strip():
            raise ValueError("name cannot be blank")
        if ":" in value or "/" in value:
            raise ValueError("Task name cannot contain ':' or '/'")
        return value

    @field_validator("prompt_data", mode="before")
    @classmethod
    def normalize_prompt_data(cls, value: Union[Prompt, Dict[str, Any], None]) -> Optional[Prompt]:
        """
        Normalizes the prompt_data input to a Prompt instance.

        :param value: Union[Prompt, Dict[str, Any], None] - The input value for prompt_data.
        :return: Optional[Prompt] - A Prompt instance or None if the input is None.
        :raises ValueError: If the value is neither a Prompt, dict, nor None.
        """
        if isinstance(value, Prompt):
            return value
        elif isinstance(value, dict):
            return Prompt.model_validate(value)
        elif value is None:
            return None
        raise ValueError("prompt_data must be a Prompt instance, a dictionary, or None")

    @field_validator("artifact_types", mode="before")
    @classmethod
    def normalize_artifact_types(cls, value: Union[List[Dict[str, Any]], List[ArtifactType], ArtifactTypeList, None]) ->  Optional[ArtifactTypeList]:
        """
        Normalizes the artifact_types input to an ArtifactTypeList instance.

        :param value: Union[List[Dict[str, Any]], List[ArtifactType], ArtifactTypeList, None] - The input value for artifact_types.
        :return: Optional[ArtifactTypeList] - An ArtifactTypeList instance or None if the input is None.
        :raises ValueError: If the value is not a valid input type.
        """
        if isinstance(value, ArtifactTypeList):
            return value
        elif isinstance(value, list):
            artifact_list = []
            for item in value:
                if isinstance(item, dict):
                    artifact_list.append(ArtifactType.model_validate(item))
                elif isinstance(item, ArtifactType):
                    artifact_list.append(item)
                else:
                    raise ValueError("artifact_types list items must be dictionaries or ArtifactType instances")
            return ArtifactTypeList(artifact_types=artifact_list)
        elif value is None:
            return None
        raise ValueError("artifact_types must be an ArtifactTypeList, a list of dictionaries/ArtifactType, or None")

    @model_validator(mode="after")
    def validate_artifact_types_constraints(self):
        if self.artifact_types and self.artifact_types.artifact_types:
            for artifact in self.artifact_types.artifact_types:
                if artifact.artifact_variable_key and len(artifact.artifact_variable_key) > 20:
                    raise ValueError(
                        f"artifactVariableKey '{artifact.artifact_variable_key}' must be 20 characters or less")
                if artifact.usage_type not in ["input", "output"]:
                    raise ValueError(f"usageType must be 'input' or 'output', got '{artifact.usage_type}'")
        return self

    def to_dict(self):
        """
        Serializes the Task instance to a dictionary, using aliases and excluding None values.

        :return: dict - A dictionary representation of the task configuration.
        """
        result = {
            "name": self.name,
            "description": self.description,
            "titleTemplate": self.title_template,
            "id": self.id,
            "promptData": self.prompt_data.to_dict() if self.prompt_data else None,
            "artifactTypes": self.artifact_types.to_dict() if self.artifact_types else None,
            "isDraft": self.is_draft,
            "revision": self.revision,
            "status": self.status
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class AgenticProcessList(CustomBaseModel):
    processes: List[AgenticProcess] = Field(..., alias="processes", description="List of agentic processes")

    @field_validator("processes", mode="before")
    @classmethod
    def normalize_processes(cls, value):
        if isinstance(value, list):
            return [AgenticProcess.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return {"processes": [process.to_dict() for process in self.processes]}

    def __getitem__(self, index: int) -> AgenticProcess:
        if self.processes is None:
            raise IndexError("AgenticProcessList is empty")
        return self.processes[index]

    def __len__(self) -> int:
        return len(self.processes) if self.processes else 0

    def __iter__(self):
        """Make AgenticProcessList iterable over its processes."""
        if self.processes is None:
            return iter([])
        return iter(self.processes)

    def append(self, item: AgenticProcess) -> None:
        """Append an AgenticProcess instance to the processes list."""
        if self.processes is None:
            self.processes = []
        self.processes.append(item)


class TaskList(CustomBaseModel):
    tasks: List[Task] = Field(..., alias="tasks", description="List of tasks")

    @field_validator("tasks", mode="before")
    @classmethod
    def normalize_tasks(cls, value):
        if isinstance(value, list):
            return [Task.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [task.to_dict() for task in self.tasks]

    def __getitem__(self, index: int) -> Task:
        if self.tasks is None:
            raise IndexError("TaskList is empty")
        return self.tasks[index]

    def __len__(self) -> int:
        return len(self.tasks) if self.tasks else 0

    def __iter__(self):
        """Make TaskList iterable over its tasks."""
        if self.tasks is None:
            return iter([])
        return iter(self.tasks)

    def append(self, item: Task) -> None:
        """Append a Task instance to the tasks list."""
        if self.tasks is None:
            self.tasks = []
        self.tasks.append(item)


class ProcessInstance(CustomBaseModel):
    id: Optional[str] = Field(None, alias="id", description="Unique identifier of the process instance, set by API")
    process: AgenticProcess = Field(..., alias="process", description="The process configuration")
    created_at: Optional[str] = Field(None, alias="createdAt", description="Timestamp when the instance was created")
    subject: str = Field(..., description="Subject of the instance")
    variables: Optional[Union[List[Variable] | VariableList]] = Field(None, alias="variables", description="List of instance variables")
    status: Optional[str] = Field(None, description="Status of the instance (e.g., 'active', 'completed')")

    @field_validator("process", mode="before")
    @classmethod
    def normalize_process(cls, value):
        """
        Normalizes the process input to an AgenticProcess instance if it's a dictionary.

        :param value: The input value for process (dict or AgenticProcess).
        :return: AgenticProcess - An AgenticProcess instance.
        :raises ValueError: If the value is neither a dict nor an AgenticProcess.
        """
        if isinstance(value, dict):
            return AgenticProcess.model_validate(value)
        elif isinstance(value, AgenticProcess):
            return value
        raise ValueError("process must be a dictionary or an AgenticProcess instance")

    @field_validator("variables", mode="before")
    @classmethod
    def normalize_variables(cls, value):
        """
        Normalizes the variables input to a VariableList instance.

        :param value: Union[VariableList, List[Variable]] - The input value for variables.
        :return: VariableList - A VariableList instance containing the models.
        """
        if isinstance(value, VariableList):
            return value
        elif isinstance(value, (list, tuple)):
            return VariableList(variables=[Variable.model_validate(item) if isinstance(item, dict) else item for item in value])
        elif value is None:
            return VariableList(variables=[])

        raise ValueError("variables must be a VariableList or a list of Variable instances")

    def to_dict(self):
        result = {
            "id": self.id,
            "process": self.process.to_dict() if self.process else None,
            "createdAt": self.created_at,
            "subject": self.subject,
            "variables": self.variables.to_dict() if self.variables else None,
            "status": self.status,
        }
        return {k: v for k, v in result.items() if v is not None}


class ProcessInstanceList(CustomBaseModel):
    instances: List[ProcessInstance] = Field(..., alias="instances", description="List of process instances")

    @field_validator("instances", mode="before")
    @classmethod
    def normalize_instances(cls, value):
        if isinstance(value, list):
            return [ProcessInstance.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [instance.to_dict() for instance in self.instances] if self.instances else None

    def __getitem__(self, index: int) -> ProcessInstance:
        if self.instances is None:
            raise IndexError("ProcessInstanceList is empty")
        return self.instances[index]

    def __len__(self) -> int:
        return len(self.instances) if self.instances else 0

    def __iter__(self):
        """Make ProcessInstanceList iterable over its instances."""
        if self.instances is None:
            return iter([])
        return iter(self.instances)

    def append(self, item: ProcessInstance) -> None:
        """Append a ProcessInstance instance to the instances list."""
        if self.instances is None:
            self.instances = []
        self.instances.append(item)


class JobParameter(CustomBaseModel):
    """
    Represents a parameter for a job.

    :param Name: str - The name of the parameter.
    :param Value: str - The value of the parameter.
    """
    Name: str = Field(..., alias="Name", description="The name of the parameter")
    Value: str = Field(..., alias="Value", description="The value of the parameter")

    @field_validator("Name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Parameter name cannot be blank")
        return value

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class Job(CustomBaseModel):
    """
    Represents a single job configuration returned by the API.

    :param caption: str - Description of the job's status and completion time.
    :param name: str - Name of the job (e.g., 'execute_workitem_jobrunner', 'publish_artifact').
    :param parameters: List[JobParameter] - List of parameters for the job.
    :param request: str - Timestamp when the job was requested.
    :param token: str - Unique token identifier for the job.
    :param topic: str - Topic associated with the job (e.g., 'Default', 'Event').
    :param info: Optional[str] - Additional information, typically for failed jobs.
    """
    caption: str = Field(..., alias="caption", description="Description of the job's status and completion time")
    name: str = Field(..., alias="name", description="Name of the job")
    parameters: Optional[List[JobParameter]] = Field([], alias="parameters", description="List of parameters for the job")
    request: str = Field(..., alias="request", description="Timestamp when the job was requested")
    token: str = Field(..., alias="token", description="Unique token identifier for the job")
    topic: str = Field(..., alias="topic", description="Topic associated with the job")
    info: Optional[str] = Field(None, alias="info", description="Additional information, typically for failed jobs")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Job name cannot be blank")
        return value

    @field_validator("token")
    @classmethod
    def validate_token(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Token cannot be blank")
        return value

    @field_validator("parameters", mode="before")
    @classmethod
    def normalize_parameters(cls, value):
        if isinstance(value, list):
            return [JobParameter.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        result = {
            "caption": self.caption,
            "name": self.name,
            "parameters": [param.to_dict() for param in self.parameters] if self.parameters else [],
            "request": self.request,
            "token": self.token,
            "topic": self.topic,
            "info": self.info
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        return str(self.to_dict())


class JobList(CustomBaseModel):
    """
    Represents a list of jobs returned by the API.

    :param jobs: List[Job] - List of job configurations.
    """
    jobs: List[Job] = Field(..., alias="jobs", description="List of job configurations")

    @field_validator("jobs", mode="before")
    @classmethod
    def normalize_jobs(cls, value):
        if isinstance(value, list):
            return [Job.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_dict(self):
        return [job.to_dict() for job in self.jobs]

    def __getitem__(self, index: int) -> Job:
        if self.jobs is None:
            raise IndexError("JobList is empty")
        return self.jobs[index]

    def __len__(self) -> int:
        return len(self.jobs) if self.jobs else 0

    def __iter__(self):
        """Make JobList iterable over its jobs."""
        if self.jobs is None:
            return iter([])
        return iter(self.jobs)

    def append(self, item: Job) -> None:
        """Append a Job instance to the jobs list."""
        if self.jobs is None:
            self.jobs = []
        self.jobs.append(item)