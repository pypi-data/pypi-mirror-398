from datetime import datetime

from pydantic import Field, field_validator, model_validator
from typing import Optional, Literal, Any, List, Union, Iterator

from pygeai.core import CustomBaseModel

"""
In this modeling, the model_validate method from pydantic is dependant on the API REST responses from
the GEAI platform.
It's not expected that the user creates a dictionary to populate the models. If they wish to do so, they
should rely on the GEAI documentation to structure the dictionaries as API responses.
"""


class AssistantRevisionMetadata(CustomBaseModel):
    """
    {
      "key": "string",
      "type": "string",
      "value": "string"
    }
    """
    key: str = Field(..., alias="key")
    type: str = Field(..., alias="type")
    value: str = Field(..., alias="value")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class AssistantRevision(CustomBaseModel):
    """
    {
      "metadata": [
        ...
      ],
      "modelId": "string",
      "modelName": "string",
      "prompt": "string",
      "providerName": "string",
      "revisionDescription": "string",
      "revisionId": "string",
      "revisionName": "string",
      "timestamp": "timestamp"
    }
    """
    metadata: Optional[list[AssistantRevisionMetadata]] = Field(default_factory=list, alias="metadata")
    model_id: Optional[str] = Field(None, alias="modelId")
    model_name: Optional[str] = Field(None, alias="modelName")
    prompt: Optional[str] = Field(None, alias="prompt")
    provider_name: Optional[str] = Field(None, alias="providerName")
    revision_description: Optional[str] = Field(None, alias="revisionDescription")
    revision_id: Optional[int] = Field(None, alias="revisionId")
    revision_name: str = Field(..., alias="revisionName")
    timestamp: Optional[datetime] = Field(None, alias="timestamp")

    class Config:
        protected_namespaces = ()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        return value

    @field_validator("metadata", mode="before")
    @classmethod
    def normalize_metadata(cls, value):
        if isinstance(value, list):
            return [AssistantRevisionMetadata.model_validate(item) if isinstance(item, dict) else item for item in
                    value]
        return value

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class AssistantIntent(CustomBaseModel):
    """
    DEPRECATED: It's ignored in the modeling of the responses, since it's added complexity
    that doesn't provide any benefit. From assistant, there will be a direct relationship
    to revisions.
    {
          "assistantIntentDefaultRevision": "number",
          "assistantIntentDescription": "string",
          "assistantIntentId": "string",
          "assistantIntentName": "string",
          "revisions": [
            ...
          ]
        }
    """
    default_revision: float
    description: str
    id: str
    name: str
    revisions: Optional[list[AssistantRevision]] = []

    def __str__(self):
        intent = {
            "assistantIntentDefaultRevision": self.default_revision,
            "assistantIntentDescription": self.description,
            "assistantIntentId": self.id,
            "assistantIntentName": self.name
        }
        if any(self.revisions):
            intent["revisions"] = self.revisions

        return str(intent)


class Organization(CustomBaseModel):
    id: Optional[str] = Field(None, alias="organizationId")
    name: Optional[str] = Field(None, alias="organizationName")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        organization = self.to_dict()
        return str(organization)


class SearchProfile(CustomBaseModel):
    """
     {
      "name": "string",
      "description": "string"
    }
    """
    name: str = Field(..., alias="name")
    description: str = Field(..., alias="description")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        search_profile = self.to_dict()
        return str(search_profile)


class ProjectToken(CustomBaseModel):
    """
     {
      "description": "string",
      "id": "string",
      "name": "string",
      "status": "string", /* Active, Blocked */
      "timestamp": "timestamp"
    }
    """
    description: Optional[str] = Field(None, alias="description")
    token_id: str = Field(..., alias="id")
    name: str = Field(..., alias="name")
    status: str = Field(..., alias="status")
    timestamp: datetime = Field(..., alias="timestamp")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        token = self.to_dict()
        return str(token)


