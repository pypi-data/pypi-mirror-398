from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput
import uuid

GEAI_LAB_HELP = """\
The Lab
The Globant Enterprise AI Lab is a comprehensive framework designed to create, manage, and orchestrate autonomous AI agents capable of addressing complex tasks with minimal human intervention. It provides a structured environment for defining agents, their associated tools, reasoning strategies, and workflows, all integrated within a cohesive ecosystem. The PyGEAI SDK serves as the primary interface for developers to interact with the Lab, offering a Python-native experience through the lab module, which enables seamless management of the Lab’s resources and operations.

Overview
The Globant Enterprise AI Lab enables the creation of intelligent AI agents, from collaborative co-pilots to fully autonomous systems, capable of executing intricate tasks. Its modular design ensures flexibility, allowing developers to define agent behaviors, orchestrate collaborative workflows, and manage knowledge artifacts. The PyGEAI SDK streamlines these processes by providing an intuitive, Python-centric interface that abstracts the Lab’s underlying APIs, making it accessible to developers familiar with Python conventions.

The Lab’s core modules are:

Agents & Tools Repository: A centralized hub for defining and managing agents and their resources, such as skills, tools, and external API integrations.

Agentic Flows: A system for creating workflows that combine tasks, agents, and knowledge artifacts to achieve broader objectives.

Knowledge Base: A repository for storing and organizing artifacts (e.g., documents, data outputs) that agents consume or produce during workflows.

Agent Runtime: The execution environment where agents perform tasks, interact with artifacts, and respond to events within defined workflows.

Interacting with the Lab via PyGEAI SDK
The PyGEAI SDK’s lab module provides a streamlined interface for developers to engage with the Globant Enterprise AI Lab. Designed to align with Python conventions, it offers a command-line tool that facilitates interaction with the Lab’s resources, including agents, tools, reasoning strategies, processes, tasks, and runtime instances. The lab module supports a range of operations, ensuring developers can efficiently manage the Lab’s ecosystem.

### Managing Agents

The lab module enables developers to define and manage AI agents within the Lab. Agents are entities configured with specific prompts, language models, and operational parameters to perform designated tasks. Through the lab module, developers can create agents with custom attributes, update their configurations, retrieve details, list available agents, publish revisions, share agents via links, or remove them as needed. This functionality allows for precise control over agent lifecycle and behavior within the Lab’s environment.

### Configuring Tools

Tools extend agent capabilities by providing access to external APIs, built-in functions, or custom logic. The lab module supports the creation and management of tools, allowing developers to define tools with specific scopes (e.g., API-based or external), configure their parameters, and control their accessibility. Developers can list tools, retrieve tool details, update configurations, publish revisions, set parameters, or delete tools, ensuring tools are seamlessly integrated into the Lab’s workflows.

### Defining Reasoning Strategies

Reasoning strategies guide how agents process information and make decisions. The lab module allows developers to create and manage these strategies, specifying system prompts and access scopes to tailor agent reasoning. Developers can list available strategies, retrieve details, update configurations, and ensure strategies align with project requirements, enhancing agent performance within the Lab.

### Orchestrating Processes

Processes in the Lab define workflows that combine agents, tasks, and knowledge artifacts to achieve complex objectives. The lab module facilitates process management by enabling developers to create processes, define their structure (including activities, signals, and sequence flows), and update configurations. Developers can list processes, retrieve details, publish revisions, or delete processes, providing full control over workflow orchestration within the Lab.

### Managing Tasks

Tasks are individual units of work within processes, assigned to agents for execution. The lab module supports task creation, allowing developers to specify task prompts, artifact types, and descriptions. Developers can list tasks, retrieve task details, update configurations, publish revisions, or delete tasks, ensuring tasks are effectively integrated into the Lab’s workflows.

### Controlling Runtime Instances

The Lab’s runtime environment executes processes, where agents perform tasks and interact with artifacts. The lab module provides commands to manage runtime instances, enabling developers to start process instances, monitor their progress, retrieve instance details, access execution history, send signals to influence workflow, or abort instances as needed. This ensures dynamic control over the Lab’s operational execution.

### Running Agents with the Runner

The Runner class in the lab module provides a direct interface for executing agent tasks asynchronously within the Lab’s runtime environment. It allows developers to run agents with flexible input formats—strings, ChatMessage, or ChatMessageList—and customizable LLM settings, enabling tailored interactions for testing or production use. The Runner simplifies agent execution by handling message processing and LLM configuration, returning a ProviderResponse object containing the agent’s response and metadata.

SDK Tools and Utilities
The PyGEAI SDK provides robust programmatic interfaces for interacting with the Globant Enterprise AI Lab, enabling developers to manage agents, tools, reasoning strategies, processes, tasks, and runtime instances directly within Python applications. Beyond the command-line interface, the SDK offers a high-level manager and low-level client classes, designed to integrate seamlessly into development workflows with structured, object-oriented access or flexible JSON-based interactions.

High-Level Interface: AILabManager
The AILabManager class serves as the primary high-level interface, offering a Pythonic, object-oriented approach to managing the Lab’s resources. It abstracts the underlying API complexity, mapping responses to structured Python objects such as Agent, Tool, ReasoningStrategy, AgenticProcess, Task, and ProcessInstance. This allows developers to work with strongly typed models, ensuring clarity and reducing errors when creating, updating, retrieving, or deleting Lab entities.

Agent Management: Create, update, retrieve, list, publish, share, or delete agents using methods like create_agent, update_agent, get_agent, and delete_agent. Agents are represented as Agent objects, encapsulating properties like name, prompts, and LLM configurations.

Tool Management: Define and manage tools with methods such as create_tool, update_tool, get_tool, list_tools, publish_tool_revision, and delete_tool. Tools are modeled as Tool objects, supporting API-based or custom configurations with parameters (ToolParameter).

Reasoning Strategies: Configure agent reasoning with create_reasoning_strategy, update_reasoning_strategy, get_reasoning_strategy, and list_reasoning_strategies. Strategies are represented as ReasoningStrategy objects, defining system prompts and access scopes.

Process Orchestration: Manage workflows through create_process, update_process, get_process, list_processes, publish_process_revision, and delete_process. Processes are encapsulated as AgenticProcess objects, detailing activities, signals, and sequence flows.

Task Management: Create and manage tasks with create_task, update_task, get_task, list_tasks, publish_task_revision, and delete_task. Tasks are modeled as Task objects, specifying prompts and artifact types.

Runtime Control: Start, monitor, and control process instances using start_instance, get_instance, list_process_instances, get_instance_history, send_user_signal, and abort_instance. Instances are represented as ProcessInstance objects, with execution details and thread information accessible via get_thread_information.

The AILabManager is initialized with an API key, base URL, and optional alias, providing a unified entry point for all Lab operations. Its methods handle error mapping (ErrorListResponse) and response validation, making it ideal for rapid development and integration into larger applications.

Low-Level Interface: Client Classes
For developers requiring fine-grained control or preferring to work directly with JSON responses, the SDK includes low-level client classes: AgentClient, ToolClient, ReasoningStrategyClient, and AgenticProcessClient. These clients interact with the Lab’s APIs without mapping responses to Python objects, returning raw JSON or text for maximum flexibility.

AgentClient: Supports operations like create_agent, update_agent, get_agent, list_agents, publish_agent_revision, create_sharing_link, and delete_agent. It handles agent-specific API endpoints, passing parameters like project ID, agent name, prompts, and LLM configurations as dictionaries.

ToolClient: Provides methods such as create_tool, update_tool, get_tool, list_tools, publish_tool_revision, get_parameter, set_parameter, and delete_tool. It manages tool configurations, including OpenAPI specifications and parameter lists, with validation for scopes and access levels.

ReasoningStrategyClient: Includes create_reasoning_strategy, update_reasoning_strategy, get_reasoning_strategy, and list_reasoning_strategies, allowing direct manipulation of strategy definitions like system prompts and localized descriptions.

AgenticProcessClient: Offers comprehensive process and task management with methods like create_process, update_process, get_process, list_processes, publish_process_revision, delete_process, create_task, update_task, get_task, list_tasks, publish_task_revision, delete_task, start_instance, get_instance, list_process_instances, get_instance_history, get_thread_information, send_user_signal, and abort_instance. It handles complex process structures and runtime operations in JSON format.

Each client is initialized with an API key and base URL, using a BaseClient for HTTP requests. They provide direct access to the Lab’s endpoints, enabling custom parsing or integration with external systems where object mapping is unnecessary.

Integration and Flexibility
Both the AILabManager and client classes are installable via pip install pygeai and support cross-platform development. The high-level AILabManager is suited for structured applications requiring type safety and ease of use, while the low-level clients cater to scenarios demanding raw API responses or custom workflows. Developers can combine these interfaces within the same project, leveraging AILabManager for rapid prototyping and clients for specialized tasks.

Data Models
The PyGEAI SDK provides Pydantic-based data models for interacting with the Globant Enterprise AI Lab, enabling developers to configure agents, tools, processes, tasks, and more. These models ensure type safety and API compatibility without requiring hardcoded field details that may change. Many models allow direct dictionary inputs for nested configurations, simplifying instantiation. This section describes each model’s purpose, provides examples of instantiation (via attributes and dictionaries), and notes key restrictions, keeping documentation maintainable and flexible.

Note

Models inherit from CustomBaseModel, a Pydantic BaseModel subclass, providing to_dict() for serialization.

FilterSettings
Purpose
Configures filters for querying Lab entities like agents or tools, supporting pagination and scope.

Usage Examples
Via Attributes:

from pygeai.lab.models import FilterSettings

filters = FilterSettings(id="agent-123", name="MyAgent", access_scope="private")
print(filters.to_dict())
# Output: Dictionary with filter settings
Via Dictionary:

from pygeai.lab.models import FilterSettings

filters = FilterSettings(**{
    "id": "agent-123",
    "name": "MyAgent",
    "accessScope": "private"
})
print(filters.to_dict())
# Output: Dictionary with filter settings
Restrictions and Considerations
Most fields are optional for flexible queries.

Pagination requires non-negative integers.

Scope values must match API expectations (e.g., “public”, “private”).

Use dictionaries for quick filter setup in API calls.

Avoid over-specifying to ensure results.

Sampling
Purpose
Controls randomness in LLM token generation.

Usage Examples
Via Attributes:

from pygeai.lab.models import Sampling

sampling = Sampling(temperature=0.8, top_k=40, top_p=0.95)
print(sampling.to_dict())
# Output: {"temperature": 0.8, "topK": 40, "topP": 0.95}
Via Dictionary:

from pygeai.lab.models import Sampling

sampling = Sampling(**{
    "temperature": 0.8,
    "topK": 40,
    "topP": 0.95
})
print(sampling.to_dict())
# Output: {"temperature": 0.8, "topK": 40, "topP": 0.95}
Restrictions and Considerations
All fields are required.

Temperature should range from 0.1 to 2.0.

Top-k and top-p need positive, reasonable values.

Dictionaries simplify sampling configuration.

Test settings to balance creativity and coherence.

LlmConfig
Purpose
Defines LLM settings, including token limits and sampling.

Usage Examples
Via Attributes:

from pygeai.lab.models import LlmConfig, Sampling

sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
print(llm_config.to_dict())
# Output: Dictionary with LLM settings
Via Dictionary (with Sampling as dict):

from pygeai.lab.models import LlmConfig

llm_config = LlmConfig(**{
    "maxTokens": 2048,
    "timeout": 30,
    "sampling": {
        "temperature": 0.7,
        "topK": 50,
        "topP": 0.9
    }
})
print(llm_config.to_dict())
# Output: Dictionary with LLM settings
Restrictions and Considerations
Core fields are mandatory.

Token limits depend on LLM capacity.

Timeout may be API-capped; use 0 carefully.

Accepts sampling as a dictionary for convenience.

Verify settings before scaling.

Model
Purpose
Customizes an LLM for an agent.

Usage Examples
Via Attributes:

from pygeai.lab.models import Model, LlmConfig, Sampling

sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
model = Model(name="gpt-4", llm_config=llm_config)
print(model.to_dict())
# Output: Dictionary with model settings
Via Dictionary (with LlmConfig as dict):

from pygeai.lab.models import Model

model = Model(**{
    "name": "gpt-4",
    "llmConfig": {
        "maxTokens": 2048,
        "timeout": 30,
        "sampling": {
            "temperature": 0.7,
            "topK": 50,
            "topP": 0.9
        }
    }
})
print(model.to_dict())
# Output: Dictionary with model settings
Restrictions and Considerations
Name is required; must be Lab-supported.

Optional LLM config can be a dictionary.

Prompt, if used, should align with agent tasks.

Useful for flexible model assignments.

Check LLM compatibility.

PromptExample
Purpose
Provides input-output pairs for few-shot learning.

Usage Examples
Via Attributes:

from pygeai.lab.models import PromptExample

example = PromptExample(input_data="Summarize: [article]", output='{"summary": "AI news."}')
print(example.to_dict())
# Output: Dictionary with example data
Via Dictionary:

from pygeai.lab.models import PromptExample

example = PromptExample(**{
    "inputData": "Summarize: [article]",
    "output": '{"summary": "AI news."}'
})
print(example.to_dict())
# Output: Dictionary with example data
Restrictions and Considerations
Both fields are required; output must be JSON.

Keep examples concise and relevant.

Multiple examples improve accuracy.

Dictionaries simplify example setup.

Monitor token usage with examples.

PromptOutput
Purpose
Defines expected prompt outputs.

Usage Examples
Via Attributes:

from pygeai.lab.models import PromptOutput

output = PromptOutput(key="summary", description="Text summary.")
print(output.to_dict())
# Output: {"key": "summary", "description": "Text summary."}
Via Dictionary:

from pygeai.lab.models import PromptOutput

output = PromptOutput(**{
    "key": "summary",
    "description": "Text summary."
})
print(output.to_dict())
# Output: {"key": "summary", "description": "Text summary."}
Restrictions and Considerations
Key and description are required.

Keys must be unique per prompt.

Use clear descriptions for output format.

Dictionaries streamline output definitions.

Supports multiple outputs.

Prompt
Purpose
Configures an agent’s prompt behavior.

Usage Examples
Via Attributes:

from pygeai.lab.models import Prompt, PromptOutput, PromptExample

output = PromptOutput(key="summary", description="Text summary.")
example = PromptExample(input_data="Article: [content]", output='{"summary": "AI news."}')
prompt = Prompt(instructions="Summarize article.", inputs=["article"], outputs=[output], examples=[example])
print(prompt.to_dict())
# Output: Dictionary with prompt settings
Via Dictionary (with Outputs, Examples as dicts):

from pygeai.lab.models import Prompt

prompt = Prompt(**{
    "instructions": "Summarize article.",
    "inputs": ["article"],
    "outputs": [{"key": "summary", "description": "Text summary."}],
    "examples": [{"inputData": "Article: [content]", "output": '{"summary": "AI news."}'}]
})
print(prompt.to_dict())
# Output: Dictionary with prompt settings
Restrictions and Considerations
Instructions, inputs, and outputs are required.

Outputs need at least one entry.

Accepts outputs and examples as dictionaries.

Inputs must be unique.

Avoid unimplemented fields like context.

ModelList
Purpose
Holds multiple model configurations.

Usage Examples
Via Attributes:

from pygeai.lab.models import ModelList, Model

model = Model(name="gpt-4")
model_list = ModelList(models=[model])
print(model_list.to_dict())
# Output: List of model dictionaries
Via Dictionary (with Models as dicts):

from pygeai.lab.models import ModelList

model_list = ModelList(**{
    "models": [
        {"name": "gpt-4"},
        {"name": "gpt-3.5"}
    ]
})
print(model_list.to_dict())
# Output: List of model dictionaries
Restrictions and Considerations
Models collection is required; can be empty.

Accepts models as dictionaries.

Supports iteration and appending.

Ensure unique model names.

Simplifies bulk model setup.

AgentData
Purpose
Defines an agent’s core configuration.

Usage Examples
Via Attributes:

from pygeai.lab.models import AgentData, Prompt, PromptOutput, LlmConfig, Sampling, ModelList, Model

prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
model_list = ModelList(models=[Model(name="gpt-4")])
agent_data = AgentData(prompt=prompt, llm_config=llm_config, models=model_list)
print(agent_data.to_dict())
# Output: Dictionary with agent data
Via Dictionary (with Prompt, LlmConfig, Models as dicts):

from pygeai.lab.models import AgentData

agent_data = AgentData(**{
    "prompt": {
        "instructions": "Summarize.",
        "inputs": ["text"],
        "outputs": [{"key": "summary", "description": "Summary."}]
    },
    "llmConfig": {
        "maxTokens": 2048,
        "timeout": 30,
        "sampling": {"temperature": 0.7, "topK": 50, "topP": 0.9}
    },
    "models": [{"name": "gpt-4"}]
})
print(agent_data.to_dict())
# Output: Dictionary with agent data
Restrictions and Considerations
Core components are required.

Accepts prompt, LLM config, and models as dictionaries.

Non-draft agents need at least one model.

Align settings with LLM capabilities.

Simplifies complex agent setups.

Agent
Purpose
Represents a complete agent with metadata.

Usage Examples
Via Attributes:

from pygeai.lab.models import Agent, AgentData, Prompt, PromptOutput, ModelList, Model

prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
model_list = ModelList(models=[Model(name="gpt-4")])
agent_data = AgentData(prompt=prompt, llm_config=LlmConfig(max_tokens=2048, timeout=30, sampling=Sampling(temperature=0.7, top_k=50, top_p=0.9)), models=model_list)
agent = Agent(name="SummaryAgent", access_scope="public", public_name="summary-agent", agent_data=agent_data)
print(agent.to_dict())
# Output: Dictionary with agent settings
Via Dictionary (with AgentData as dict):

from pygeai.lab.models import Agent

agent = Agent(**{
    "name": "SummaryAgent",
    "accessScope": "public",
    "publicName": "summary-agent",
    "agentData": {
        "prompt": {
            "instructions": "Summarize.",
            "inputs": ["text"],
            "outputs": [{"key": "summary", "description": "Summary."}]
        },
        "llmConfig": {
            "maxTokens": 2048,
            "timeout": 30,
            "sampling": {"temperature": 0.7, "topK": 50, "topP": 0.9}
        },
        "models": [{"name": "gpt-4"}]
    }
})
print(agent.to_dict())
# Output: Dictionary with agent settings
Restrictions and Considerations
Name is required; avoid special characters.

Accepts agent_data as a dictionary.

Public agents need valid public names.

Non-draft agents require full configuration.

API sets identifiers automatically.

AgentList
Purpose
Manages multiple agents, typically from API responses.

Usage Examples
Via Attributes:

from pygeai.lab.models import AgentList, Agent

agent = Agent(name="Agent1", access_scope="private")
agent_list = AgentList(agents=[agent])
print(agent_list.to_dict())
# Output: List of agent dictionaries
Via Dictionary (with Agents as dicts):

from pygeai.lab.models import AgentList

agent_list = AgentList(**{
    "agents": [
        {"name": "Agent1", "accessScope": "private"},
        {"name": "Agent2", "accessScope": "public", "publicName": "agent-two"}
    ]
})
print(agent_list.to_dict())
# Output: List of agent dictionaries
Restrictions and Considerations
Agents collection is required; can be empty.

Accepts agents as dictionaries.

Supports iteration and appending.

Useful for bulk agent management.

SharingLink
Purpose
Enables agent sharing via links.

Usage Examples
Via Attributes:

from pygeai.lab.models import SharingLink

link = SharingLink(agent_id="agent-123", api_token="xyz-token", shared_link="https://lab.globant.ai/share/agent-123")
print(link.to_dict())
# Output: Dictionary with link details
Via Dictionary:

from pygeai.lab.models import SharingLink

link = SharingLink(**{
    "agentId": "agent-123",
    "apiToken": "xyz-token",
    "sharedLink": "https://lab.globant.ai/share/agent-123"
})
print(link.to_dict())
# Output: Dictionary with link details
Restrictions and Considerations
All fields are required, set by API.

Links must be valid URLs.

Secure tokens to prevent leaks.

Dictionaries simplify link creation.

ToolParameter
Purpose
Defines tool parameters.

Usage Examples
Via Attributes:

from pygeai.lab.models import ToolParameter

param = ToolParameter(key="api_key", data_type="String", description="API key.", is_required=True)
print(param.to_dict())
# Output: Dictionary with parameter details
Via Dictionary:

from pygeai.lab.models import ToolParameter

param = ToolParameter(**{
    "key": "api_key",
    "dataType": "String",
    "description": "API key.",
    "isRequired": True
})
print(param.to_dict())
# Output: Dictionary with parameter details
Restrictions and Considerations
Core fields are mandatory.

Data types must match API expectations.

Keys must be unique per tool.

Dictionaries streamline parameter setup.

ToolMessage
Purpose
Provides tool feedback messages.

Usage Examples
Via Attributes:

from pygeai.lab.models import ToolMessage

message = ToolMessage(description="Invalid key.", type="error")
print(message.to_dict())
# Output: {"description": "Invalid key.", "type": "error"}
Via Dictionary:

from pygeai.lab.models import ToolMessage

message = ToolMessage(**{
    "description": "Invalid key.",
    "type": "error"
})
print(message.to_dict())
# Output: {"description": "Invalid key.", "type": "error"}
Restrictions and Considerations
Both fields are required.

Types are typically “warning” or “error.”

Keep messages concise.

Dictionaries simplify message creation.

Tool
Purpose
Configures tools for agents.

Usage Examples
Via Attributes:

from pygeai.lab.models import Tool, ToolParameter

param = ToolParameter(key="api_key", data_type="String", description="API key.", is_required=True)
tool = Tool(name="WeatherTool", description="Fetches weather.", scope="api", parameters=[param])
print(tool.to_dict())
# Output: Dictionary with tool settings
Via Dictionary (with Parameters as dicts):

from pygeai.lab.models import Tool

tool = Tool(**{
    "name": "WeatherTool",
    "description": "Fetches weather.",
    "scope": "api",
    "parameters": [
        {"key": "api_key", "dataType": "String", "description": "API key.", "isRequired": True}
    ]
})
print(tool.to_dict())
# Output: Dictionary with tool settings
Restrictions and Considerations
Name and description are required.

Accepts parameters as dictionaries.

API tools need valid OpenAPI specs.

Public tools require valid public names.

Ensure unique parameter keys.

ToolList
Purpose
Manages multiple tools.

Usage Examples
Via Attributes:

from pygeai.lab.models import ToolList, Tool

tool = Tool(name="Tool1", description="Tool one.", scope="builtin")
tool_list = ToolList(tools=[tool])
print(tool_list.to_dict())
# Output: Dictionary with tool list
Via Dictionary (with Tools as dicts):

from pygeai.lab.models import ToolList

tool_list = ToolList(**{
    "tools": [
        {"name": "Tool1", "description": "Tool one.", "scope": "builtin"}
    ]
})
print(tool_list.to_dict())
# Output: Dictionary with tool list
Restrictions and Considerations
Tools collection is required; can be empty.

Accepts tools as dictionaries.

Supports iteration and appending.

Simplifies bulk tool handling.

LocalizedDescription
Purpose
Provides multilingual strategy descriptions.

Usage Examples
Via Attributes:

from pygeai.lab.models import LocalizedDescription

desc = LocalizedDescription(language="english", description="Creative strategy.")
print(desc.to_dict())
# Output: {"language": "english", "description": "Creative strategy."}
Via Dictionary:

from pygeai.lab.models import LocalizedDescription

desc = LocalizedDescription(**{
    "language": "english",
    "description": "Creative strategy."
})
print(desc.to_dict())
# Output: {"language": "english", "description": "Creative strategy."}
Restrictions and Considerations
Both fields are required.

Use standard language names.

Dictionaries simplify descriptions.

Supports multiple languages.

ReasoningStrategy
Purpose
Guides agent reasoning behavior.

Usage Examples
Via Attributes:

from pygeai.lab.models import ReasoningStrategy, LocalizedDescription

desc = LocalizedDescription(language="english", description="Creative strategy.")
strategy = ReasoningStrategy(name="CreativeStrategy", access_scope="public", type="addendum", localized_descriptions=[desc])
print(strategy.to_dict())
# Output: Dictionary with strategy settings
Via Dictionary (with Descriptions as dicts):

from pygeai.lab.models import ReasoningStrategy

strategy = ReasoningStrategy(**{
    "name": "CreativeStrategy",
    "accessScope": "public",
    "type": "addendum",
    "localizedDescriptions": [
        {"language": "english", "description": "Creative strategy."}
    ]
})
print(strategy.to_dict())
# Output: Dictionary with strategy settings
Restrictions and Considerations
Name, scope, and type are required.

Accepts descriptions as dictionaries.

Scope and type depend on Lab values.

API sets identifiers.

ReasoningStrategyList
Purpose
Manages multiple reasoning strategies.

Usage Examples
Via Attributes:

from pygeai.lab.models import ReasoningStrategyList, ReasoningStrategy

strategy = ReasoningStrategy(name="Strategy1", access_scope="private", type="addendum")
strategy_list = ReasoningStrategyList(strategies=[strategy])
print(strategy_list.to_dict())
# Output: List of strategy dictionaries
Via Dictionary (with Strategies as dicts):

from pygeai.lab.models import ReasoningStrategyList

strategy_list = ReasoningStrategyList(**{
    "strategies": [
        {"name": "Strategy1", "accessScope": "private", "type": "addendum"}
    ]
})
print(strategy_list.to_dict())
# Output: List of strategy dictionaries
Restrictions and Considerations
Strategies collection is required; can be empty.

Accepts strategies as dictionaries.

Supports iteration and appending.

KnowledgeBase
Purpose
Manages process artifacts.

Usage Examples
Via Attributes:

from pygeai.lab.models import KnowledgeBase

kb = KnowledgeBase(name="DocsKB", artifact_type_name=["document"])
print(kb.to_dict())
# Output: Dictionary with knowledge base settings
Via Dictionary:

from pygeai.lab.models import KnowledgeBase

kb = KnowledgeBase(**{
    "name": "DocsKB",
    "artifactTypeName": ["document"]
})
print(kb.to_dict())
# Output: Dictionary with knowledge base settings
Restrictions and Considerations
Name and artifact types are required.

Dictionaries simplify setup.

API sets identifiers.

Ensure valid artifact types.

AgenticActivity
Purpose
Links tasks and agents in processes.

Usage Examples
Via Attributes:

from pygeai.lab.models import AgenticActivity

activity = AgenticActivity(key="act1", name="Summarize", task_name="SummaryTask", agent_name="SummaryAgent", agent_revision_id=1)
print(activity.to_dict())
# Output: Dictionary with activity settings
Via Dictionary:

from pygeai.lab.models import AgenticActivity

activity = AgenticActivity(**{
    "key": "act1",
    "name": "Summarize",
    "taskName": "SummaryTask",
    "agentName": "SummaryAgent",
    "agentRevisionId": 1
})
print(activity.to_dict())
# Output: Dictionary with activity settings
Restrictions and Considerations
Core fields are required.

Keys must be unique.

Dictionaries streamline activity setup.

Reference existing tasks and agents.

ArtifactSignal
Purpose
Triggers process actions via artifacts.

Usage Examples
Via Attributes:

from pygeai.lab.models import ArtifactSignal

signal = ArtifactSignal(key="sig1", name="DocSignal", handling_type="C", artifact_type_name=["document"])
print(signal.to_dict())
# Output: Dictionary with signal settings
Via Dictionary:

from pygeai.lab.models import ArtifactSignal

signal = ArtifactSignal(**{
    "key": "sig1",
    "name": "DocSignal",
    "handlingType": "C",
    "artifactTypeName": ["document"]
})
print(signal.to_dict())
# Output: Dictionary with signal settings
Restrictions and Considerations
All fields are required.

Keys must be unique.

Dictionaries simplify signal setup.

Handling types depend on Lab engine.

UserSignal
Purpose
Enables user-driven process signals.

Usage Examples
Via Attributes:

from pygeai.lab.models import UserSignal

signal = UserSignal(key="user1", name="UserInput")
print(signal.to_dict())
# Output: {"key": "user1", "name": "UserInput"}
Via Dictionary:

from pygeai.lab.models import UserSignal

signal = UserSignal(**{
    "key": "user1",
    "name": "UserInput"
})
print(signal.to_dict())
# Output: {"key": "user1", "name": "UserInput"}
Restrictions and Considerations
Both fields are required.

Keys must be unique.

Dictionaries simplify setup.

Use descriptive names.

Event
Purpose
Marks process start or end points.

Usage Examples
Via Attributes:

from pygeai.lab.models import Event

event = Event(key="start1", name="ProcessStart")
print(event.to_dict())
# Output: {"key": "start1", "name": "ProcessStart"}
Via Dictionary:

from pygeai.lab.models import Event

event = Event(**{
    "key": "start1",
    "name": "ProcessStart"
})
print(event.to_dict())
# Output: {"key": "start1", "name": "ProcessStart"}
Restrictions and Considerations
Both fields are required.

Keys must be unique.

Dictionaries simplify event setup.

Ensure flow connectivity.

SequenceFlow
Purpose
Connects process elements.

Usage Examples
Via Attributes:

from pygeai.lab.models import SequenceFlow

flow = SequenceFlow(key="flow1", source_key="start1", target_key="act1")
print(flow.to_dict())
# Output: Dictionary with flow settings
Via Dictionary:

from pygeai.lab.models import SequenceFlow

flow = SequenceFlow(**{
    "key": "flow1",
    "sourceKey": "start1",
    "targetKey": "act1"
})
print(flow.to_dict())
# Output: Dictionary with flow settings
Restrictions and Considerations
All fields are required.

Keys must be unique.

Dictionaries simplify flow setup.

Reference valid elements.

Variable
Purpose
Stores dynamic process data.

Usage Examples
Via Attributes:

from pygeai.lab.models import Variable

var = Variable(key="input_text", value="Sample text")
print(var.to_dict())
# Output: {"key": "input_text", "value": "Sample text"}
Via Dictionary:

from pygeai.lab.models import Variable

var = Variable(**{
    "key": "input_text",
    "value": "Sample text"
})
print(var.to_dict())
# Output: {"key": "input_text", "value": "Sample text"}
Restrictions and Considerations
Both fields are required.

Keys should be unique.

Dictionaries simplify variable setup.

Values must be strings.

VariableList
Purpose
Manages process variables.

Usage Examples
Via Attributes:

from pygeai.lab.models import VariableList, Variable

var = Variable(key="input_text", value="Sample text")
var_list = VariableList(variables=[var])
print(var_list.to_dict())
# Output: List of variable dictionaries
Via Dictionary (with Variables as dicts):

from pygeai.lab.models import VariableList

var_list = VariableList(**{
    "variables": [
        {"key": "input_text", "value": "Sample text"}
    ]
})
print(var_list.to_dict())
# Output: List of variable dictionaries
Restrictions and Considerations
Variables collection is optional; defaults to empty.

Accepts variables as dictionaries.

Supports iteration and appending.

AgenticProcess
Purpose
Orchestrates process workflows.

Usage Examples
Via Attributes:

from pygeai.lab.models import AgenticProcess, AgenticActivity, Event, SequenceFlow

activity = AgenticActivity(key="act1", name="Summarize", task_name="SummaryTask", agent_name="SummaryAgent", agent_revision_id=1)
start_event = Event(key="start1", name="Start")
flow = SequenceFlow(key="flow1", source_key="start1", target_key="act1")
process = AgenticProcess(name="SummaryProcess", agentic_activities=[activity], start_event=start_event, sequence_flows=[flow])
print(process.to_dict())
# Output: Dictionary with process settings
Via Dictionary (with Activities, Event, Flows as dicts):

from pygeai.lab.models import AgenticProcess

process = AgenticProcess(**{
    "name": "SummaryProcess",
    "agenticActivities": [
        {
            "key": "act1",
            "name": "Summarize",
            "taskName": "SummaryTask",
            "agentName": "SummaryAgent",
            "agentRevisionId": 1
        }
    ],
    "startEvent": {"key": "start1", "name": "Start"},
    "sequenceFlows": [
        {"key": "flow1", "sourceKey": "start1", "targetKey": "act1"}
    ]
})
print(process.to_dict())
# Output: Dictionary with process settings
Restrictions and Considerations
Name is required; avoid special characters.

Accepts activities, events, and flows as dictionaries.

Flows must reference valid keys.

API sets identifiers.

Ensure valid process structure.

ArtifactType
Purpose
Defines task artifacts.

Usage Examples
Via Attributes:

from pygeai.lab.models import ArtifactType

artifact = ArtifactType(name="document", usage_type="input")
print(artifact.to_dict())
# Output: Dictionary with artifact settings
Via Dictionary:

from pygeai.lab.models import ArtifactType

artifact = ArtifactType(**{
    "name": "document",
    "usageType": "input"
})
print(artifact.to_dict())
# Output: Dictionary with artifact settings
Restrictions and Considerations
Name and usage type are required.

Usage type is “input” or “output.”

Dictionaries simplify artifact setup.

Variable keys have length limits.

ArtifactTypeList
Purpose
Manages task artifact types.

Usage Examples
Via Attributes:

from pygeai.lab.models import ArtifactTypeList, ArtifactType

artifact = ArtifactType(name="document", usage_type="input")
artifact_list = ArtifactTypeList(artifact_types=[artifact])
print(artifact_list.to_dict())
# Output: List of artifact dictionaries
Via Dictionary (with ArtifactTypes as dicts):

from pygeai.lab.models import ArtifactTypeList

artifact_list = ArtifactTypeList(**{
    "artifact_types": [
        {"name": "document", "usageType": "input"}
    ]
})
print(artifact_list.to_dict())
# Output: List of artifact dictionaries
Restrictions and Considerations
Artifact types collection is optional; defaults to empty.

Accepts artifact types as dictionaries.

Supports iteration and appending.

Task
Purpose
Configures agent tasks.

Usage Examples
Via Attributes:

from pygeai.lab.models import Task, Prompt, PromptOutput, ArtifactTypeList, ArtifactType

prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
artifact = ArtifactType(name="document", usage_type="input")
task = Task(name="SummaryTask", prompt_data=prompt, artifact_types=ArtifactTypeList(artifact_types=[artifact]))
print(task.to_dict())
# Output: Dictionary with task settings
Via Dictionary (with Prompt, ArtifactTypes as dicts):

from pygeai.lab.models import Task

task = Task(**{
    "name": "SummaryTask",
    "promptData": {
        "instructions": "Summarize.",
        "inputs": ["text"],
        "outputs": [{"key": "summary", "description": "Summary."}]
    },
    "artifactTypes": [
        {"name": "document", "usageType": "input"}
    ]
})
print(task.to_dict())
# Output: Dictionary with task settings
Restrictions and Considerations
Name is required; avoid special characters.

Accepts prompt and artifact types as dictionaries.

Artifact types must use valid usage types.

Prompt is optional but recommended.

AgenticProcessList
Purpose
Manages multiple processes.

Usage Examples
Via Attributes:

from pygeai.lab.models import AgenticProcessList, AgenticProcess

process = AgenticProcess(name="Process1")
process_list = AgenticProcessList(processes=[process])
print(process_list.to_dict())
# Output: Dictionary with process list
Via Dictionary (with Processes as dicts):

from pygeai.lab.models import AgenticProcessList

process_list = AgenticProcessList(**{
    "processes": [
        {"name": "Process1"}
    ]
})
print(process_list.to_dict())
# Output: Dictionary with process list
Restrictions and Considerations
Processes collection is required; can be empty.

Accepts processes as dictionaries.

Supports iteration and appending.

TaskList
Purpose
Manages multiple tasks.

Usage Examples
Via Attributes:

from pygeai.lab.models import TaskList, Task

task = Task(name="Task1")
task_list = TaskList(tasks=[task])
print(task_list.to_dict())
# Output: List of task dictionaries
Via Dictionary (with Tasks as dicts):

from pygeai.lab.models import TaskList

task_list = TaskList(**{
    "tasks": [
        {"name": "Task1"}
    ]
})
print(task_list.to_dict())
# Output: List of task dictionaries
Restrictions and Considerations
Tasks collection is required; can be empty.

Accepts tasks as dictionaries.

Supports iteration and appending.

ProcessInstance
Purpose
Tracks running process instances.

Usage Examples
Via Attributes:

from pygeai.lab.models import ProcessInstance, AgenticProcess

process = AgenticProcess(name="SummaryProcess")
instance = ProcessInstance(process=process, subject="Summary")
print(instance.to_dict())
# Output: Dictionary with instance settings
Via Dictionary (with Process as dict):

from pygeai.lab.models import ProcessInstance

instance = ProcessInstance(**{
    "process": {"name": "SummaryProcess"},
    "subject": "Summary"
})
print(instance.to_dict())
# Output: Dictionary with instance settings
Restrictions and Considerations
Process and subject are required.

Accepts process as a dictionary.

API sets identifiers.

Align variables with process needs.

ProcessInstanceList
Purpose
Manages multiple process instances.

Usage Examples
Via Attributes:

from pygeai.lab.models import ProcessInstanceList, ProcessInstance, AgenticProcess

process = AgenticProcess(name="Process1")
instance = ProcessInstance(process=process, subject="Instance1")
instance_list = ProcessInstanceList(instances=[instance])
print(instance_list.to_dict())
# Output: List of instance dictionaries
Via Dictionary (with Instances as dicts):

from pygeai.lab.models import ProcessInstanceList

instance_list = ProcessInstanceList(**{
    "instances": [
        {"process": {"name": "Process1"}, "subject": "Instance1"}
    ]
})
print(instance_list.to_dict())
# Output: List of instance dictionaries
Restrictions and Considerations
Instances collection is required; can be empty.

Accepts instances as dictionaries.

Supports iteration and appending.

The Lab - Usage
The Globant Enterprise AI Lab enables developers to create and manage AI agents, tools, tasks, and processes. The AILabManager class provides a high-level interface for these operations, while low-level clients (AgentClient, ToolClient, AgenticProcessClient) offer direct API access, and the geai ai-lab CLI provides command-line control. This section documents all Lab operations, grouped by resource type (Agents, Tools, Tasks, Processes), with examples for command-line, low-level, and high-level usage.

Agents
Create Agent
Creates a new AI agent in a specified project, defining its name, access scope, prompt instructions, LLM settings, and other configurations.

Command Line
geai ai-lab create-agent \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --name "Public Translator V2" \
  --access-scope "public" \
  --public-name "com.genexus.geai.public_translator" \
  --job-description "Translates" \
  --avatar-image "https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png" \
  --description "Agent that translates from any language to english." \
  --agent-data-prompt-instructions "the user will provide a text, you must return the same text translated to english" \
  --agent-data-prompt-input "text" \
  --agent-data-prompt-input "avoid slang indicator" \
  --agent-data-prompt-output '{"key": "translated_text", "description": "translated text, with slang or not depending on the indication. in plain text."}' \
  --agent-data-prompt-output '{"key": "summary", "description": "a summary in the original language of the text to be translated, also in plain text."}' \
  --agent-data-prompt-example '{"inputData": "opitiiiis mundo [no-slang]", "output": "{\"translated_text\":\"hello world\",\"Summary\":\"saludo\"}"}' \
  --agent-data-llm-max-tokens 5000 \
  --agent-data-llm-timeout 0 \
  --agent-data-llm-temperature 0.5 \
  --agent-data-model-name "gpt-4-turbo-preview" \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.agents.clients import AgentClient

client = AgentClient()
response = client.create_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    name="Public Translator V2",
    access_scope="public",
    public_name="com.genexus.geai.public_translator",
    job_description="Translates",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png",
    description="Agent that translates from any language to english.",
    agent_data_prompt={
        "instructions": "the user will provide a text, you must return the same text translated to english",
        "inputs": ["text", "avoid slang indicator"],
        "outputs": [
            {"key": "translated_text", "description": "translated text, with slang or not depending on the indication. in plain text."},
            {"key": "summary", "description": "a summary in the original language of the text to be translated, also in plain text."}
        ],
        "examples": [
            {"inputData": "opitiiiis mundo [no-slang]", "output": "{\"translated_text\":\"hello world\",\"Summary\":\"saludo\"}"}
        ]
    },
    agent_data_llm_config={
        "maxTokens": 5000,
        "timeout": 0,
        "temperature": 0.5
    },
    agent_data_models=[{"name": "gpt-4-turbo-preview"}],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, PromptOutput, PromptExample, LlmConfig, ModelList, Model

manager = AILabManager()

prompt = Prompt(
    instructions="the user will provide a text, you must return the same text translated to english",
    inputs=["text", "avoid slang indicator"],
    outputs=[
        PromptOutput(key="translated_text", description="translated text, with slang or not depending on the indication. in plain text."),
        PromptOutput(key="summary", description="a summary in the original language of the text to be translated, also in plain text.")
    ],
    examples=[
        PromptExample(input_data="opitiiiis mundo [no-slang]", output="{\"translated_text\":\"hello world\",\"Summary\":\"saludo\"}")
    ]
)
llm_config = LlmConfig(max_tokens=5000, timeout=0, temperature=0.5)
models = ModelList(models=[Model(name="gpt-4-turbo-preview")])
agent_data = AgentData(prompt=prompt, llm_config=llm_config, models=models)

agent = Agent(
    name="Public Translator V2",
    access_scope="public",
    public_name="com.genexus.geai.public_translator",
    job_description="Translates",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png",
    description="Agent that translates from any language to english.",
    agent_data=agent_data
)

created_agent = manager.create_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent=agent,
    automatic_publish=False
)
print(created_agent)
Update Agent
Updates an existing agent’s configuration, such as its name, prompt instructions, or LLM settings.

Command Line
geai ai-lab update-agent \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --agent-id "agent-123" \
  --name "Public Translator V3" \
  --description "Updated agent for translations." \
  --agent-data-prompt-instructions "the user provides text, translate it to English accurately" \
  --agent-data-llm-temperature 0.7 \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.agents.clients import AgentClient

client = AgentClient()
response = client.update_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123",
    name="Public Translator V3",
    description="Updated agent for translations.",
    agent_data_prompt={
        "instructions": "the user provides text, translate it to English accurately"
    },
    agent_data_llm_config={
        "temperature": 0.7
    },
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig

manager = AILabManager()

agent = Agent(
    name="Public Translator V3",
    description="Updated agent for translations.",
    agent_data=AgentData(
        prompt=Prompt(instructions="the user provides text, translate it to English accurately"),
        llm_config=LlmConfig(temperature=0.7)
    )
)

updated_agent = manager.update_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123",
    agent=agent,
    automatic_publish=False
)
print(updated_agent)
List Agents
Retrieves a list of agents in a specified project, with optional filters for status, pagination, scope, and draft inclusion.

Command Line
geai ai-lab list-agents \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --status "active" \
  --allow-drafts 0 \
  --allow-external 1
Low-Level Service Layer
from pygeai.lab.agents.clients import AgentClient

client = AgentClient()
response = client.list_agents(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    status="active",
    allow_drafts=False,
    allow_external=True
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings

manager = AILabManager()

filters = FilterSettings(
    status="active",
    allow_drafts=False,
    allow_external=True
)
agent_list = manager.get_agent_list(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    filter_settings=filters
)
print(agent_list)
Delete Agent
Deletes an agent from a specified project by its ID.

Command Line
geai ai-lab delete-agent \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --agent-id "agent-123"
Low-Level Service Layer
from pygeai.lab.agents.clients import AgentClient

client = AgentClient()
response = client.delete_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.delete_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123"
)
print(response)
Publish Agent Revision
Publishes a revision of an agent, making it available for use.

Command Line
geai ai-lab publish-agent-revision \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --agent-id "agent-123"
Low-Level Service Layer
from pygeai.lab.agents.clients import AgentClient

client = AgentClient()
response = client.publish_agent_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.publish_agent_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent_id="agent-123"
)
print(response)
Tools
Create Tool
Creates a new tool in a specified project, defining its name, description, scope, and parameters for agent use.

Command Line
geai ai-lab create-tool \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --name "sample tool V3" \
  --description "a builtin tool that does something but really does nothing cos it does not exist." \
  --scope "builtin" \
  --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": true}' \
  --parameter '{"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.", "isRequired": true, "type": "config", "fromSecret": false, "value": "b001e30b4016001f5f76b9ae9215ac40"}' \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.tools.clients import ToolClient

client = ToolClient()
response = client.create_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    name="sample tool V3",
    description="a builtin tool that does something but really does nothing cos it does not exist.",
    scope="builtin",
    parameters=[
        {"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": True},
        {"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.", "isRequired": True, "type": "config", "fromSecret": False, "value": "b001e30b4016001f5f76b9ae9215ac40"}
    ],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, ToolParameter

manager = AILabManager()

tool = Tool(
    name="sample tool V3",
    description="a builtin tool that does something but really does nothing cos it does not exist.",
    scope="builtin",
    parameters=[
        ToolParameter(
            key="input",
            data_type="String",
            description="some input that the tool needs.",
            is_required=True
        ),
        ToolParameter(
            key="some_nonsensitive_id",
            data_type="String",
            description="Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.",
            is_required=True,
            type="config",
            from_secret=False,
            value="b001e30b4016001f5f76b9ae9215ac40"
        )
    ]
)

created_tool = manager.create_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool=tool,
    automatic_publish=False
)
print(created_tool)
Update Tool
Updates an existing tool’s configuration, such as its name, description, or parameters.

Command Line
geai ai-lab update-tool \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --tool-id "tool-456" \
  --name "sample tool V4" \
  --description "Updated builtin tool." \
  --scope "builtin" \
  --parameter '{"key": "input", "dataType": "String", "description": "updated input.", "isRequired": true}' \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.tools.clients import ToolClient

client = ToolClient()
response = client.update_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456",
    name="sample tool V4",
    description="Updated builtin tool.",
    scope="builtin",
    parameters=[
        {"key": "input", "dataType": "String", "description": "updated input.", "isRequired": True}
    ],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, ToolParameter

manager = AILabManager()

tool = Tool(
    name="sample tool V4",
    description="Updated builtin tool.",
    scope="builtin",
    parameters=[
        ToolParameter(
            key="input",
            data_type="String",
            description="updated input.",
            is_required=True
        )
    ]
)

updated_tool = manager.update_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456",
    tool=tool,
    automatic_publish=False
)
print(updated_tool)
Delete Tool
Deletes a tool from a specified project by its ID.

Command Line
geai ai-lab delete-tool \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --tool-id "tool-456"
Low-Level Service Layer
from pygeai.lab.tools.clients import ToolClient

client = ToolClient()
response = client.delete_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.delete_tool(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456"
)
print(response)
Publish Tool Revision
Publishes a revision of a tool, making it available for use.

Command Line
geai ai-lab publish-tool-revision \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --tool-id "tool-456"
Low-Level Service Layer
from pygeai.lab.tools.clients import ToolClient

client = ToolClient()
response = client.publish_tool_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.publish_tool_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    tool_id="tool-456"
)
print(response)
Tasks
Create Task
Creates a new task in a specified project, defining its name, description, prompt configuration, and artifact types.

Command Line
geai ai-lab create-task \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --name "Sample v2" \
  --description "A simple task that requires no tools and define no prompt" \
  --title-template "Sample Task" \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.create_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    name="Sample v2",
    description="A simple task that requires no tools and define no prompt",
    title_template="Sample Task",
    prompt_data={},
    artifact_types=[],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Task, Prompt, ArtifactTypeList

manager = AILabManager()

task = Task(
    name="Sample v2",
    description="A simple task that requires no tools and define no prompt",
    title_template="Sample Task",
    prompt_data=Prompt(),
    artifact_types=ArtifactTypeList(artifact_types=[])
)

created_task = manager.create_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task=task,
    automatic_publish=False
)
print(created_task)
Update Task
Updates an existing task’s configuration, such as its name, description, or prompt settings.

Command Line
geai ai-lab update-task \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --task-id "task-789" \
  --name "Sample v3" \
  --description "Updated simple task." \
  --title-template "Updated Sample Task" \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.update_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789",
    name="Sample v3",
    description="Updated simple task.",
    title_template="Updated Sample Task",
    prompt_data={},
    artifact_types=[],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Task, Prompt, ArtifactTypeList

manager = AILabManager()

task = Task(
    name="Sample v3",
    description="Updated simple task.",
    title_template="Updated Sample Task",
    prompt_data=Prompt(),
    artifact_types=ArtifactTypeList(artifact_types=[])
)

updated_task = manager.update_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789",
    task=task,
    automatic_publish=False
)
print(updated_task)
Delete Task
Deletes a task from a specified project by its ID.

Command Line
geai ai-lab delete-task \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --task-id "task-789"
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.delete_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.delete_task(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789"
)
print(response)
Publish Task Revision
Publishes a revision of a task, making it available for use.

Command Line
geai ai-lab publish-task-revision \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --task-id "task-789"
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.publish_task_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.publish_task_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    task_id="task-789"
)
print(response)
Processes
Create Process
Creates a new agentic process in a specified project, defining its workflow with activities, signals, events, and sequence flows.

Command Line
geai ai-lab create-process \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --key "product_def" \
  --name "Basic Process V4" \
  --description "This is a sample process" \
  --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
  --agentic-activity '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' \
  --artifact-signal '{"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}' \
  --user-signal '{"key": "signal_done", "name": "process-completed"}' \
  --start-event '{"key": "artifact.upload.1", "name": "artifact.upload"}' \
  --end-event '{"key": "end", "name": "Done"}' \
  --sequence-flow '{"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"}' \
  --sequence-flow '{"key": "step2", "sourceKey": "activityOne", "targetKey": "signal_done"}' \
  --sequence-flow '{"key": "stepEnd", "sourceKey": "signal_done", "targetKey": "end"}' \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.create_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    key="product_def",
    name="Basic Process V4",
    description="This is a sample process",
    kb={"name": "basic-sample", "artifactTypeName": ["sample-artifact"]},
    agentic_activities=[
        {"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}
    ],
    artifact_signals=[
        {"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}
    ],
    user_signals=[
        {"key": "signal_done", "name": "process-completed"}
    ],
    start_event={"key": "artifact.upload.1", "name": "artifact.upload"},
    end_event={"key": "end", "name": "Done"},
    sequence_flows=[
        {"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"},
        {"key": "step2", "sourceKey": "activityOne", "targetKey": "signal_done"},
        {"key": "stepEnd", "sourceKey": "signal_done", "targetKey": "end"}
    ],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow

manager = AILabManager()

process = AgenticProcess(
    key="product_def",
    name="Basic Process V4",
    description="This is a sample process",
    kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"]),
    agentic_activities=[
        AgenticActivity(
            key="activityOne",
            name="First Step",
            task_name="basic-task",
            agent_name="sample-translator",
            agent_revision_id=0
        )
    ],
    artifact_signals=[
        ArtifactSignal(
            key="artifact.upload.1",
            name="artifact.upload",
            handling_type="C",
            artifact_type_name=["sample-artifact"]
        )
    ],
    user_signals=[
        UserSignal(key="signal_done", name="process-completed")
    ],
    start_event=Event(key="artifact.upload.1", name="artifact.upload"),
    end_event=Event(key="end", name="Done"),
    sequence_flows=[
        SequenceFlow(key="step1", source_key="artifact.upload.1", target_key="activityOne"),
        SequenceFlow(key="step2", source_key="activityOne", target_key="signal_done"),
        SequenceFlow(key="stepEnd", source_key="signal_done", target_key="end")
    ]
)

created_process = manager.create_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process=process,
    automatic_publish=False
)
print(created_process)
Update Process
Updates an existing process’s configuration, such as its name, description, or workflow components.

Command Line
geai ai-lab update-process \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --process-id "process-101" \
  --key "product_def" \
  --name "Basic Process V5" \
  --description "Updated sample process" \
  --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
  --automatic-publish 0
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.update_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101",
    key="product_def",
    name="Basic Process V5",
    description="Updated sample process",
    kb={"name": "basic-sample", "artifactTypeName": ["sample-artifact"]},
    agentic_activities=[],
    artifact_signals=[],
    user_signals=[],
    start_event={},
    end_event={},
    sequence_flows=[],
    automatic_publish=False
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, KnowledgeBase

manager = AILabManager()

process = AgenticProcess(
    key="product_def",
    name="Basic Process V5",
    description="Updated sample process",
    kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"])
)

updated_process = manager.update_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101",
    process=process,
    automatic_publish=False
)
print(updated_process)
Delete Process
Deletes a process from a specified project by its ID.

Command Line
geai ai-lab delete-process \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --process-id "process-101"
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.delete_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.delete_process(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101"
)
print(response)
Publish Process Revision
Publishes a revision of a process, making it available for use.

Command Line
geai ai-lab publish-process-revision \
  --project-id "2ca6883f-6778-40bb-bcc1-85451fb11107" \
  --process-id "process-101"
Low-Level Service Layer
from pygeai.lab.processes.clients import AgenticProcessClient

client = AgenticProcessClient()
response = client.publish_process_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101"
)
print(response)
High-Level Service Layer
from pygeai.lab.managers import AILabManager

manager = AILabManager()
response = manager.publish_process_revision(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    process_id="process-101"
)
print(response)

Working with the GEAI Lab using the CLI
The geai ai-lab command-line interface (CLI) allows users to interact with the Globant Enterprise AI (GEAI) Lab to manage agents, tools, reasoning strategies, processes, tasks, and process instances. This guide provides step-by-step instructions for performing common operations using CLI commands.

Table of Contents

Prerequisites

Managing Agents

Managing Tools

Managing Reasoning Strategies

Managing Processes

Managing Tasks

Managing Process Instances

Complete Example Workflow

Prerequisites
CLI Installation: Ensure the geai CLI is installed. Contact your GEAI administrator for installation instructions.

Authentication: Obtain your project ID and API token from the GEAI platform.

Environment: A terminal with access to the geai command, typically on Linux, macOS, or Windows (via WSL or similar).

Set the project ID as an environment variable for convenience:

export PROJECT_ID="2ca6883f-6778-40bb-bcc1-85451fb11107"
Managing Agents
Agents are AI entities that perform tasks based on prompts and LLM configurations.

### List Agents

Retrieve a list of agents with filtering options.

geai ai-lab list-agents \
  --project-id "$PROJECT_ID" \
  --status "active" \
  --access-scope "public" \
  --allow-drafts 0 \
  --allow-external 1
Example Output:

- Name: Public Translator V2, ID: f2a160ed-67b3-481d-a822-778cd520f499, Status: active
- Name: Jarvis, ID: f9a744ed-84c0-4afa-bee6-c679320a996d, Status: active
### Create a Public Agent

Create a public agent with detailed configurations.

geai ai-lab create-agent \
  --project-id "$PROJECT_ID" \
  --name "Public Translator V2" \
  --access-scope "public" \
  --public-name "com.genexus.geai.public_translator" \
  --job-description "Translates" \
  --avatar-image "https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png" \
  --description "Agent that translates from any language to English." \
  --agent-data-prompt-instructions "the user will provide a text, you must return the same text translated to English" \
  --agent-data-prompt-input "text" \
  --agent-data-prompt-input "avoid slang indicator" \
  --agent-data-prompt-output '{"key": "translated_text", "description": "translated text, with slang or not depending on the indication. in plain text."}' \
  --agent-data-prompt-output '{"key": "summary", "description": "a summary in the original language of the text to be translated, also in plain text."}' \
  --agent-data-prompt-example '{"inputData": "opitiiiis mundo [no-slang]", "output": "{\"translated_text\":\"hello world\",\"summary\":\"saludo\"}"}' \
  --agent-data-prompt-example '{"inputData": "esto es una prueba pincheguey [keep-slang]", "output": "{\"translated_text\":\"this is a test pal\",\"summary\":\"prueba\"}"}' \
  --agent-data-llm-max-tokens 5000 \
  --agent-data-llm-timeout 0 \
  --agent-data-llm-temperature 0.5 \
  --agent-data-llm-top-k 0 \
  --agent-data-llm-top-p 0 \
  --agent-data-model-name "gpt-4-turbo-preview" \
  --automatic-publish 0
### Create a Private Agent

Create a private agent with automatic publication.

geai ai-lab create-agent \
  --project-id "$PROJECT_ID" \
  --name "Private Translator V4" \
  --access-scope "private" \
  --public-name "com.genexus.geai.private_translatorv4" \
  --job-description "Text Translation Service" \
  --avatar-image "https://www.shareicon.net/data/128x128/2016/11/09/851443_logo_512x512.png" \
  --description "Agent that translates text from any language to English for private use." \
  --agent-data-prompt-instructions "The user provides a text; return it translated to English based on slang preference." \
  --agent-data-prompt-input "text" \
  --agent-data-prompt-input "slang preference (optional)" \
  --agent-data-prompt-output '{"key": "translated_text", "description": "translated text to English, with or without slang based on preference, in plain text."}' \
  --agent-data-prompt-output '{"key": "summary", "description": "a short summary in the original language of the input text, in plain text."}' \
  --agent-data-prompt-example '{"inputData": "hola amigos [no-slang]", "output": "{\"translated_text\":\"hello friends\",\"summary\":\"saludo\"}"}' \
  --agent-data-prompt-example '{"inputData": "qué onda carnal [keep-slang]", "output": "{\"translated_text\":\"what’s up bro\",\"summary\":\"saludo informal\"}"}' \
  --agent-data-llm-max-tokens 6000 \
  --agent-data-llm-timeout 0 \
  --agent-data-llm-temperature 0.7 \
  --agent-data-llm-top-k 0 \
  --agent-data-llm-top-p 0 \
  --agent-data-model-name "gpt-4o" \
  --automatic-publish 1
### Get Agent Information

Retrieve details for a specific agent.

geai ai-lab get-agent \
  --project-id "$PROJECT_ID" \
  --agent-id "f2a160ed-67b3-481d-a822-778cd520f499"
Example Output:

Name: Public Translator V2
ID: f2a160ed-67b3-481d-a822-778cd520f499
Description: Agent that translates from any language to English.
Access Scope: public
### Update an Agent

Update an existing agent’s properties.

geai ai-lab update-agent \
  --project-id "$PROJECT_ID" \
  --agent-id "f64ba214-152b-4dd4-be0d-2920da415f5d" \
  --name "Private Translator V4" \
  --access-scope "private" \
  --public-name "com.genexus.geai.private_translatorv4" \
  --job-description "Enhanced Text Translation Service" \
  --avatar-image "https://www.shareicon.net/data/128x128/2016/11/09/851443_logo_512x512.png" \
  --description "Updated agent that translates text from any language to English for private use with improved accuracy." \
  --agent-data-prompt-instructions "The user provides a text; return it translated to English based on slang preference, ensuring natural phrasing." \
  --agent-data-prompt-input "text" \
  --agent-data-prompt-input "slang preference (optional)" \
  --agent-data-prompt-output '{"key": "translated_text", "description": "translated text to English, with or without slang based on preference, in plain text."}' \
  --agent-data-prompt-output '{"key": "summary", "description": "a concise summary in the original language of the input text, in plain text."}' \
  --agent-data-prompt-example '{"inputData": "hola amigos [no-slang]", "output": "{\"translated_text\":\"hello friends\",\"summary\":\"saludo\"}"}' \
  --agent-data-prompt-example '{"inputData": "qué pasa compa [keep-slang]", "output": "{\"translated_text\":\"what’s good buddy\",\"summary\":\"saludo informal\"}"}' \
  --agent-data-llm-max-tokens 6500 \
  --agent-data-llm-timeout 0 \
  --agent-data-llm-temperature 0.8 \
  --agent-data-llm-top-k 0 \
  --agent-data-llm-top-p 0 \
  --agent-data-model-name "gpt-4o" \
  --automatic-publish 1 \
  --upsert 0
### Create a Sharing Link

Generate a sharing link for an agent.

geai ai-lab create-sharing-link \
  --project-id "$PROJECT_ID" \
  --agent-id "9716a0a1-5eab-4cc9-a611-fa2c3237c511"
Example Output:

Shared Link: https://geai.example.com/share/9716a0a1-5eab-4cc9-a611-fa2c3237c511
### Delete an Agent

Remove an agent from the project.

geai ai-lab delete-agent \
  --project-id "$PROJECT_ID" \
  --agent-id "db43884b-4e6c-4fa5-ad28-952d4eaeffc2"
Managing Tools
Tools extend agent capabilities with external APIs or built-in functions.

### List Tools

Retrieve a list of tools with filtering options.

geai ai-lab list-tools \
  --project-id "$PROJECT_ID" \
  --access-scope "public" \
  --scope "api" \
  --count "100" \
  --allow-drafts 1 \
  --allow-external 1
Example Output:

- Name: gdrive_create_docs_post, ID: 04f217f0-3797-4848-afd9-823108553576
- Name: create_image_post, ID: 0a29f983-536f-4065-862b-3d46edaf9181
### Create a Tool

Create a built-in tool with parameters.

geai ai-lab create-tool \
  --project-id "$PROJECT_ID" \
  --name "sample tool V3" \
  --description "A builtin tool that does something but really does nothing." \
  --scope "builtin" \
  --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": true}' \
  --parameter '{"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static.", "isRequired": true, "type": "config", "fromSecret": false, "value": "b001e30b4016001f5f76b9ae9215ac40"}' \
  --parameter '{"key": "api_token", "dataType": "String", "description": "Configuration that is sensitive.", "isRequired": true, "type": "config", "fromSecret": true, "value": "0cd84dc7-f3f5-4a03-9288-cdfd8d72fde1"}' \
  --automatic-publish 0
### Get Tool Information

Retrieve details for a specific tool.

geai ai-lab get-tool \
  --project-id "$PROJECT_ID" \
  --tool-id "04f217f0-3797-4848-afd9-823108553576"
Example Output:

Name: gdrive_create_docs_post
ID: 04f217f0-3797-4848-afd9-823108553576
Description: Create a new Google Docs document.
### Update a Tool

Update an API-based tool with OpenAPI specification.

geai ai-lab update-tool \
  --project-id "$PROJECT_ID" \
  --tool-id "04f217f0-3797-4848-afd9-823108553576" \
  --name "saia_models_get" \
  --description "Get all LLM models" \
  --scope "api" \
  --parameter '{"key": "Authorization", "dataType": "String", "description": "token with which you are going to connect to SAIA", "isRequired": true, "type": "config", "fromSecret": false, "value": "Bearer default_thRMVCZCV5i1-dI0s-1FR76RbjfFBCWRZbTA4PyL1FWI7h108OVg8i2a2Flf8esvlkqpgCz2pRND3cPVMqPUg9eiHyJZcg--gARu1ACSQrLfFagvQV1DUs7vImZFdERFbyyf567t867PzlkBM9k7lhiT_KNtJZKdxB8KHmKbtR8="}' \
  --open-api-json '{"openapi": "3.0.0", "info": {"title": "LLM Providers API", "version": "2.0.0", "description": "API to retrieve information about models provided by OpenAI."}, "servers": [{"url": "https://api.beta.saia.ai", "description": "Production Server"}], "paths": {"/v2/llm/providers/openai/models": {"get": {"summary": "Retrieve models from OpenAI", "operationId": "saia_models", "description": "Fetches a list of available models along with their properties and configurations.", "responses": {"200": {"description": "Successful response with a list of models.", "content": {"application/json": {"schema": {"type": "object", "properties": {"models": {"type": "array", "items": {"type": "object", "properties": {"contextWindow": {"type": "integer", "description": "Maximum context window size for the model."}, "fullName": {"type": "string", "description": "Full name of the model."}, "id": {"type": "string", "format": "uuid", "description": "Unique identifier of the model."}, "isCustom": {"type": "boolean", "description": "Indicates whether the model is custom."}, "maxOutputTokens": {"type": "integer", "description": "Maximum number of output tokens the model can generate."}, "name": {"type": "string", "description": "Name of the model."}, "priority": {"type": "integer", "description": "Priority level of the model."}, "properties": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string", "format": "uuid", "description": "Unique identifier for the property."}, "name": {"type": "string", "description": "Name of the property."}, "type": {"type": "string", "description": "Data type of the property (e.g., Boolean, String)."}, "value": {"type": "string", "description": "Value of the property."}}}}}, "type": {"type": "string", "description": "Type of the model (e.g., Chat)."}}}}}}}}}, "security": [{"bearerAuth": []}]}}}}' \
  --automatic-publish 1
### Publish a Tool Revision

Publish a specific revision of a tool.

geai ai-lab publish-tool-revision \
  --project-id "$PROJECT_ID" \
  --tool-id "ada1665f-ecea-4635-b2cd-d614756b83a4" \
  --revision "2"
### Get Tool Parameters

Retrieve parameters for a tool.

geai ai-lab get-parameter \
  --project-id "$PROJECT_ID" \
  --tool-public-name "sample_tool_V3" \
  --revision "0" \
  --version "0" \
  --allow-drafts 1
Example Output:

- Key: input, Description: some input that the tool needs HERE., Required: true
- Key: api_token, Description: API token for authentication, Required: true
### Set Tool Parameters

Update parameters for a tool.

geai ai-lab set-parameter \
  --project-id "$PROJECT_ID" \
  --tool-public-name "sample_tool_V3" \
  --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs HERE.", "isRequired": true}' \
  --parameter '{"key": "api_token", "dataType": "String", "description": "API token for authentication", "isRequired": true, "type": "config", "fromSecret": true, "value": "0cd84dc7-f3f5-4a03-9288-cdfd8d72fde1"}'
### Delete a Tool

Remove a tool from the project.

geai ai-lab delete-tool \
  --project-id "$PROJECT_ID" \
  --tool-id "ada1665f-ecea-4635-b2cd-d614756b83a4"
Managing Reasoning Strategies
Reasoning strategies define how agents process information.

### List Reasoning Strategies

Retrieve a list of reasoning strategies.

geai ai-lab list-reasoning-strategies \
  --start "0" \
  --count "50" \
  --allow-external 1 \
  --access-scope "public"
Example Output:

- Name: RSName2, Access Scope: public
- Name: test1, Access Scope: public
### Create a Reasoning Strategy

Create a reasoning strategy with localized descriptions.

geai ai-lab create-reasoning-strategy \
  --project-id "$PROJECT_ID" \
  --name "RSName2" \
  --system-prompt "Let's think step by step." \
  --access-scope "private" \
  --type "addendum" \
  --localized-description '{"language": "spanish", "description": "RSName spanish description"}' \
  --localized-description '{"language": "english", "description": "RSName english description"}' \
  --localized-description '{"language": "japanese", "description": "RSName japanese description"}' \
  --automatic-publish 1
### Update a Reasoning Strategy

Update an existing reasoning strategy.

geai ai-lab update-reasoning-strategy \
  --project-id "$PROJECT_ID" \
  --reasoning-strategy-id "50832dd9-1b69-4842-9349-de993a86661e" \
  --name "test1" \
  --system-prompt "Let's think step by step." \
  --access-scope "private" \
  --type "addendum" \
  --automatic-publish 0 \
  --upsert 1
### Get a Reasoning Strategy

Retrieve details for a specific reasoning strategy.

geai ai-lab get-reasoning-strategy \
  --project-id "$PROJECT_ID" \
  --reasoning-strategy-name "test1"
Example Output:

Name: test1
System Prompt: Let's think step by step.
Access Scope: private
Managing Processes
Processes define workflows involving agents, tasks, and events.

### Create a Process

Create a process with agentic activities and signals.

geai ai-lab create-process \
  --project-id "$PROJECT_ID" \
  --key "product_def" \
  --name "Basic Process V4" \
  --description "This is a sample process" \
  --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
  --agentic-activity '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' \
  --artifact-signal '{"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}' \
  --user-signal '{"key": "signal_done", "name": "process-completed"}' \
  --start-event '{"key": "artifact.upload.1", "name": "artifact.upload"}' \
  --end-event '{"key": "end", "name": "Done"}' \
  --sequence-flow '{"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"}' \
  --sequence-flow '{"key": "step2", "sourceKey": "activityOne", "targetKey": "signal_done"}' \
  --sequence-flow '{"key": "stepEnd", "sourceKey": "signal_done", "targetKey": "end"}' \
  --automatic-publish 0
### Ensure Task Exists

Create a task required for the process.

geai ai-lab create-task \
  --project-id "$PROJECT_ID" \
  --name "basic-task" \
  --description "Basic task for process" \
  --title-template "Basic Task" \
  --automatic-publish 1
### Update a Process

Update an existing process.

geai ai-lab update-process \
  --project-id "$PROJECT_ID" \
  --process-id "cf64f4b2-7f39-4294-94e4-5d441229b441" \
  --name "Basic Process V3" \
  --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
  --agentic-activity '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' \
  --automatic-publish 0 \
  --upsert 0
### Get a Process

Retrieve process details by ID or name.

geai ai-lab get-process \
  --project-id "$PROJECT_ID" \
  --process-id "e8f34673-dd66-4eb2-8d91-886ba0e1da69" \
  --revision "0" \
  --version 0 \
  --allow-drafts 1
Example Output:

Name: Basic Process V4
ID: e8f34673-dd66-4eb2-8d91-886ba0e1da69
Description: This is a sample process
### List Processes

Retrieve a list of processes.

geai ai-lab list-processes \
  --project-id "$PROJECT_ID" \
  --start "0" \
  --count "100" \
  --allow-draft 1
Example Output:

- Name: Basic Process V4, ID: e8f34673-dd66-4eb2-8d91-886ba0e1da69
- Name: Basic Process V3, ID: cf64f4b2-7f39-4294-94e4-5d441229b441
### Publish a Process Revision

Publish a specific revision of a process.

geai ai-lab publish-process-revision \
  --project-id "$PROJECT_ID" \
  --process-id "325e69db-1ae6-4266-82fb-114a2051b708" \
  --revision "1"
### Delete a Process

Remove a process from the project.

geai ai-lab delete-process \
  --project-id "$PROJECT_ID" \
  --process-id "e8f34673-dd66-4eb2-8d91-886ba0e1da69"
Managing Tasks
Tasks define specific actions within processes.

### Create a Task

Create a task with minimal configuration.

geai ai-lab create-task \
  --project-id "$PROJECT_ID" \
  --name "Sample v2" \
  --description "A simple task that requires no tools and defines no prompt" \
  --title-template "Sample Task" \
  --automatic-publish 0
### List Tasks

Retrieve a list of tasks.

geai ai-lab list-tasks \
  --project-id "$PROJECT_ID" \
  --start "0" \
  --count "50" \
  --allow-drafts 1
Example Output:

- Name: Sample v2, ID: 70143b97-8e52-460f-b4cc-c48405a38cff
- Name: basic-task, ID: <task-id>
### Get a Task

Retrieve details for a specific task.

geai ai-lab get-task \
  --project-id "$PROJECT_ID" \
  --task-id "70143b97-8e52-460f-b4cc-c48405a38cff"
Example Output:

Name: Sample v2
ID: 70143b97-8e52-460f-b4cc-c48405a38cff
Description: A simple task that requires no tools and defines no prompt
### Update a Task

Update an existing task.

geai ai-lab update-task \
  --project-id "$PROJECT_ID" \
  --task-id "70143b97-8e52-460f-b4cc-c48405a38cff" \
  --name "Sample v2 Updated" \
  --description "Updated description" \
  --title-template "Updated Sample Task" \
  --automatic-publish 1 \
  --upsert 0
### Publish a Task Revision

Publish a specific revision of a task.

geai ai-lab publish-task-revision \
  --project-id "$PROJECT_ID" \
  --task-id "70143b97-8e52-460f-b4cc-c48405a38cff" \
  --revision "1"
### Delete a Task

Remove a task from the project.

geai ai-lab delete-task \
  --project-id "$PROJECT_ID" \
  --task-id "70143b97-8e52-460f-b4cc-c48405a38cff"
Managing Process Instances
Process instances represent running workflows.

### Start a Process Instance

Start a new instance of a process.

geai ai-lab start-instance \
  --project-id "$PROJECT_ID" \
  --process-name "Basic Process V2" \
  --subject "should we talk about the weather?" \
  --variables '[{"key": "location", "value": "Paris"}]'
Example Output:

Instance ID: <instance-id>
Status: active
### List Process Instances

Retrieve a list of process instances.

geai ai-lab list-processes-instances \
  --project-id "$PROJECT_ID" \
  --process-id "e8f34673-dd66-4eb2-8d91-886ba0e1da69" \
  --is-active 1 \
  --start "0" \
  --count "10"
Example Output:

- Instance ID: <instance-id>, Status: active, Subject: should we talk about the weather?
### Get a Process Instance

Retrieve details for a specific instance.

geai ai-lab get-instance \
  --project-id "$PROJECT_ID" \
  --instance-id "<instance-id>"
Example Output:

Instance ID: <instance-id>
Process: Basic Process V2
Subject: should we talk about the weather?
### Get Instance History

Retrieve the history of a process instance.

geai ai-lab get-instance-history \
  --project-id "$PROJECT_ID" \
  --instance-id "<instance-id>"
Example Output:

- Event: Started, Timestamp: 2025-04-15T10:00:00Z
- Event: Artifact Uploaded, Timestamp: 2025-04-15T10:01:00Z
### Send a User Signal

Send a signal to a running process instance.

geai ai-lab send-user-signal \
  --project-id "$PROJECT_ID" \
  --instance-id "<instance-id>" \
  --signal-name "approval"
### Abort a Process Instance

Stop a running process instance.

geai ai-lab abort-instance \
  --project-id "$PROJECT_ID" \
  --instance-id "<instance-id>"
Complete Example Workflow
This example demonstrates creating an agent, a task, a process, and starting an instance.

Create an Agent:

geai ai-lab create-agent \
  --project-id "$PROJECT_ID" \
  --name "sample-translator" \
  --description "Translator agent for processes" \
  --access-scope "public" \
  --automatic-publish 1
Create a Task:

geai ai-lab create-task \
  --project-id "$PROJECT_ID" \
  --name "basic-task" \
  --description "Basic task for process" \
  --title-template "Basic Task" \
  --automatic-publish 1
Create a Process:

geai ai-lab create-process \
  --project-id "$PROJECT_ID" \
  --key "product_def" \
  --name "Basic Process V4" \
  --description "This is a sample process" \
  --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
  --agentic-activity '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' \
  --artifact-signal '{"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}' \
  --user-signal '{"key": "signal_done", "name": "process-completed"}' \
  --start-event '{"key": "artifact.upload.1", "name": "artifact.upload"}' \
  --end-event '{"key": "end", "name": "Done"}' \
  --sequence-flow '{"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"}' \
  --sequence-flow '{"key": "step2", "sourceKey": "activityOne", "targetKey": "signal_done"}' \
  --sequence-flow '{"key": "stepEnd", "sourceKey": "signal_done", "targetKey": "end"}' \
  --automatic-publish 1
Start a Process Instance:

geai ai-lab start-instance \
  --project-id "$PROJECT_ID" \
  --process-name "Basic Process V4" \
  --subject "should we talk about the weather?" \
  --variables '[{"key": "location", "value": "Paris"}]'
  
  GEAI CLI - AI Lab - Spec Command Documentation
Name
geai - Command Line Interface for Globant Enterprise AI

Synopsis
geai spec <subcommand> --[flag] [flag.arg]
Description
The geai spec command is a utility within the Globant Enterprise AI (GEAI) CLI, designed to load components (agents, tools, tasks, and agentic processes) into the AI Lab from JSON specification files. It supports the following subcommands:

help (or h): Displays help text for the geai spec command.

load-agent (or la): Loads agent(s) from a JSON specification file.

load-tool (or lt): Loads tool(s) from a JSON specification file.

load-task (or ltask): Loads task(s) from a JSON specification file.

load-agentic-process (or lap): Loads agentic process(es) from a JSON specification file.

Each subcommand accepts specific options to configure the loading process, such as project ID (specified as a UUID), file path, and publication settings.

Subcommands and Options
The following subcommands are available under geai spec:

help
Aliases: help, h

Description: Displays help text describing the geai spec command and its subcommands.

Options: None

Usage:

geai spec help
load-agent
Aliases: load-agent, la

Description: Loads one or more agent specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.

Options:

Usage:

geai spec load-agent --project-id 123e4567-e89b-12d3-a456-426614174000 --file agent.json --automatic-publish 0
load-tool
Aliases: load-tool, lt

Description: Loads one or more tool specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.

Options:

Usage:

geai spec load-tool --pid 987fcdeb-1a2b-3c4d-5e6f-7890abcd1234 -f tool.json --ap 1
load-task
Aliases: load-task, ltask

Description: Loads one or more task specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.

Options:

Usage:

geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 -f task.json --ap 0
load-agentic-process
Aliases: load-agentic-process, lap

Description: Loads one or more agentic process specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.

Options:

Usage:

geai spec load-agentic-process --project-id 789a0bcd-2e3f-5c4d-6e7f-9012cdef3456 -f process.json --ap 1
Usage Examples
Below are example commands demonstrating the usage of geai spec subcommands, using UUIDs for project IDs.

Example 1: Display Help

Display the help text for the geai spec command.

geai spec help
Output (example):

geai spec - Command Line Interface for Globant Enterprise AI
Usage: geai spec <subcommand> --[flag] [flag.arg]
Subcommands:
  help, h                    Display help text
  load-agent, la             Load agent from JSON specification
  load-tool, lt              Load tool from JSON specification
  load-task, ltask           Load task from JSON specification
  load-agentic-process, lap  Load agentic process from JSON specification
...
Example 2: Load a Single Agent

Load an agent from a JSON file into project with UUID 123e4567-e89b-12d3-a456-426614174000 as a draft.

geai spec load-agent --project-id 123e4567-e89b-12d3-a456-426614174000 --file agent.json --automatic-publish 0
Output (example):

Created agent detail:
<agent details>
Example 3: Load and Publish a Tool

Load a tool from a JSON file into project with UUID 987fcdeb-1a2b-3c4d-5e6f-7890abcd1234 and publish it.

geai spec load-tool --pid 987fcdeb-1a2b-3c4d-5e6f-7890abcd1234 -f tool.json --ap 1
Output (example):

Created tool detail:
<tool details>
Example 4: Load a Task

Load a task from a JSON file into project with UUID 456e7890-f1a2-4b3c-5d6e-8901bcde2345 as a draft.

geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 -f task.json --ap 0
Output (example):

Created task detail:
<task details>
Example 5: Load and Publish an Agentic Process

Load an agentic process from a JSON file into project with UUID 789a0bcd-2e3f-5c4d-6e7f-9012cdef3456 and publish it.

geai spec load-agentic-process --project-id 789a0bcd-2e3f-5c4d-6e7f-9012cdef3456 -f process.json --ap 1
Output (example):

Created agentic process detail:
<process details>
Example 6: Missing File Path (Error Case)

Attempt to load a task without specifying the file path.

geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 --ap 0
Output:

Error: Cannot load task definition without specifying path to JSON file.
JSON Specification Formats
The load-agent, load-tool, load-task, and load-agentic-process subcommands expect JSON files containing agent, tool, task, or agentic process specifications, respectively. The JSON file can contain a single specification (object) or multiple specifications (array).

Agent Specification Example

Below is an example of a single agent specification for a “Public Translator V2x” agent.

{
  "name": "Public Translator V2x",
  "accessScope": "private",
  "publicName": "com.genexus.geai.public_translator_v2x",
  "jobDescription": "Translates",
  "avatarImage": "https://www.shareicon.net/data/128x128/2016/11/09/851442_logo_512x512.png",
  "description": "Agent that translates from any language to english.",
  "agentData": {
    "prompt": {
      "instructions": "the user will provide a text, you must return the same text translated to english",
      "inputs": ["text", "avoid slang indicator"],
      "outputs": [
        {
          "key": "translated_text",
          "description": "translated text, with slang or not depending on the indication. in plain text."
        },
        {
          "key": "summary",
          "description": "a summary in the original language of the text to be translated, also in plain text."
        }
      ],
      "examples": [
        {
          "inputData": "opitiiiis mundo [no-slang]",
          "output": "{\"translated_text\":\"hello world\",\"summary\":\"saludo\"}"
        },
        {
          "inputData": "esto es una prueba pincheguey [keep-slang]",
          "output": "{\"translated_text\":\"this is a test pal\",\"summary\":\"prueba\"}"
        }
      ]
    },
    "llmConfig": {
      "maxTokens": 5000,
      "timeout": 0,
      "sampling": {
        "temperature": 0.5,
        "topK": 0,
        "topP": 0
      }
    },
    "models": [
      { "name": "gpt-4-turbo-preview" }
    ]
  }
}
Tool Specification Example

Below is an example of a single tool specification for a “Weather Forecaster” tool.

{
  "name": "Weather Forecaster",
  "description": "A builtin tool that provides weather forecasts based on location and date.",
  "scope": "builtin",
  "parameters": [
    {
      "key": "location_date",
      "dataType": "String",
      "description": "Location and date for the weather forecast (e.g., 'New York, 2025-05-22').",
      "isRequired": true
    },
    {
      "key": "forecast_type",
      "dataType": "String",
      "description": "Type of forecast (e.g., daily, hourly), configured statically.",
      "isRequired": true,
      "type": "config",
      "fromSecret": false,
      "value": "daily"
    },
    {
      "key": "weather_api_key",
      "dataType": "String",
      "description": "API key for accessing the weather service, stored in secret manager.",
      "isRequired": true,
      "type": "config",
      "fromSecret": true,
      "value": "6f7a8b9c-0d1e-2f3a-4b5c-6d7e8f9a0b1c"
    }
  ]
}
Task Specification Example

Below is an example of a single task specification for an “Email Review v1” task.

{
  "name": "Email Review v1",
  "description": "A simple task to review and categorize email content, requiring no tools or prompts.",
  "titleTemplate": "Email Review Task"
}
Agentic Process Specification Example

Below is an example of a single agentic process specification for a “Content Moderation Process.”

{
  "key": "content_moderation_proc",
  "name": "Content Moderation Process",
  "description": "A process to review and moderate user-generated content for compliance.",
  "kb": {
    "name": "content-moderation-kb",
    "artifactTypeName": ["content-artifact"]
  },
  "agenticActivities": [
    {
      "key": "moderate_content",
      "name": "Moderate Content",
      "taskName": "content-moderation-task",
      "agentName": "content-moderator",
      "agentRevisionId": 0
    }
  ],
  "artifactSignals": [
    {
      "key": "artifact.content.upload.1",
      "name": "content.upload",
      "handlingType": "C",
      "artifactTypeName": ["content-artifact"]
    }
  ],
  "userSignals": [
    {
      "key": "signal_content_done",
      "name": "content-moderation-completed"
    }
  ],
  "startEvent": {
    "key": "artifact.content.upload.1",
    "name": "content.upload"
  },
  "endEvent": {
    "key": "end",
    "name": "Done"
  },
  "sequenceFlows": [
    {
      "key": "step1",
      "sourceKey": "artifact.content.upload.1",
      "targetKey": "moderate_content"
    },
    {
      "key": "step2",
      "sourceKey": "moderate_content",
      "targetKey": "signal_content_done"
    },
    {
      "key": "stepEnd",
      "sourceKey": "signal_content_done",
      "targetKey": "end"
    }
  ]
}
Error Handling
The geai spec subcommands may raise the following errors:

MissingRequirementException: - Triggered if required options (--project-id or --file) are not provided. - Example: Cannot load task definition without specifying path to JSON file.

File Loading Errors: - Invalid or inaccessible JSON files will cause errors during loading, logged and displayed to stderr.

Parsing Errors: - Malformed JSON specifications may fail during parsing, with errors output to stderr.

Notes
The project_id must be a valid UUID (e.g., 123e4567-e89b-12d3-a456-426614174000).

JSON files must conform to the expected format for agents, tools, tasks, or agentic processes, as shown in the examples above.

The automatic_publish option (0 or 1) determines whether the component is created as a draft or published immediately.

Ensure the project UUID exists in the AI Lab and the JSON file path is valid before running the command.

Multiple components can be loaded from a single JSON file if it contains an array of specifications.

from typing import Union, Optional, List

from pygeai.core.base.mappers import ResponseMapper
from pygeai.core.base.responses import ErrorListResponse, EmptyResponse
from pygeai.core.handlers import ErrorHandler
from pygeai.lab.agents.clients import AgentClient
from pygeai.lab.agents.mappers import AgentMapper
from pygeai.lab.models import FilterSettings, Agent, AgentList, SharingLink, Tool, ToolList, ToolParameter, \
    ReasoningStrategyList, ReasoningStrategy, AgenticProcess, AgenticProcessList, ProcessInstanceList, Task, TaskList, \
    ProcessInstance, Variable, VariableList, KnowledgeBase, KnowledgeBaseList, JobList
from pygeai.lab.processes.clients import AgenticProcessClient
from pygeai.lab.processes.mappers import AgenticProcessMapper, ProcessInstanceMapper, TaskMapper, KnowledgeBaseMapper, \
    JobMapper
from pygeai.lab.strategies.clients import ReasoningStrategyClient
from pygeai.lab.strategies.mappers import ReasoningStrategyMapper
from pygeai.lab.tools.clients import ToolClient
from pygeai.lab.tools.mappers import ToolMapper


class AILabManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default"):
        self.__agent_client = AgentClient(api_key=api_key, base_url=base_url, alias=alias)
        self.__tool_client = ToolClient(api_key=api_key, base_url=base_url, alias=alias)
        self.__reasoning_strategy_client = ReasoningStrategyClient(api_key=api_key, base_url=base_url, alias=alias)
        self.__process_client = AgenticProcessClient(api_key=api_key, base_url=base_url, alias=alias)

    def get_agent_list(
            self,
            project_id: str,
            filter_settings: FilterSettings = None
    ) -> AgentList:
        '''
        Retrieves a list of agents for a given project based on filter settings.

        This method queries the agent client to fetch a list of agents associated with the specified
        project ID, applying the provided filter settings. If the response contains errors, it maps
        them to an `ErrorListResponse`. Otherwise, it maps the response to an `AgentList`.

        :param project_id: str - The ID of the project to retrieve agents for.
        :param filter_settings: FilterSettings - The filter settings to apply to the agent list query.
            Includes fields such as status, start, count, access_scope, allow_drafts, and allow_external.
        :return: Union[AgentList, ErrorListResponse] - An `AgentList` containing the retrieved agents
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        if not filter_settings:
            filter_settings = FilterSettings()

        response_data = self.__agent_client.list_agents(
            project_id=project_id,
            status=filter_settings.status,
            start=filter_settings.start,
            count=filter_settings.count,
            access_scope=filter_settings.access_scope,
            allow_drafts=filter_settings.allow_drafts,
            allow_external=filter_settings.allow_external
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_agent_list(response_data)

        return result

    def create_agent(
            self,
            project_id: str,
            agent: Agent,
            automatic_publish: bool = False
    ) -> Union[Agent, ErrorListResponse]:
        '''
        Creates a new agent in the specified project using the provided agent configuration.

        This method sends a request to the agent client to create an agent based on the attributes
        of the provided `Agent` object. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to an `Agent` object.

        :param project_id: str - Unique identifier of the project where the agent will be created.
        :param agent: Agent - The agent configuration object containing all necessary details,
            including name, access scope, public name, job description, avatar image, description,
            and agent data (prompt, LLM config, and models).
        :param automatic_publish: bool - Whether to automatically publish the agent after creation.
            Defaults to False.
        :return: Union[Agent, ErrorListResponse] - An `Agent` object representing the created agent
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__agent_client.create_agent(
            project_id=project_id,
            name=agent.name,
            access_scope=agent.access_scope,
            public_name=agent.public_name,
            job_description=agent.job_description,
            avatar_image=agent.avatar_image,
            description=agent.description,
            agent_data_prompt=agent.agent_data.prompt.to_dict() if agent.agent_data is not None else None,
            agent_data_llm_config=agent.agent_data.llm_config.to_dict() if agent.agent_data is not None else None,
            agent_data_models=agent.agent_data.models.to_dict() if agent.agent_data is not None else None,
            agent_data_resource_pools=agent.agent_data.resource_pools.to_dict() if agent.agent_data and agent.agent_data.resource_pools else None,
            automatic_publish=automatic_publish
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_agent(response_data)

        return result

    def update_agent(
            self,
            project_id: str,
            agent: Agent,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Union[Agent, ErrorListResponse]:
        '''
        Updates an existing agent in the specified project using the provided agent configuration.

        This method sends a request to the agent client to update an agent identified by `agent_id`
        (or `agent.id` if not provided) based on the attributes of the provided `Agent` object.
        It can optionally publish the agent automatically or perform an upsert if the agent doesn’t exist.
        If the response contains errors, it maps them to an `ErrorListResponse`. Otherwise, it maps
        the response to an `Agent` object.

        :param project_id: str - Unique identifier of the project where the agent resides.
        :param agent: Agent - The agent configuration object containing updated details,
            including id, name, access scope, public name, job description, avatar image, description,
            and agent data (prompt, LLM config, and models).
        :param automatic_publish: bool - Whether to automatically publish the agent after updating.
            Defaults to False.
        :param upsert: bool - Whether to insert the agent if it does not exist (upsert) instead of
            just updating. Defaults to False.
        :return: Union[Agent, ErrorListResponse] - An `Agent` object representing the updated agent
            if successful, or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither `agent_id` nor `agent.id` is provided.
        '''
        response_data = self.__agent_client.update_agent(
            project_id=project_id,
            agent_id=agent.id,
            name=agent.name,
            access_scope=agent.access_scope,
            public_name=agent.public_name,
            job_description=agent.job_description,
            avatar_image=agent.avatar_image,
            description=agent.description,
            agent_data_prompt=agent.agent_data.prompt.to_dict() if agent.agent_data is not None else None,
            agent_data_llm_config=agent.agent_data.llm_config.to_dict() if agent.agent_data is not None else None,
            agent_data_models=agent.agent_data.models.to_dict() if agent.agent_data is not None else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_agent(response_data)

        return result

    def get_agent(
            self,
            project_id: str,
            agent_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[Agent, ErrorListResponse]:
        '''
        Retrieves details of a specific agent from the specified project.

        This method sends a request to the agent client to retrieve an agent identified by `agent_id`
        from the specified project. Optional filter settings can be provided to specify the revision,
        version, and whether to allow drafts. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to an `Agent` object.

        :param project_id: str - Unique identifier of the project where the agent resides.
        :param agent_id: str - Unique identifier of the agent to retrieve.
        :param filter_settings: FilterSettings, optional - Settings to filter the agent retrieval,
            including revision (defaults to "0"), version (defaults to 0), and allow_drafts (defaults to True).
        :return: Union[Agent, ErrorListResponse] - An `Agent` object representing the retrieved agent
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__agent_client.get_agent(
            project_id=project_id,
            agent_id=agent_id,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_agent(response_data)

        return result

    def create_sharing_link(
            self,
            project_id: str,
            agent_id: str
    ) -> Union[SharingLink, ErrorListResponse]:
        '''
        Creates a sharing link for a specific agent in the specified project.

        This method sends a request to the agent client to create a sharing link for the agent
        identified by `agent_id` in the specified project. If the response contains errors, it maps
        them to an `ErrorListResponse`. Otherwise, it maps the response to a `SharingLink` object.

        :param project_id: str - Unique identifier of the project where the agent resides.
        :param agent_id: str - Unique identifier of the agent for which to create a sharing link.
        :return: Union[SharingLink, ErrorListResponse] - A `SharingLink` object representing the
            sharing link details if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__agent_client.create_sharing_link(
            project_id=project_id,
            agent_id=agent_id
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_sharing_link(response_data)

        return result

    def publish_agent_revision(
            self,
            project_id: str,
            agent_id: str,
            revision: str
    ) -> Union[Agent, ErrorListResponse]:
        '''
        Publishes a specific revision of an agent in the specified project.

        This method sends a request to the agent client to publish the specified revision of the agent
        identified by `agent_id` in the specified project. If the response contains errors, it maps
        them to an `ErrorListResponse`. Otherwise, it maps the response to an `Agent` object
        representing the published agent.

        :param project_id: str - Unique identifier of the project where the agent resides.
        :param agent_id: str - Unique identifier of the agent to publish.
        :param revision: str - Revision of the agent to publish.
        :return: Union[Agent, ErrorListResponse] - An `Agent` object representing the published agent
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__agent_client.publish_agent_revision(
            project_id=project_id,
            agent_id=agent_id,
            revision=revision
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgentMapper.map_to_agent(response_data)

        return result

    def delete_agent(
            self,
            project_id: str,
            agent_id: str
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Deletes a specific agent from the specified project.

        This method sends a request to the agent client to delete the agent identified by `agent_id`
        from the specified project. Returns True if the deletion is successful (indicated by an
        empty response or success confirmation), or an `ErrorListResponse` if the API returns errors.

        :param project_id: str - Unique identifier of the project where the agent resides.
        :param agent_id: str - Unique identifier of the agent to delete.
        :return: Union[EmptyResponse, ErrorListResponse] - EmptyResponse if the agent was deleted successfully,
            or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__agent_client.delete_agent(
            project_id=project_id,
            agent_id=agent_id
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            response_data = response_data if response_data else "Agent deleted successfully"
            result = ResponseMapper.map_to_empty_response(response_data)

        return result

    def create_tool(
            self,
            project_id: str,
            tool: Tool,
            automatic_publish: bool = False
    ) -> Union[Tool, ErrorListResponse]:
        '''
        Creates a new tool in the specified project using the provided tool configuration.

        This method sends a request to the tool client to create a tool based on the attributes
        of the provided `Tool` object, including name, description, scope, access_scope, public_name,
        icon, open_api, open_api_json, report_events, and parameters. If the response contains errors,
        it maps them to an `ErrorListResponse`. Otherwise, it maps the response to a `Tool` object.

        :param project_id: str - Unique identifier of the project where the tool will be created.
        :param tool: Tool - The tool configuration object containing name, description, scope,
            access_scope, public_name, icon, open_api, open_api_json, report_events, and parameters.
            Optional fields (e.g., id, access_scope) are included if set in the `Tool` object.
        :param automatic_publish: bool - Whether to automatically publish the tool after creation.
            Defaults to False.
        :return: Union[Tool, ErrorListResponse] - A `Tool` object representing the created tool
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        parameters = [param.to_dict() for param in tool.parameters] if tool.parameters else []

        response_data = self.__tool_client.create_tool(
            project_id=project_id,
            name=tool.name,
            description=tool.description,
            scope=tool.scope,
            access_scope=tool.access_scope,
            public_name=tool.public_name,
            icon=tool.icon,
            open_api=tool.open_api,
            open_api_json=tool.open_api_json,
            report_events=tool.report_events,
            parameters=parameters,
            automatic_publish=automatic_publish
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_tool(response_data)

        return result

    def update_tool(
            self,
            project_id: str,
            tool: Tool,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Union[Tool, ErrorListResponse]:
        '''
        Updates an existing tool in the specified project or upserts it if specified.

        This method sends a request to the tool client to update a tool identified by `tool.id`
        based on the attributes of the provided `Tool` object, including name, description, scope,
        access_scope, public_name, icon, open_api, open_api_json, report_events, and parameters.
        It can optionally publish the tool automatically or perform an upsert if the tool doesn’t exist.
        If the response contains errors, it maps them to an `ErrorListResponse`. Otherwise, it maps
        the response to a `Tool` object.

        :param project_id: str - Unique identifier of the project where the tool resides.
        :param tool: Tool - The tool configuration object containing updated details, including
            id, name, description, scope, access_scope, public_name, icon, open_api, open_api_json,
            report_events, and parameters.
        :param automatic_publish: bool - Whether to automatically publish the tool after updating.
            Defaults to False.
        :param upsert: bool - Whether to insert the tool if it does not exist (upsert) instead of
            just updating. Defaults to False.
        :return: Union[Tool, ErrorListResponse] - A `Tool` object representing the updated tool
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        parameters = [param.to_dict() for param in tool.parameters] if tool.parameters else []

        response_data = self.__tool_client.update_tool(
            project_id=project_id,
            tool_id=tool.id,
            name=tool.name,
            description=tool.description,
            scope=tool.scope,
            access_scope=tool.access_scope,
            public_name=tool.public_name,
            icon=tool.icon,
            open_api=tool.open_api,
            open_api_json=tool.open_api_json,
            report_events=tool.report_events,
            parameters=parameters,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_tool(response_data)

        return result

    def get_tool(
            self,
            project_id: str,
            tool_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[Tool, ErrorListResponse]:
        '''
        Retrieves details of a specific tool from the specified project.

        This method sends a request to the tool client to retrieve a tool identified by `tool_id`
        from the specified project. Optional filter settings can be provided to specify the revision,
        version, and whether to allow drafts. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to a `Tool` object.

        :param project_id: str - Unique identifier of the project where the tool resides.
        :param tool_id: str - Unique identifier of the tool to retrieve.
        :param filter_settings: FilterSettings, optional - Settings to filter the tool retrieval,
            including revision (defaults to "0"), version (defaults to "0"), and allow_drafts (defaults to True).
        :return: Union[Tool, ErrorListResponse] - A `Tool` object representing the retrieved tool
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__tool_client.get_tool(
            project_id=project_id,
            tool_id=tool_id,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_tool(response_data)

        return result

    def delete_tool(
            self,
            project_id: str,
            tool_id: Optional[str] = None,
            tool_name: Optional[str] = None
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Deletes a specific tool from the specified project.

        This method sends a request to the tool client to delete the tool identified by either
        `tool_id` or `tool_name`. Returns an `EmptyResponse` if the deletion is successful,
        or an `ErrorListResponse` if the API returns errors.

        :param project_id: str - Unique identifier of the project where the tool resides.
        :param tool_id: str, optional - Unique identifier of the tool to delete.
        :param tool_name: str, optional - Name of the tool to delete.
        :return: Union[EmptyResponse, ErrorListResponse] - `EmptyResponse` if the tool was deleted successfully,
            or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither tool_id nor tool_name is provided.
        '''
        if not (tool_id or tool_name):
            raise ValueError("Either tool_id or tool_name must be provided.")

        response_data = self.__tool_client.delete_tool(
            project_id=project_id,
            tool_id=tool_id,
            tool_name=tool_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            response_data = response_data if response_data else "Tool deleted successfully"
            result = ResponseMapper.map_to_empty_response(response_data)

        return result

    def list_tools(
            self,
            project_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[ToolList, ErrorListResponse]:
        '''
        Retrieves a list of tools associated with the specified project.

        This method queries the tool client to fetch a list of tools for the given project ID,
        applying the specified filter settings. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to a `ToolList` object using `ToolMapper`.

        :param project_id: str - Unique identifier of the project.
        :param filter_settings: FilterSettings, optional - Settings to filter the tool list query,
            including id (defaults to ""), count (defaults to "100"), access_scope (defaults to "public"),
            allow_drafts (defaults to True), scope (defaults to "api"), and allow_external (defaults to True).
        :return: Union[ToolList, ErrorListResponse] - A `ToolList` object containing the retrieved tools
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        if filter_settings is None:
            filter_settings = FilterSettings(
                id="",
                count="100",
                access_scope="public",
                allow_drafts=True,
                scope="api",
                allow_external=True
            )

        response_data = self.__tool_client.list_tools(
            project_id=project_id,
            id=filter_settings.id,
            count=filter_settings.count,
            access_scope=filter_settings.access_scope,
            allow_drafts=filter_settings.allow_drafts,
            scope=filter_settings.scope,
            allow_external=filter_settings.allow_external
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_tool_list(response_data)

        return result

    def publish_tool_revision(
            self,
            project_id: str,
            tool_id: str,
            revision: str
    ) -> Union[Tool, ErrorListResponse]:
        '''
        Publishes a specific revision of a tool in the specified project.

        This method sends a request to the tool client to publish the specified revision of the tool
        identified by `tool_id`. If the response contains errors, it maps them to an `ErrorListResponse`.
        Otherwise, it maps the response to a `Tool` object representing the published tool.

        :param project_id: str - Unique identifier of the project where the tool resides.
        :param tool_id: str - Unique identifier of the tool to publish.
        :param revision: str - Revision of the tool to publish.
        :return: Union[Tool, ErrorListResponse] - A `Tool` object representing the published tool
            if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__tool_client.publish_tool_revision(
            project_id=project_id,
            tool_id=tool_id,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_tool(response_data)

        return result

    def get_parameter(
            self,
            project_id: str,
            tool_id: Optional[str] = None,
            tool_public_name: Optional[str] = None,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[List[ToolParameter], ErrorListResponse]:
        '''
        Retrieves details of parameters for a specific tool in the specified project.

        This method sends a request to the tool client to retrieve parameters for a tool identified
        by either `tool_id` or `tool_public_name`. Optional filter settings can specify revision,
        version, and whether to allow drafts. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to a list of `ToolParameter` objects.

        :param project_id: str - Unique identifier of the project.
        :param tool_id: str, optional - Unique identifier of the tool whose parameters are to be retrieved.
        :param tool_public_name: str, optional - Public name of the tool whose parameters are to be retrieved.
        :param filter_settings: FilterSettings, optional - Settings to filter the parameter retrieval,
            including revision (defaults to "0"), version (defaults to "0"), and allow_drafts (defaults to True).
        :return: Union[List[ToolParameter], ErrorListResponse] - A list of `ToolParameter` objects if successful,
            or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither tool_id nor tool_public_name is provided.
        '''
        if not (tool_id or tool_public_name):
            raise ValueError("Either tool_id or tool_public_name must be provided.")

        if filter_settings is None:
            filter_settings = FilterSettings(
                revision="0",
                version="0",
                allow_drafts=True
            )

        response_data = self.__tool_client.get_parameter(
            project_id=project_id,
            tool_id=tool_id,
            tool_public_name=tool_public_name,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ToolMapper.map_to_parameter_list(response_data)

        return result

    def set_parameter(
            self,
            project_id: str,
            tool_id: Optional[str] = None,
            tool_public_name: Optional[str] = None,
            parameters: List[ToolParameter] = None
    ) -> Union[Tool, ErrorListResponse]:
        '''
        Sets or updates parameters for a specific tool in the specified project.

        This method sends a request to the tool client to set parameters for a tool identified by
        either `tool_id` or `tool_public_name`. If the response contains errors, it maps them to an
        `ErrorListResponse`. Otherwise, it maps the response to a `Tool` object.

        :param project_id: str - Unique identifier of the project.
        :param tool_id: str, optional - Unique identifier of the tool whose parameters are to be set.
        :param tool_public_name: str, optional - Public name of the tool whose parameters are to be set.
        :param parameters: List[ToolParameter] - List of parameter objects defining the tool's parameters.
        :return: Union[Tool, ErrorListResponse] - A `Tool` object representing the updated tool if successful,
            or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither tool_id nor tool_public_name is provided, or if parameters is None or empty.
        '''
        if not (tool_id or tool_public_name):
            raise ValueError("Either tool_id or tool_public_name must be provided.")
        if not parameters:
            raise ValueError("Parameters list must be provided and non-empty.")

        params_dict = [param.to_dict() for param in parameters]

        response_data = self.__tool_client.set_parameter(
            project_id=project_id,
            tool_id=tool_id,
            tool_public_name=tool_public_name,
            parameters=params_dict
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ResponseMapper.map_to_empty_response(response_data)

        return result

    def list_reasoning_strategies(
            self,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[ReasoningStrategyList, ErrorListResponse]:
        if filter_settings is None:
            filter_settings = FilterSettings(
                start="0",
                count="100",
                allow_external=True,
                access_scope="public"
            )

        response_data = self.__reasoning_strategy_client.list_reasoning_strategies(
            name=filter_settings.name or "",
            start=filter_settings.start,
            count=filter_settings.count,
            allow_external=filter_settings.allow_external,
            access_scope=filter_settings.access_scope
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ReasoningStrategyMapper.map_to_reasoning_strategy_list(response_data)

        return result

    def create_reasoning_strategy(
            self,
            project_id: str,
            strategy: ReasoningStrategy,
            automatic_publish: bool = False
    ) -> Union[ReasoningStrategy, ErrorListResponse]:
        response_data = self.__reasoning_strategy_client.create_reasoning_strategy(
            project_id=project_id,
            name=strategy.name,
            system_prompt=strategy.system_prompt,
            access_scope=strategy.access_scope,
            strategy_type=strategy.type,
            localized_descriptions=[desc.to_dict() for desc in strategy.localized_descriptions],
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)

        return result

    def update_reasoning_strategy(
            self,
            project_id: str,
            strategy: ReasoningStrategy,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Union[ReasoningStrategy, ErrorListResponse]:
        response_data = self.__reasoning_strategy_client.update_reasoning_strategy(
            project_id=project_id,
            reasoning_strategy_id=strategy.id,
            name=strategy.name,
            system_prompt=strategy.system_prompt,
            access_scope=strategy.access_scope,
            strategy_type=strategy.type,
            localized_descriptions=[desc.to_dict() for desc in strategy.localized_descriptions],
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)

        return result

    def get_reasoning_strategy(
            self,
            project_id: str,
            reasoning_strategy_id: Optional[str] = None,
            reasoning_strategy_name: Optional[str] = None
    ) -> Union[ReasoningStrategy, ErrorListResponse]:
        if not (reasoning_strategy_id or reasoning_strategy_name):
            raise ValueError("Either reasoning_strategy_id or reasoning_strategy_name must be provided.")

        response_data = self.__reasoning_strategy_client.get_reasoning_strategy(
            project_id=project_id,
            reasoning_strategy_id=reasoning_strategy_id,
            reasoning_strategy_name=reasoning_strategy_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ReasoningStrategyMapper.map_to_reasoning_strategy(response_data)

        return result

    def create_process(
            self,
            project_id: str,
            process: AgenticProcess,
            automatic_publish: bool = False
    ) -> Union[AgenticProcess, ErrorListResponse]:
        '''
        Creates a new process in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process: AgenticProcess - The process configuration to create.
        :param automatic_publish: bool - Whether to publish the process after creation. Defaults to False.
        :return: Union[AgenticProcess, ErrorListResponse] - The created process if successful, or an error response.
        '''
        response_data = self.__process_client.create_process(
            project_id=project_id,
            key=process.key,
            name=process.name,
            description=process.description,
            kb=process.kb.to_dict(),
            agentic_activities=[activity.to_dict() for activity in process.agentic_activities] if process.agentic_activities else None,
            artifact_signals=[signal.to_dict() for signal in process.artifact_signals] if process.artifact_signals else None,
            user_signals=[signal.to_dict() for signal in process.user_signals] if process.user_signals else None,
            start_event=process.start_event.to_dict(),
            end_event=process.end_event.to_dict(),
            sequence_flows=[flow.to_dict() for flow in process.sequence_flows] if process.sequence_flows else None,
            variables=[variable.to_dict() for variable in process.variables] if process.variables else None,
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgenticProcessMapper.map_to_agentic_process(response_data)

        return result

    def update_process(
            self,
            project_id: str,
            process: AgenticProcess,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Union[AgenticProcess, ErrorListResponse]:
        '''
        Updates an existing process in the specified project or upserts it if specified.

        :param project_id: str - Unique identifier of the project.
        :param process: AgenticProcess - The process configuration to update.
        :param automatic_publish: bool - Whether to publish the process after updating. Defaults to False.
        :param upsert: bool - Whether to insert the process if it does not exist. Defaults to False.
        :return: Union[AgenticProcess, ErrorListResponse] - The updated process if successful, or an error response.
        '''
        response_data = self.__process_client.update_process(
            project_id=project_id,
            process_id=process.id,
            name=process.name,
            key=process.key,
            description=process.description,
            kb=process.kb.to_dict(),
            agentic_activities=[activity.to_dict() for activity in process.agentic_activities] if process.agentic_activities else None,
            artifact_signals=[signal.to_dict() for signal in process.artifact_signals] if process.artifact_signals else None,
            user_signals=[signal.to_dict() for signal in process.user_signals] if process.user_signals else None,
            start_event=process.start_event.to_dict(),
            end_event=process.end_event.to_dict(),
            sequence_flows=[flow.to_dict() for flow in process.sequence_flows] if process.sequence_flows else None,
            variables=[variable.to_dict() for variable in process.variables] if process.variables else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgenticProcessMapper.map_to_agentic_process(response_data)

        return result

    def get_process(
            self,
            project_id: str,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[AgenticProcess, ErrorListResponse]:
        '''
        Retrieves details of a specific process in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process_id: Optional[str] - Unique identifier of the process to retrieve. Defaults to None.
        :param process_name: Optional[str] - Name of the process to retrieve. Defaults to None.
        :param filter_settings: Optional[FilterSettings] - Settings to filter the process retrieval (revision, version, allow_drafts).
        :return: Union[AgenticProcess, ErrorListResponse] - The retrieved process if successful, or an error response.
        :raises ValueError: If neither process_id nor process_name is provided.
        '''
        if not (process_id or process_name):
            raise ValueError("Either process_id or process_name must be provided.")

        filter_settings = filter_settings or FilterSettings(revision="0", version="0", allow_drafts=True)
        response_data = self.__process_client.get_process(
            project_id=project_id,
            process_id=process_id,
            process_name=process_name,
            revision=filter_settings.revision,
            version=filter_settings.version,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgenticProcessMapper.map_to_agentic_process(response_data)

        return result

    def list_processes(
            self,
            project_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[AgenticProcessList, ErrorListResponse]:
        '''
        Retrieves a list of processes in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param filter_settings: Optional[FilterSettings] - Settings to filter the process list (id, name, status, start, count, allow_drafts).
        :return: Union[AgenticProcessList, ErrorListResponse] - The list of processes if successful, or an error response.
        '''
        filter_settings = filter_settings or FilterSettings(start="0", count="100", allow_drafts=True)
        response_data = self.__process_client.list_processes(
            project_id=project_id,
            id=filter_settings.id,
            name=filter_settings.name,
            status=filter_settings.status,
            start=filter_settings.start,
            count=filter_settings.count,
            allow_draft=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgenticProcessMapper.map_to_agentic_process_list(response_data)

        return result

    def list_process_instances(
            self,
            project_id: str,
            process_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[ProcessInstanceList, ErrorListResponse]:
        '''
        Retrieves a list of process instances for a specific process in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process_id: str - Unique identifier of the process to list instances for.
        :param filter_settings: Optional[FilterSettings] - Settings to filter the instance list (is_active, start, count).
        :return: Union[ProcessInstanceList, ErrorListResponse] - The list of process instances if successful, or an error response.
        '''
        filter_settings = filter_settings or FilterSettings(start="0", count="10", is_active=True)
        response_data = self.__process_client.list_process_instances(
            project_id=project_id,
            process_id=process_id,
            is_active=filter_settings.is_active,
            start=filter_settings.start,
            count=filter_settings.count
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ProcessInstanceMapper.map_to_process_instance_list(response_data)

        return result

    def delete_process(
            self,
            project_id: str,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Deletes a specific process in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process_id: Optional[str] - Unique identifier of the process to delete. Defaults to None.
        :param process_name: Optional[str] - Name of the process to delete. Defaults to None.
        :return: Union[EmptyResponse, ErrorListResponse] - Empty response if successful, or an error response.
        :raises ValueError: If neither process_id nor process_name is provided.
        '''
        if not (process_id or process_name):
            raise ValueError("Either process_id or process_name must be provided.")

        response_data = self.__process_client.delete_process(
            project_id=project_id,
            process_id=process_id,
            process_name=process_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ResponseMapper.map_to_empty_response(response_data or "Process deleted successfully")

        return result

    def publish_process_revision(
            self,
            project_id: str,
            process_id: Optional[str] = None,
            process_name: Optional[str] = None,
            revision: str = None
    ) -> Union[AgenticProcess, ErrorListResponse]:
        '''
        Publishes a specific revision of a process in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process_id: Optional[str] - Unique identifier of the process to publish. Defaults to None.
        :param process_name: Optional[str] - Name of the process to publish. Defaults to None.
        :param revision: str - Revision of the process to publish. Defaults to None.
        :return: Union[AgenticProcess, ErrorListResponse] - The published process if successful, or an error response.
        :raises ValueError: If neither process_id nor process_name is provided, or if revision is not specified.
        '''
        if not (process_id or process_name) or not revision:
            raise ValueError("Either process_id or process_name and revision must be provided.")

        response_data = self.__process_client.publish_process_revision(
            project_id=project_id,
            process_id=process_id,
            process_name=process_name,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = AgenticProcessMapper.map_to_agentic_process(response_data)

        return result

    def create_task(
            self,
            project_id: str,
            task: Task,
            automatic_publish: bool = False
    ) -> Union[Task, ErrorListResponse]:
        '''
        Creates a new task in the specified project.

        :param project_id: str - Unique identifier of the project where the task will be created.
        :param task: Task - The task configuration to create, including name (required), description,
            title_template, id, prompt_data, and artifact_types. Optional fields are included if set.
        :param automatic_publish: bool - Whether to publish the task after creation. Defaults to False.
        :return: Union[Task, ErrorListResponse] - The created task if successful, or an error response.
        '''
        response_data = self.__process_client.create_task(
            project_id=project_id,
            name=task.name,
            description=task.description,
            title_template=task.title_template,
            id=task.id,
            prompt_data=task.prompt_data.to_dict() if task.prompt_data else None,
            artifact_types=task.artifact_types.to_dict() if task.artifact_types else None,
            automatic_publish=automatic_publish
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = TaskMapper.map_to_task(response_data)

        return result

    def get_task(
            self,
            project_id: str,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None
    ) -> Union[Task, ErrorListResponse]:
        '''
        Retrieves details of a specific task in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param task_id: Optional[str] - Unique identifier of the task to retrieve. Defaults to None.
        :param task_name: Optional[str] - Name of the task to retrieve. Defaults to None.
        :return: Union[Task, ErrorListResponse] - The retrieved task if successful, or an error response.
        :raises ValueError: If neither task_id nor task_name is provided.
        '''
        if not (task_id or task_name):
            raise ValueError("Either task_id or task_name must be provided.")

        response_data = self.__process_client.get_task(
            project_id=project_id,
            task_id=task_id,
            task_name=task_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = TaskMapper.map_to_task(response_data)

        return result

    def list_tasks(
            self,
            project_id: str,
            filter_settings: Optional[FilterSettings] = None
    ) -> Union[TaskList, ErrorListResponse]:
        '''
        Retrieves a list of tasks in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param filter_settings: Optional[FilterSettings] - Settings to filter the task list (id, start, count, allow_drafts).
        :return: Union[TaskList, ErrorListResponse] - The list of tasks if successful, or an error response.
        '''
        filter_settings = filter_settings or FilterSettings(start="0", count="100", allow_drafts=True)
        response_data = self.__process_client.list_tasks(
            project_id=project_id,
            id=filter_settings.id,
            start=filter_settings.start,
            count=filter_settings.count,
            allow_drafts=filter_settings.allow_drafts
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = TaskMapper.map_to_task_list(response_data)

        return result

    def update_task(
            self,
            project_id: str,
            task: Task,
            automatic_publish: bool = False,
            upsert: bool = False
    ) -> Union[Task, ErrorListResponse]:
        '''
        Updates an existing task in the specified project or upserts it if specified.

        :param project_id: str - Unique identifier of the project where the task resides.
        :param task: Task - The task configuration to update, including id (required), name, description,
            title_template, prompt_data, and artifact_types. Optional fields are included if set.
        :param automatic_publish: bool - Whether to publish the task after updating. Defaults to False.
        :param upsert: bool - Whether to insert the task if it does not exist. Defaults to False.
        :return: Union[Task, ErrorListResponse] - The updated task if successful, or an error response.
        :raises ValueError: If task.id is not provided.
        '''
        if not task.id:
            raise ValueError("Task ID must be provided for update.")

        response_data = self.__process_client.update_task(
            project_id=project_id,
            task_id=task.id,
            name=task.name,
            description=task.description,
            title_template=task.title_template,
            id=task.id,
            prompt_data=task.prompt_data.to_dict() if task.prompt_data else None,
            artifact_types=task.artifact_types.to_dict() if task.artifact_types else None,
            automatic_publish=automatic_publish,
            upsert=upsert
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = TaskMapper.map_to_task(response_data)

        return result

    def delete_task(
            self,
            project_id: str,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Deletes a specific task in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param task_id: Optional[str] - Unique identifier of the task to delete. Defaults to None.
        :param task_name: Optional[str] - Name of the task to delete. Defaults to None.
        :return: Union[EmptyResponse, ErrorListResponse] - Empty response if successful, or an error response.
        :raises ValueError: If neither task_id nor task_name is provided.
        '''
        if not (task_id or task_name):
            raise ValueError("Either task_id or task_name must be provided.")

        response_data = self.__process_client.delete_task(
            project_id=project_id,
            task_id=task_id,
            task_name=task_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ResponseMapper.map_to_empty_response(response_data or "Task deleted successfully")

        return result

    def publish_task_revision(
            self,
            project_id: str,
            task_id: Optional[str] = None,
            task_name: Optional[str] = None,
            revision: str = None
    ) -> Union[Task, ErrorListResponse]:
        '''
        Publishes a specific revision of a task in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param task_id: Optional[str] - Unique identifier of the task to publish. Defaults to None.
        :param task_name: Optional[str] - Name of the task to publish. Defaults to None.
        :param revision: str - Revision of the task to publish. Defaults to None.
        :return: Union[Task, ErrorListResponse] - The published task if successful, or an error response.
        :raises ValueError: If neither task_id nor task_name is provided, or if revision is not specified.
        '''
        if not (task_id or task_name) or not revision:
            raise ValueError("Either task_id or task_name and revision must be provided.")

        response_data = self.__process_client.publish_task_revision(
            project_id=project_id,
            task_id=task_id,
            task_name=task_name,
            revision=revision
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = TaskMapper.map_to_task(response_data)

        return result

    def start_instance(
            self,
            project_id: str,
            process_name: str,
            subject: Optional[str] = None,
            variables: Optional[List[Variable] | VariableList] = None
    ) -> Union[ProcessInstance, ErrorListResponse]:
        '''
        Starts a new process instance in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param process_name: str - Name of the process to start an instance for.
        :param subject: Optional[str] - Subject of the process instance. Defaults to None.
        :param variables: Optional[List[dict]] - List of variables for the instance. Defaults to None.
        :return: Union[StartInstanceResponse, ErrorListResponse] - The started instance if successful, or an error response.
        '''
        if not isinstance(variables, VariableList):
            variables = VariableList(variables=variables)

        response_data = self.__process_client.start_instance(
            project_id=project_id,
            process_name=process_name,
            subject=subject,
            variables=variables.to_dict()
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ProcessInstanceMapper.map_to_process_instance(response_data)

        return result

    def abort_instance(
            self,
            project_id: str,
            instance_id: str
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Aborts a specific process instance in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param instance_id: str - Unique identifier of the instance to abort.
        :return: Union[EmptyResponse, ErrorListResponse] - Empty response if successful, or an error response.
        :raises ValueError: If instance_id is not provided.
        '''
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        response_data = self.__process_client.abort_instance(
            project_id=project_id,
            instance_id=instance_id
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ResponseMapper.map_to_empty_response(response_data or "Instance aborted successfully")

        return result

    def get_instance(
            self,
            project_id: str,
            instance_id: str
    ) -> Union[ProcessInstance, ErrorListResponse]:
        '''
        Retrieves details of a specific process instance in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param instance_id: str - Unique identifier of the instance to retrieve.
        :return: Union[ProcessInstance, ErrorListResponse] - The retrieved instance if successful, or an error response.
        :raises ValueError: If instance_id is not provided.
        '''
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        response_data = self.__process_client.get_instance(
            project_id=project_id,
            instance_id=instance_id
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ProcessInstanceMapper.map_to_process_instance(response_data)

        return result

    def get_instance_history(
            self,
            project_id: str,
            instance_id: str
    ) -> Union[dict, ErrorListResponse]:
        '''
        Retrieves the history of a specific process instance in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param instance_id: str - Unique identifier of the instance to retrieve history for.
        :return: Union[dict, ErrorListResponse] - The instance history if successful, or an error response.
        :raises ValueError: If instance_id is not provided.
        '''
        if not instance_id:
            raise ValueError("Instance ID must be provided.")

        response_data = self.__process_client.get_instance_history(
            project_id=project_id,
            instance_id=instance_id
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = response_data

        return result

    def get_thread_information(
            self,
            project_id: str,
            thread_id: str
    ) -> Union[dict, ErrorListResponse]:
        '''
        Retrieves information about a specific thread in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param thread_id: str - Unique identifier of the thread to retrieve information for.
        :return: Union[dict, ErrorListResponse] - The thread information if successful, or an error response.
        :raises ValueError: If thread_id is not provided.
        '''
        if not thread_id:
            raise ValueError("Thread ID must be provided.")

        response_data = self.__process_client.get_thread_information(
            project_id=project_id,
            thread_id=thread_id
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = response_data

        return result

    def send_user_signal(
            self,
            project_id: str,
            instance_id: str,
            signal_name: str
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Sends a user signal to a specific process instance in the specified project.

        :param project_id: str - Unique identifier of the project.
        :param instance_id: str - Unique identifier of the instance to send the signal to.
        :param signal_name: str - Name of the user signal to send.
        :return: Union[EmptyResponse, ErrorListResponse] - Empty response if successful, or an error response.
        :raises ValueError: If instance_id or signal_name is not provided.
        '''
        if not instance_id or not signal_name:
            raise ValueError("Instance ID and signal name must be provided.")

        response_data = self.__process_client.send_user_signal(
            project_id=project_id,
            instance_id=instance_id,
            signal_name=signal_name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = ResponseMapper.map_to_empty_response(response_data or "Signal sent successfully")

        return result

    def create_knowledge_base(
            self,
            project_id: str,
            knowledge_base: KnowledgeBase,
    ) -> Union[KnowledgeBase, ErrorListResponse]:
        '''
        Creates a new knowledge base in the specified project using the provided configuration.

        This method sends a request to the process client to create a knowledge base based on
        the attributes of the provided `KnowledgeBase` object. If the response contains errors, it
        maps them to an `ErrorListResponse`. Otherwise, it maps the response to a `KnowledgeBase` object.

        :param project_id: str - Unique identifier of the project where the knowledge base will be created.
        :param knowledge_base: KnowledgeBase - The knowledge base configuration object containing name
            and artifact type names.
        :return: Union[KnowledgeBase, ErrorListResponse] - A `KnowledgeBase` object representing the created
            knowledge base if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__process_client.create_kb(
            project_id=project_id,
            name=knowledge_base.name,
            artifacts=knowledge_base.artifacts if knowledge_base.artifacts else None,
            metadata=knowledge_base.metadata if knowledge_base.metadata else None
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = KnowledgeBaseMapper.map_to_knowledge_base(response_data)

        return result

    def list_knowledge_bases(
            self,
            project_id: str,
            name: Optional[str] = None,
            start: Optional[int] = 0,
            count: Optional[int] = 10
    ) -> Union[KnowledgeBaseList, ErrorListResponse]:
        '''
        Retrieves a list of knowledge bases for the specified project.

        This method queries the process client to fetch a list of knowledge bases associated
        with the specified project ID, applying optional filters for name and pagination. If the
        response contains errors, it maps them to an `ErrorListResponse`. Otherwise, it maps the
        response to a `KnowledgeBaseList`.

        :param project_id: str - Unique identifier of the project to retrieve knowledge bases for.
        :param name: Optional[str] - Name filter to narrow down the list of knowledge bases.
        :param start: Optional[int] - Starting index for pagination, defaults to 0.
        :param count: Optional[int] - Number of knowledge bases to return, defaults to 10.
        :return: Union[KnowledgeBaseList, ErrorListResponse] - A `KnowledgeBaseList` containing the
            retrieved knowledge bases if successful, or an `ErrorListResponse` if the API returns errors.
        '''
        response_data = self.__process_client.list_kbs(
            project_id=project_id,
            name=name,
            start=start,
            count=count
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = KnowledgeBaseMapper.map_to_knowledge_base_list(response_data)

        return result

    def get_knowledge_base(
            self,
            project_id: str,
            kb_name: Optional[str] = None,
            kb_id: Optional[str] = None
    ) -> Union[KnowledgeBase, ErrorListResponse]:
        '''
        Retrieves details of a specific knowledge base from the specified project.

        This method sends a request to the process client to retrieve a knowledge base
        identified by either `kb_name` or `kb_id`. If the response contains errors, it maps them to
        an `ErrorListResponse`. Otherwise, it maps the response to a `KnowledgeBase` object.

        :param project_id: str - Unique identifier of the project where the knowledge base resides.
        :param kb_name: Optional[str] - Name of the knowledge base to retrieve.
        :param kb_id: Optional[str] - Unique identifier of the knowledge base to retrieve.
        :return: Union[KnowledgeBase, ErrorListResponse] - A `KnowledgeBase` object representing the
            retrieved knowledge base if successful, or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither `kb_name` nor `kb_id` is provided.
        '''
        if not (kb_name or kb_id):
            raise ValueError("Either kb_name or kb_id must be provided.")

        response_data = self.__process_client.get_kb(
            project_id=project_id,
            kb_name=kb_name,
            kb_id=kb_id
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = KnowledgeBaseMapper.map_to_knowledge_base(response_data)

        return result

    def delete_knowledge_base(
            self,
            project_id: str,
            kb_name: Optional[str] = None,
            kb_id: Optional[str] = None
    ) -> Union[EmptyResponse, ErrorListResponse]:
        '''
        Deletes a specific knowledge base from the specified project.

        This method sends a request to the process client to delete a knowledge base
        identified by either `kb_name` or `kb_id`. Returns an `EmptyResponse` if the deletion is
        successful, or an `ErrorListResponse` if the API returns errors.

        :param project_id: str - Unique identifier of the project where the knowledge base resides.
        :param kb_name: Optional[str] - Name of the knowledge base to delete.
        :param kb_id: Optional[str] - Unique identifier of the knowledge base to delete.
        :return: Union[EmptyResponse, ErrorListResponse] - `EmptyResponse` if the knowledge base was
            deleted successfully, or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If neither `kb_name` nor `kb_id` is provided.
        '''
        if not (kb_name or kb_id):
            raise ValueError("Either kb_name or kb_id must be provided.")

        response_data = self.__process_client.delete_kb(
            project_id=project_id,
            kb_name=kb_name,
            kb_id=kb_id
        )
        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            response_data = response_data if response_data else "Knowledge base deleted successfully"
            result = ResponseMapper.map_to_empty_response(response_data)

        return result

    def list_jobs(
            self,
            project_id: str,
            filter_settings: Optional[FilterSettings] = None,
            topic: Optional[str] = None,
            token: Optional[str] = None
    ) -> Union[JobList, ErrorListResponse]:
        '''
        Retrieves a list of jobs in the specified project.

        This method queries the process client to fetch a list of jobs associated with the specified
        project ID, applying optional filter settings. If the response contains errors,
        it maps them to an `ErrorListResponse`. Otherwise, it maps the response to a `JobList`.

        :param project_id: str - Unique identifier of the project.
        :param filter_settings: Optional[FilterSettings] - Settings to filter the job list (start, count).
        :param topic: Optional[str] - Topic to filter the jobs (e.g., 'Default', 'Event'). Defaults to None.
        :param token: Optional[str] - Unique token identifier to filter a specific job. Defaults to None.
        :return: Union[JobList, ErrorListResponse] - A `JobList` containing the retrieved jobs if successful,
            or an `ErrorListResponse` if the API returns errors.
        :raises ValueError: If project_id is not provided.
        '''
        if not project_id:
            raise ValueError("Project ID must be provided.")

        filter_settings = filter_settings or FilterSettings(start="0", count="100")
        response_data = self.__process_client.list_jobs(
            project_id=project_id,
            start=filter_settings.start,
            count=filter_settings.count,
            topic=topic,
            token=token,
            name=filter_settings.name
        )

        if ErrorHandler.has_errors(response_data):
            result = ErrorHandler.extract_error(response_data)
        else:
            result = JobMapper.map_to_job_list(response_data)

        return result

For any other question regarding the command line interface or the debugger, refer the user to the PyGEAI CLI Expert, another
Agent specialized in answering those types of questions.

"""