class UsageLimit(CustomBaseModel):
    """
    "hardLimit": "number",                // Upper usage limit
    "id": "string",                       // Usage limit ID
    "relatedEntityName": "string",        // Name of the related entity
    "remainingUsage": "number",           // Remaining usage
    "renewalStatus": "string",            // Renewal status (Renewable, NonRenewable)
    "softLimit": "number",                // Lower usage limit
    "status": "integer",                  // Status (1: Active, 2: Expired, 3: Empty, 4: Cancelled)
    "subscriptionType": "string",         // Subscription type (Freemium, Daily, Weekly, Monthly)
    "usageUnit": "string",                // Usage unit (Requests, Cost)
    "usedAmount": "number",               // Amount used (decimal or scientific notation)
    "validFrom": "timestamp",             // Start date of the usage limit
    "validUntil": "timestamp"             // Expiration or renewal date
    """
    hard_limit: Optional[float] = Field(None, alias="hardLimit")
    id: Optional[str] = Field(None, alias="id")
    related_entity_name: Optional[str] = Field(None, alias="relatedEntityName")
    remaining_usage: Optional[float] = Field(None, alias="remainingUsage")
    renewal_status: Optional[Literal["Renewable", "NonRenewable"]] = Field(None, alias="renewalStatus")
    soft_limit: Optional[float] = Field(None, alias="softLimit")
    status: Optional[Literal[1, 2, 3, 4]] = Field(None, alias="status")
    subscription_type: Optional[Literal["Freemium", "Daily", "Weekly", "Monthly"]] = Field(None, alias="subscriptionType")
    usage_unit: Optional[Literal["Requests", "Cost"]] = Field(None, alias="usageUnit")
    used_amount: Optional[float] = Field(None, alias="usedAmount")
    valid_from: Optional[datetime] = Field(None, alias="validFrom")
    valid_until: Optional[datetime] = Field(None, alias="validUntil")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        usage_limit = self.to_dict()
        return str(usage_limit)


class Project(CustomBaseModel):
    """
     {
      "projectActive": "boolean",
      "projectDescription": "string",
      "projectId": "string",
      "projectName": "string",
      "projectStatus": "integer", /* 0:Active, 2:Hidden */
    }
    """
    organization: Optional[Organization] = None
    active: Optional[bool] = Field(None, alias="projectActive")
    description: Optional[str] = Field(None, alias="projectDescription")
    id: Optional[str] = Field(None, alias="projectId")
    name: Optional[str] = Field(None, alias="projectName")
    email: Optional[str] = None
    status: Optional[int] = Field(None, alias="projectStatus")
    tokens: Optional[list[ProjectToken]] = []
    usage_limit: Optional[UsageLimit] = None

    @classmethod
    def model_validate(cls, data: dict):
        organization_data = {
            "organizationId": data.get("organizationId"),
            "organizationName": data.get("organizationName"),
        }
        organization = Organization.model_validate(organization_data) if any(value is not None for value in organization_data.values()) else None
        return cls(organization=organization, **data)

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class RequestItem(CustomBaseModel):
    """
    Represents a request item with metadata about an API interaction.
    Follows a JSON schema with camelCase aliases for external compatibility.
    """
    api_token: str = Field(..., alias="apiToken")
    assistant: str = Field(..., alias="assistant")
    cost: float = Field(..., alias="cost")
    elapsed_time_ms: int = Field(..., alias="elapsedTimeMs")
    end_timestamp: datetime = Field(..., alias="endTimestamp")
    feedback: Optional[str] = Field(None, alias="feedback")
    intent: Optional[str] = Field(None, alias="intent")
    module: str = Field(..., alias="module")
    prompt: Optional[str] = Field(None, alias="prompt")
    output: Optional[str] = Field(None, alias="output")
    input_text: Optional[str] = Field(None, alias="inputText")
    rag_sources_consulted: Optional[str] = Field(None, alias="ragSourcesConsulted")
    session_id: str = Field(..., alias="sessionId")
    start_timestamp: datetime = Field(..., alias="startTimestamp")
    status: str = Field(..., alias="status")
    timestamp: datetime = Field(..., alias="timestamp")

    @model_validator(mode="after")
    def validate_status(self):
        valid_statuses = {"succeeded", "failed", "pending"}
        if self.status not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return self

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())


class GuardrailSettings(CustomBaseModel):
    llm_output: Optional[bool] = Field(False, alias="llmOutputGuardrail")
    input_moderation: Optional[bool] = Field(False, alias="inputModerationGuardrail")
    prompt_injection: Optional[bool] = Field(False, alias="promptInjectionGuardrail")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        settings = self.to_dict()
        return str(settings)


class LlmSettings(CustomBaseModel):
    """
    "llmSettings": {
        "providerName": "string",
        "modelName": "string",
        "temperature": "decimal",
        "maxTokens": "integer",
        "uploadFiles": "boolean",
        "llmOutputGuardrail": "boolean",
        "inputModerationGuardrail": "boolean",
        "promptInjectionGuardrail": "boolean"
      }
    """
    provider_name: Optional[str] = Field(None, alias="providerName")
    model_name: Optional[str] = Field(None, alias="modelName")
    temperature: Optional[float] = Field(None, alias="temperature")
    max_tokens: Optional[int] = Field(None, alias="maxTokens")
    frequency_penalty: Optional[float] = Field(None, alias="frequencyPenalty")
    presence_penalty: Optional[float] = Field(None, alias="presencePenalty")
    upload_files: Optional[bool] = Field(None, alias="uploadFiles")
    guardrail_settings: Optional[GuardrailSettings] = Field(None, alias="guardrail_settings")
    n: Optional[int] = None
    stream: Optional[bool] = Field(None, alias="stream")
    top_p: Optional[float] = Field(None, alias="topP")
    type: Optional[str] = Field(None, alias="type")
    cache: Optional[bool] = Field(None, alias="cache")
    verbose: Optional[bool] = Field(None, alias="verbose")

    class Config:
        protected_namespaces = ()

    @classmethod
    def model_validate(cls, data: dict):
        guardrail_data = {
            "llmOutputGuardrail": data.get("llmOutputGuardrail"),
            "inputModerationGuardrail": data.get("inputModerationGuardrail"),
            "promptInjectionGuardrail": data.get("promptInjectionGuardrail")
        }
        guardrail_settings = GuardrailSettings.model_validate(guardrail_data) \
            if any(value is not None for value in guardrail_data.values()) else None
        return cls(guardrail_settings=guardrail_settings, **data)

    def to_dict(self):
        llm_data = self.model_dump(by_alias=True, exclude_none=True)
        if 'guardrail_settings' in llm_data:
            del llm_data["guardrail_settings"]
        if self.guardrail_settings:
            llm_data.update({
                "llmOutputGuardrail": self.guardrail_settings.llm_output,
                "inputModerationGuardrail": self.guardrail_settings.input_moderation,
                "promptInjectionGuardrail": self.guardrail_settings.prompt_injection
            })
        return {k: v for k, v in llm_data.items() if v is not None}

    def __str__(self):
        llm_setting = self.to_dict()
        return str(llm_setting)


class WelcomeDataFeature(CustomBaseModel):
    """
    {
        "title": "string",
        "description": "string"
    }
    """
    title: str = Field(..., alias="title")
    description: str = Field(..., alias="description")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        feature = self.to_dict()
        return str(feature)


class WelcomeDataExamplePrompt(CustomBaseModel):
    """
    {
        "title": "string",
        "description": "string",
        "promptText": "string"
    }
    """
    title: str = Field(..., alias="title")
    description: str = Field(..., alias="description")
    prompt_text: str = Field(..., alias="promptText")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        example_prompt = self.to_dict()
        return str(example_prompt)


class WelcomeData(CustomBaseModel):
    """
    "title": "string",
    "description": "string",
    "features": [
        ],
        "examplesPrompt": [
        ]
      }
    """
    title: Optional[str] = Field(None, alias="title")
    description: Optional[str] = Field(None, alias="description")
    features: Optional[list[WelcomeDataFeature]] = Field([], alias="features")
    examples_prompt: Optional[list[WelcomeDataExamplePrompt]] = Field([], alias="examplesPrompt")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        welcome_data = self.to_dict()
        return str(welcome_data)