agent_id = "1765d89b-6111-4780-8ef6-662b108cb96c"

agent = Agent(
    id=agent_id,
    status="active",
    name="PyGEAI LAB Expert",
    access_scope="public",
    public_name="com.globant.geai.pygeai_lab_expert",
    job_description="Assists with PyGEAI LAB queries",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851447_logo_512x512.png",
    description="Expert agent for the Globant Enterprise AI Lab, providing guidance on using the PyGEAI SDK to manage agents, tools, reasoning strategies, processes, tasks, and runtime instances.",
    is_draft=False,
    is_readonly=False,
    revision=1,
    version=None,
    agent_data=AgentData(
        prompt=Prompt(
            instructions=f"""\
You are an expert assistant for the Globant Enterprise AI Lab, designed to answer queries about using the PyGEAI SDK. Use the GEAI CLI documentation as your knowledge base to provide accurate, clear, and concise responses in plain text. Tailor the response tone based on the 'style' input (formal or informal). If the query is unclear, ask for clarification. Provide examples where relevant. If an error code is mentioned, explain its meaning and suggest solutions.
IMPORTANT: Answers should be short, clear, and concise.

The documentation is provided below for reference:

{GEAI_LAB_HELP}

Respond with a detailed answer to the query and a brief summary. Ensure responses are accurate and aligned with the documentation.
            """,
            inputs=["query", "style"],
            outputs=[
                PromptOutput(key="response", description="Answer to the user's query about PyGEAI SDK usage, in plain text."),
            ],
            examples=[
                PromptExample(
                    input_data="How do I create a new agent using PyGEAI SDK? [formal]",
                    output="Use the AILabManager's `create_agent` method, specifying the project ID and an Agent object with attributes like name, prompts, and LLM configurations. Example: `manager.create_agent(project_id='proj123', agent=Agent(id=str(uuid.uuid4()), name='MyAgent', agent_data=AgentData(prompt=Prompt(instructions='...'))))`."
                ),
                PromptExample(
                    input_data="What does error code 403 mean in PyGEAI? [informal]",
                    output="Error 403 means 'Forbidden'. It usually pops up when you don't have permission for that action. Check your API key's access scope with `geai configure --key <your_key>` or verify your role in the project with `geai organization list-members`."
                ),
                PromptExample(
                    input_data="How to list all tools in a project? [formal]",
                    output="To list all tools in a project, use the AILabManager's `list_tools` method: `manager.list_tools(project_id='proj123')`. Alternatively, use the CLI command: `geai organization list-tools --organization-id org123 --project-id proj123`. Ensure your API key is configured with `geai configure`."
                ),
                PromptExample(
                    input_data="How do I start a process instance? [formal]",
                    output="Use the AILabManager's `start_instance` method, specifying the process ID and project ID. Example: `manager.start_instance(project_id='proj123', process_id='proc456')`. Alternatively, use the CLI: `geai process start-instance --project-id proj123 --process-id proc456`."
                )
            ]
        ),
        llm_config=LlmConfig(
            max_tokens=5000,
            timeout=0,
            sampling=Sampling(temperature=0.7, top_k=0, top_p=0)
        ),
        models=[Model(name="openai/gpt-4.1")]
    )
)

manager = AILabManager()
result = manager.update_agent(
    project_id="2ca6883f-6778-40bb-bcc1-85451fb11107",
    agent=agent,
    automatic_publish=False
)

if isinstance(result, Agent):
    print(f"Agent created successfully: {agent.to_dict()}")
else:
    print("Errors:", result.errors)