class ChatMessage(CustomBaseModel):
    role: str = Field(..., alias="role")
    content: Union[str, List[Any]] = Field(..., alias="content")
    function_call: Optional[Any] = Field(None, alias="function_call")
    refusal: Optional[Any] = Field(None, alias="refusal")
    tool_calls: Optional[Any] = Field(None, alias="tool_calls")
    annotations: Optional[List[dict]] = Field(None, alias="annotations")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        message = self.to_dict()
        return str(message)


class ChatMessageList(CustomBaseModel):
    messages: List[ChatMessage] = Field(..., alias="messages", description="List of chat messages")

    @field_validator("messages", mode="before")
    @classmethod
    def normalize_messages(cls, value):
        if isinstance(value, list):
            return [ChatMessage.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_list(self):
        return [message.to_dict() for message in self.messages]

    def __getitem__(self, index: int) -> ChatMessage:
        if self.messages is None:
            raise IndexError("ChatMessageList is empty")
        return self.messages[index]

    def __len__(self) -> int:
        return len(self.messages) if self.messages else 0

    def __iter__(self) -> Iterator[ChatMessage]:
        """Make ChatMessageList iterable over its messages."""
        if self.messages is None:
            return iter([])
        return iter(self.messages)

    def append(self, item: ChatMessage) -> None:
        """Append a ChatMessage instance to the messages list."""
        if self.messages is None:
            self.messages = []
        self.messages.append(item)

    def __str__(self):
        return str(self.to_dict())


class ChatVariable(CustomBaseModel):
    key: str = Field(..., alias="key")
    value: str = Field(..., alias="value")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        variable = self.to_dict()
        return str(variable)


class ChatVariableList(CustomBaseModel):
    variables: List[ChatVariable] = Field(..., alias="variables", description="List of chat variables")

    @field_validator("variables", mode="before")
    @classmethod
    def normalize_variables(cls, value):
        if isinstance(value, list):
            return [ChatVariable.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_list(self):
        return [variable.to_dict() for variable in self.variables]

    def __getitem__(self, index: int) -> ChatVariable:
        if self.variables is None:
            raise IndexError("ChatVariableList is empty")
        return self.variables[index]

    def __len__(self) -> int:
        return len(self.variables) if self.variables else 0

    def __iter__(self) -> Iterator[ChatVariable]:
        """Make ChatVariableList iterable over its variables."""
        if self.variables is None:
            return iter([])
        return iter(self.variables)

    def append(self, item: ChatVariable) -> None:
        """Append a ChatVariable instance to the variables list."""
        if self.variables is None:
            self.variables = []
        self.variables.append(item)

    def __str__(self):
        return str(self.to_dict())


class ChatTool(CustomBaseModel):
    name: str = Field(..., alias="name", max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    description: Optional[str] = Field(None, alias="description")
    parameters: Optional[dict] = Field(None, alias="parameters")
    strict: Optional[bool] = Field(None, alias="strict")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        tool = self.to_dict()
        return str(tool)


class ChatToolList(CustomBaseModel):
    tools: List[ChatTool] = Field(..., alias="tools", description="List of chat tools", max_items=128)

    @field_validator("tools", mode="before")
    @classmethod
    def normalize_tools(cls, value):
        if isinstance(value, list):
            return [ChatTool.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    def to_list(self):
        return [tool.to_dict() for tool in self.tools]

    def __getitem__(self, index: int) -> ChatTool:
        if self.tools is None:
            raise IndexError("ChatToolList is empty")
        return self.tools[index]

    def __len__(self) -> int:
        return len(self.tools) if self.tools else 0

    def __iter__(self) -> Iterator[ChatTool]:
        """Make ChatToolList iterable over its tools."""
        if self.tools is None:
            return iter([])
        return iter(self.tools)

    def append(self, item: ChatTool) -> None:
        """Append a ChatTool instance to the tools list."""
        if self.tools is None:
            self.tools = []
        self.tools.append(item)

    def __str__(self):
        return str(self.to_list())


class ToolChoiceFunction(CustomBaseModel):
    type: Optional[Literal["function"]] = Field("function", alias="type")
    name: str = Field(..., alias="name")

    @field_validator("type")
    def validate_type(cls, v):
        if v != "function":
            raise ValueError("Type must be 'function'")
        return v

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        function = self.to_dict()
        return str(function)


class ToolChoiceObject(CustomBaseModel):
    function: ToolChoiceFunction = Field(..., alias="function")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        obj = self.to_dict()
        return str(obj)


class ToolChoice(CustomBaseModel):
    value: Union[str, ToolChoiceObject] = Field(..., alias="tool_choice")

    @field_validator("value")
    def validate_string_value(cls, v):
        if isinstance(v, str) and v not in ["none", "auto", "required"]:
            raise ValueError("String tool_choice must be 'none', 'auto', or 'required'")
        return v

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        choice = self.to_dict()
        return str(choice)


class Assistant(CustomBaseModel):
    id: Optional[str] = Field(None, alias="assistantId")
    name: Optional[str] = Field(None, alias="assistantName")
    description: Optional[str] = Field(None, alias="assistantDescription")
    status: Optional[Literal[1, 2]] = Field(1, alias="assistantStatus")
    priority: Optional[int] = Field(0, alias="assistantPriority")
    type: Optional[str] = Field(None, alias="type")
    prompt: Optional[str] = Field(None, alias="prompt")
    default_revision: Optional[float] = Field(None, alias="assistantIntentDefaultRevision")
    intent_description: Optional[str] = Field(None, alias="assistantIntentDescription")
    intent_id: Optional[str] = Field(None, alias="assistantIntentId")
    intent_name: Optional[str] = Field(None, alias="assistantIntentName")
    revisions: Optional[List["AssistantRevision"]] = Field([], alias="revisions")
    project: Optional["Project"] = Field(None, alias="project")
    welcome_data: Optional["WelcomeData"] = Field(None, alias="welcomeData")
    llm_settings: Optional["LlmSettings"] = Field(None, alias="llmSettings")

    @field_validator("revisions", mode="before")
    @classmethod
    def normalize_revisions(cls, value):
        if isinstance(value, list):
            return [AssistantRevision.model_validate(item) if isinstance(item, dict) else item for item in value]
        return value

    @field_validator("welcome_data", mode="before")
    @classmethod
    def normalize_welcome_data(cls, value):
        if isinstance(value, dict):
            return WelcomeData.model_validate(value)
        return value

    @field_validator("llm_settings", mode="before")
    @classmethod
    def normalize_llm_settings(cls, value):
        if isinstance(value, dict):
            return LlmSettings.model_validate(value)
        return value

    def to_dict(self):
        result = {
            "assistantId": self.id,
            "assistantName": self.name,
            "assistantDescription": self.description,
            "assistantStatus": self.status,
            "assistantPriority": self.priority,
            "type": self.type,
            "prompt": self.prompt,
            "assistantIntentDefaultRevision": self.default_revision,
            "assistantIntentDescription": self.intent_description,
            "assistantIntentId": self.intent_id,
            "assistantIntentName": self.intent_name,
            "revisions": [revision.to_dict() for revision in self.revisions] if self.revisions else None,
            "project": self.project.to_dict() if self.project else None,
            "welcomeData": self.welcome_data.to_dict() if self.welcome_data else None,
            "llmSettings": self.llm_settings.to_dict() if self.llm_settings else None
        }
        return {k: v for k, v in result.items() if v is not None}

    def __str__(self):
        assistant = self.to_dict()
        return str(assistant)


class TextAssistant(Assistant):
    type: Literal["text"] = "text"


class ChatAssistant(Assistant):
    type: Literal["chat"] = "chat"


class DataAnalystAssistant(Assistant):
    pass


class ChatWithDataAssistant(Assistant):
    type: Literal["ChatWithData"] = "ChatWithData"
