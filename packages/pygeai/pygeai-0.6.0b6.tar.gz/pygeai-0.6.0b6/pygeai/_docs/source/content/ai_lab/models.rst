Data Models
===========

The PyGEAI SDK provides Pydantic-based data models for interacting with the Globant Enterprise AI Lab, enabling developers to configure agents, tools, processes, tasks, and more. These models ensure type safety and API compatibility without requiring hardcoded field details that may change. Many models allow direct dictionary inputs for nested configurations, simplifying instantiation. This section describes each model’s purpose, provides examples of instantiation (via attributes and dictionaries), and notes key restrictions, keeping documentation maintainable and flexible.

.. note::
   Models inherit from ``CustomBaseModel``, a Pydantic ``BaseModel`` subclass, providing ``to_dict()`` for serialization.

FilterSettings
--------------

Purpose
~~~~~~~

Configures filters for querying Lab entities like agents or tools, supporting pagination and scope.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import FilterSettings

   filters = FilterSettings(id="agent-123", name="MyAgent", access_scope="private")
   print(filters.to_dict())
   # Output: Dictionary with filter settings

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import FilterSettings

   filters = FilterSettings(**{
       "id": "agent-123",
       "name": "MyAgent",
       "accessScope": "private"
   })
   print(filters.to_dict())
   # Output: Dictionary with filter settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Most fields are optional for flexible queries.
- Pagination requires non-negative integers.
- Scope values must match API expectations (e.g., "public", "private").
- Use dictionaries for quick filter setup in API calls.
- Avoid over-specifying to ensure results.

Sampling
--------

Purpose
~~~~~~~

Controls randomness in LLM token generation.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Sampling

   sampling = Sampling(temperature=0.8, top_k=40, top_p=0.95)
   print(sampling.to_dict())
   # Output: {"temperature": 0.8, "topK": 40, "topP": 0.95}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import Sampling

   sampling = Sampling(**{
       "temperature": 0.8,
       "topK": 40,
       "topP": 0.95
   })
   print(sampling.to_dict())
   # Output: {"temperature": 0.8, "topK": 40, "topP": 0.95}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- All fields are required.
- Temperature should range from 0.1 to 2.0.
- Top-k and top-p need positive, reasonable values.
- Dictionaries simplify sampling configuration.
- Test settings to balance creativity and coherence.

LlmConfig
---------

Purpose
~~~~~~~

Defines LLM settings, including token limits and sampling.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import LlmConfig, Sampling

   sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
   llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
   print(llm_config.to_dict())
   # Output: Dictionary with LLM settings

**Via Dictionary (with Sampling as dict)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Core fields are mandatory.
- Token limits depend on LLM capacity.
- Timeout may be API-capped; use 0 carefully.
- Accepts sampling as a dictionary for convenience.
- Verify settings before scaling.

Model
-----

Purpose
~~~~~~~

Customizes an LLM for an agent.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Model, LlmConfig, Sampling

   sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
   llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
   model = Model(name="gpt-4", llm_config=llm_config)
   print(model.to_dict())
   # Output: Dictionary with model settings

**Via Dictionary (with LlmConfig as dict)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name is required; must be Lab-supported.
- Optional LLM config can be a dictionary.
- Prompt, if used, should align with agent tasks.
- Useful for flexible model assignments.
- Check LLM compatibility.

PromptExample
-------------

Purpose
~~~~~~~

Provides input-output pairs for few-shot learning.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import PromptExample

   example = PromptExample(input_data="Summarize: [article]", output='{"summary": "AI news."}')
   print(example.to_dict())
   # Output: Dictionary with example data

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import PromptExample

   example = PromptExample(**{
       "inputData": "Summarize: [article]",
       "output": '{"summary": "AI news."}'
   })
   print(example.to_dict())
   # Output: Dictionary with example data

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required; output must be JSON.
- Keep examples concise and relevant.
- Multiple examples improve accuracy.
- Dictionaries simplify example setup.
- Monitor token usage with examples.

PromptOutput
------------

Purpose
~~~~~~~

Defines expected prompt outputs.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import PromptOutput

   output = PromptOutput(key="summary", description="Text summary.")
   print(output.to_dict())
   # Output: {"key": "summary", "description": "Text summary."}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import PromptOutput

   output = PromptOutput(**{
       "key": "summary",
       "description": "Text summary."
   })
   print(output.to_dict())
   # Output: {"key": "summary", "description": "Text summary."}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Key and description are required.
- Keys must be unique per prompt.
- Use clear descriptions for output format.
- Dictionaries streamline output definitions.
- Supports multiple outputs.

Prompt
------

Purpose
~~~~~~~

Configures an agent’s prompt behavior.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Prompt, PromptOutput, PromptExample

   output = PromptOutput(key="summary", description="Text summary.")
   example = PromptExample(input_data="Article: [content]", output='{"summary": "AI news."}')
   prompt = Prompt(instructions="Summarize article.", inputs=["article"], outputs=[output], examples=[example])
   print(prompt.to_dict())
   # Output: Dictionary with prompt settings

**Via Dictionary (with Outputs, Examples as dicts)**:

.. code-block:: python

   from pygeai.lab.models import Prompt

   prompt = Prompt(**{
       "instructions": "Summarize article.",
       "inputs": ["article"],
       "outputs": [{"key": "summary", "description": "Text summary."}],
       "examples": [{"inputData": "Article: [content]", "output": '{"summary": "AI news."}'}]
   })
   print(prompt.to_dict())
   # Output: Dictionary with prompt settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Instructions, inputs, and outputs are required.
- Outputs need at least one entry.
- Accepts outputs and examples as dictionaries.
- Inputs must be unique.
- Avoid unimplemented fields like context.

ModelList
---------

Purpose
~~~~~~~

Holds multiple model configurations.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ModelList, Model

   model = Model(name="gpt-4")
   model_list = ModelList(models=[model])
   print(model_list.to_dict())
   # Output: List of model dictionaries

**Via Dictionary (with Models as dicts)**:

.. code-block:: python

   from pygeai.lab.models import ModelList

   model_list = ModelList(**{
       "models": [
           {"name": "gpt-4"},
           {"name": "gpt-3.5"}
       ]
   })
   print(model_list.to_dict())
   # Output: List of model dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Models collection is required; can be empty.
- Accepts models as dictionaries.
- Supports iteration and appending.
- Ensure unique model names.
- Simplifies bulk model setup.

AgentData
---------

Purpose
~~~~~~~

Defines an agent’s core configuration.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import AgentData, Prompt, PromptOutput, LlmConfig, Sampling, ModelList, Model

   prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
   sampling = Sampling(temperature=0.7, top_k=50, top_p=0.9)
   llm_config = LlmConfig(max_tokens=2048, timeout=30, sampling=sampling)
   model_list = ModelList(models=[Model(name="gpt-4")])
   agent_data = AgentData(prompt=prompt, llm_config=llm_config, models=model_list)
   print(agent_data.to_dict())
   # Output: Dictionary with agent data

**Via Dictionary (with Prompt, LlmConfig, Models as dicts)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Core components are required.
- Accepts prompt, LLM config, and models as dictionaries.
- Non-draft agents need at least one model.
- Align settings with LLM capabilities.
- Simplifies complex agent setups.

Agent
-----

Purpose
~~~~~~~

Represents a complete agent with metadata.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Agent, AgentData, Prompt, PromptOutput, ModelList, Model

   prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
   model_list = ModelList(models=[Model(name="gpt-4")])
   agent_data = AgentData(prompt=prompt, llm_config=LlmConfig(max_tokens=2048, timeout=30, sampling=Sampling(temperature=0.7, top_k=50, top_p=0.9)), models=model_list)
   agent = Agent(name="SummaryAgent", access_scope="public", public_name="summary-agent", agent_data=agent_data)
   print(agent.to_dict())
   # Output: Dictionary with agent settings

**Via Dictionary (with AgentData as dict)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name is required; avoid special characters.
- Accepts `agent_data` as a dictionary.
- Public agents need valid public names.
- Non-draft agents require full configuration.
- API sets identifiers automatically.

AgentList
---------

Purpose
~~~~~~~

Manages multiple agents, typically from API responses.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import AgentList, Agent

   agent = Agent(name="Agent1", access_scope="private")
   agent_list = AgentList(agents=[agent])
   print(agent_list.to_dict())
   # Output: List of agent dictionaries

**Via Dictionary (with Agents as dicts)**:

.. code-block:: python

   from pygeai.lab.models import AgentList

   agent_list = AgentList(**{
       "agents": [
           {"name": "Agent1", "accessScope": "private"},
           {"name": "Agent2", "accessScope": "public", "publicName": "agent-two"}
       ]
   })
   print(agent_list.to_dict())
   # Output: List of agent dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Agents collection is required; can be empty.
- Accepts agents as dictionaries.
- Supports iteration and appending.
- Useful for bulk agent management.

SharingLink
-----------

Purpose
~~~~~~~

Enables agent sharing via links.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import SharingLink

   link = SharingLink(agent_id="agent-123", api_token="xyz-token", shared_link="https://lab.globant.ai/share/agent-123")
   print(link.to_dict())
   # Output: Dictionary with link details

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import SharingLink

   link = SharingLink(**{
       "agentId": "agent-123",
       "apiToken": "xyz-token",
       "sharedLink": "https://lab.globant.ai/share/agent-123"
   })
   print(link.to_dict())
   # Output: Dictionary with link details

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- All fields are required, set by API.
- Links must be valid URLs.
- Secure tokens to prevent leaks.
- Dictionaries simplify link creation.

ToolParameter
-------------

Purpose
~~~~~~~

Defines tool parameters.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ToolParameter

   param = ToolParameter(key="api_key", data_type="String", description="API key.", is_required=True)
   print(param.to_dict())
   # Output: Dictionary with parameter details

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import ToolParameter

   param = ToolParameter(**{
       "key": "api_key",
       "dataType": "String",
       "description": "API key.",
       "isRequired": True
   })
   print(param.to_dict())
   # Output: Dictionary with parameter details

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Core fields are mandatory.
- Data types must match API expectations.
- Keys must be unique per tool.
- Dictionaries streamline parameter setup.

ToolMessage
-----------

Purpose
~~~~~~~

Provides tool feedback messages.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ToolMessage

   message = ToolMessage(description="Invalid key.", type="error")
   print(message.to_dict())
   # Output: {"description": "Invalid key.", "type": "error"}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import ToolMessage

   message = ToolMessage(**{
       "description": "Invalid key.",
       "type": "error"
   })
   print(message.to_dict())
   # Output: {"description": "Invalid key.", "type": "error"}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required.
- Types are typically "warning" or "error."
- Keep messages concise.
- Dictionaries simplify message creation.

Tool
----

Purpose
~~~~~~~

Configures tools for agents.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Tool, ToolParameter

   param = ToolParameter(key="api_key", data_type="String", description="API key.", is_required=True)
   tool = Tool(name="WeatherTool", description="Fetches weather.", scope="api", parameters=[param])
   print(tool.to_dict())
   # Output: Dictionary with tool settings

**Via Dictionary (with Parameters as dicts)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name and description are required.
- Accepts parameters as dictionaries.
- API tools need valid OpenAPI specs.
- Public tools require valid public names.
- Ensure unique parameter keys.

ToolList
--------

Purpose
~~~~~~~

Manages multiple tools.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ToolList, Tool

   tool = Tool(name="Tool1", description="Tool one.", scope="builtin")
   tool_list = ToolList(tools=[tool])
   print(tool_list.to_dict())
   # Output: Dictionary with tool list

**Via Dictionary (with Tools as dicts)**:

.. code-block:: python

   from pygeai.lab.models import ToolList

   tool_list = ToolList(**{
       "tools": [
           {"name": "Tool1", "description": "Tool one.", "scope": "builtin"}
       ]
   })
   print(tool_list.to_dict())
   # Output: Dictionary with tool list

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Tools collection is required; can be empty.
- Accepts tools as dictionaries.
- Supports iteration and appending.
- Simplifies bulk tool handling.

LocalizedDescription
--------------------

Purpose
~~~~~~~

Provides multilingual strategy descriptions.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import LocalizedDescription

   desc = LocalizedDescription(language="english", description="Creative strategy.")
   print(desc.to_dict())
   # Output: {"language": "english", "description": "Creative strategy."}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import LocalizedDescription

   desc = LocalizedDescription(**{
       "language": "english",
       "description": "Creative strategy."
   })
   print(desc.to_dict())
   # Output: {"language": "english", "description": "Creative strategy."}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required.
- Use standard language names.
- Dictionaries simplify descriptions.
- Supports multiple languages.

ReasoningStrategy
-----------------

Purpose
~~~~~~~

Guides agent reasoning behavior.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ReasoningStrategy, LocalizedDescription

   desc = LocalizedDescription(language="english", description="Creative strategy.")
   strategy = ReasoningStrategy(name="CreativeStrategy", access_scope="public", type="addendum", localized_descriptions=[desc])
   print(strategy.to_dict())
   # Output: Dictionary with strategy settings

**Via Dictionary (with Descriptions as dicts)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name, scope, and type are required.
- Accepts descriptions as dictionaries.
- Scope and type depend on Lab values.
- API sets identifiers.

ReasoningStrategyList
---------------------

Purpose
~~~~~~~

Manages multiple reasoning strategies.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ReasoningStrategyList, ReasoningStrategy

   strategy = ReasoningStrategy(name="Strategy1", access_scope="private", type="addendum")
   strategy_list = ReasoningStrategyList(strategies=[strategy])
   print(strategy_list.to_dict())
   # Output: List of strategy dictionaries

**Via Dictionary (with Strategies as dicts)**:

.. code-block:: python

   from pygeai.lab.models import ReasoningStrategyList

   strategy_list = ReasoningStrategyList(**{
       "strategies": [
           {"name": "Strategy1", "accessScope": "private", "type": "addendum"}
       ]
   })
   print(strategy_list.to_dict())
   # Output: List of strategy dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Strategies collection is required; can be empty.
- Accepts strategies as dictionaries.
- Supports iteration and appending.

KnowledgeBase
-------------

Purpose
~~~~~~~

Manages process artifacts.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import KnowledgeBase

   kb = KnowledgeBase(name="DocsKB", artifact_type_name=["document"])
   print(kb.to_dict())
   # Output: Dictionary with knowledge base settings

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import KnowledgeBase

   kb = KnowledgeBase(**{
       "name": "DocsKB",
       "artifactTypeName": ["document"]
   })
   print(kb.to_dict())
   # Output: Dictionary with knowledge base settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name and artifact types are required.
- Dictionaries simplify setup.
- API sets identifiers.
- Ensure valid artifact types.

AgenticActivity
---------------

Purpose
~~~~~~~

Links tasks and agents in processes.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import AgenticActivity

   activity = AgenticActivity(key="act1", name="Summarize", task_name="SummaryTask", agent_name="SummaryAgent", agent_revision_id=1)
   print(activity.to_dict())
   # Output: Dictionary with activity settings

**Via Dictionary**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Core fields are required.
- Keys must be unique.
- Dictionaries streamline activity setup.
- Reference existing tasks and agents.

ArtifactSignal
--------------

Purpose
~~~~~~~

Triggers process actions via artifacts.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ArtifactSignal

   signal = ArtifactSignal(key="sig1", name="DocSignal", handling_type="C", artifact_type_name=["document"])
   print(signal.to_dict())
   # Output: Dictionary with signal settings

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import ArtifactSignal

   signal = ArtifactSignal(**{
       "key": "sig1",
       "name": "DocSignal",
       "handlingType": "C",
       "artifactTypeName": ["document"]
   })
   print(signal.to_dict())
   # Output: Dictionary with signal settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- All fields are required.
- Keys must be unique.
- Dictionaries simplify signal setup.
- Handling types depend on Lab engine.

UserSignal
----------

Purpose
~~~~~~~

Enables user-driven process signals.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import UserSignal

   signal = UserSignal(key="user1", name="UserInput")
   print(signal.to_dict())
   # Output: {"key": "user1", "name": "UserInput"}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import UserSignal

   signal = UserSignal(**{
       "key": "user1",
       "name": "UserInput"
   })
   print(signal.to_dict())
   # Output: {"key": "user1", "name": "UserInput"}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required.
- Keys must be unique.
- Dictionaries simplify setup.
- Use descriptive names.

Event
-----

Purpose
~~~~~~~

Marks process start or end points.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Event

   event = Event(key="start1", name="ProcessStart")
   print(event.to_dict())
   # Output: {"key": "start1", "name": "ProcessStart"}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import Event

   event = Event(**{
       "key": "start1",
       "name": "ProcessStart"
   })
   print(event.to_dict())
   # Output: {"key": "start1", "name": "ProcessStart"}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required.
- Keys must be unique.
- Dictionaries simplify event setup.
- Ensure flow connectivity.

SequenceFlow
------------

Purpose
~~~~~~~

Connects process elements.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import SequenceFlow

   flow = SequenceFlow(key="flow1", source_key="start1", target_key="act1")
   print(flow.to_dict())
   # Output: Dictionary with flow settings

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import SequenceFlow

   flow = SequenceFlow(**{
       "key": "flow1",
       "sourceKey": "start1",
       "targetKey": "act1"
   })
   print(flow.to_dict())
   # Output: Dictionary with flow settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- All fields are required.
- Keys must be unique.
- Dictionaries simplify flow setup.
- Reference valid elements.

Variable
--------

Purpose
~~~~~~~

Stores dynamic process data.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Variable

   var = Variable(key="input_text", value="Sample text")
   print(var.to_dict())
   # Output: {"key": "input_text", "value": "Sample text"}

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import Variable

   var = Variable(**{
       "key": "input_text",
       "value": "Sample text"
   })
   print(var.to_dict())
   # Output: {"key": "input_text", "value": "Sample text"}

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Both fields are required.
- Keys should be unique.
- Dictionaries simplify variable setup.
- Values must be strings.

VariableList
------------

Purpose
~~~~~~~

Manages process variables.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import VariableList, Variable

   var = Variable(key="input_text", value="Sample text")
   var_list = VariableList(variables=[var])
   print(var_list.to_dict())
   # Output: List of variable dictionaries

**Via Dictionary (with Variables as dicts)**:

.. code-block:: python

   from pygeai.lab.models import VariableList

   var_list = VariableList(**{
       "variables": [
           {"key": "input_text", "value": "Sample text"}
       ]
   })
   print(var_list.to_dict())
   # Output: List of variable dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Variables collection is optional; defaults to empty.
- Accepts variables as dictionaries.
- Supports iteration and appending.

AgenticProcess
--------------

Purpose
~~~~~~~

Orchestrates process workflows.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import AgenticProcess, AgenticActivity, Event, SequenceFlow

   activity = AgenticActivity(key="act1", name="Summarize", task_name="SummaryTask", agent_name="SummaryAgent", agent_revision_id=1)
   start_event = Event(key="start1", name="Start")
   flow = SequenceFlow(key="flow1", source_key="start1", target_key="act1")
   process = AgenticProcess(name="SummaryProcess", agentic_activities=[activity], start_event=start_event, sequence_flows=[flow])
   print(process.to_dict())
   # Output: Dictionary with process settings

**Via Dictionary (with Activities, Event, Flows as dicts)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name is required; avoid special characters.
- Accepts activities, events, and flows as dictionaries.
- Flows must reference valid keys.
- API sets identifiers.
- Ensure valid process structure.

ArtifactType
------------

Purpose
~~~~~~~

Defines task artifacts.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ArtifactType

   artifact = ArtifactType(name="document", usage_type="input")
   print(artifact.to_dict())
   # Output: Dictionary with artifact settings

**Via Dictionary**:

.. code-block:: python

   from pygeai.lab.models import ArtifactType

   artifact = ArtifactType(**{
       "name": "document",
       "usageType": "input"
   })
   print(artifact.to_dict())
   # Output: Dictionary with artifact settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name and usage type are required.
- Usage type is "input" or "output."
- Dictionaries simplify artifact setup.
- Variable keys have length limits.

ArtifactTypeList
----------------

Purpose
~~~~~~~

Manages task artifact types.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ArtifactTypeList, ArtifactType

   artifact = ArtifactType(name="document", usage_type="input")
   artifact_list = ArtifactTypeList(artifact_types=[artifact])
   print(artifact_list.to_dict())
   # Output: List of artifact dictionaries

**Via Dictionary (with ArtifactTypes as dicts)**:

.. code-block:: python

   from pygeai.lab.models import ArtifactTypeList

   artifact_list = ArtifactTypeList(**{
       "artifact_types": [
           {"name": "document", "usageType": "input"}
       ]
   })
   print(artifact_list.to_dict())
   # Output: List of artifact dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Artifact types collection is optional; defaults to empty.
- Accepts artifact types as dictionaries.
- Supports iteration and appending.

Task
----

Purpose
~~~~~~~

Configures agent tasks.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import Task, Prompt, PromptOutput, ArtifactTypeList, ArtifactType

   prompt = Prompt(instructions="Summarize.", inputs=["text"], outputs=[PromptOutput(key="summary", description="Summary.")])
   artifact = ArtifactType(name="document", usage_type="input")
   task = Task(name="SummaryTask", prompt_data=prompt, artifact_types=ArtifactTypeList(artifact_types=[artifact]))
   print(task.to_dict())
   # Output: Dictionary with task settings

**Via Dictionary (with Prompt, ArtifactTypes as dicts)**:

.. code-block:: python

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

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Name is required; avoid special characters.
- Accepts prompt and artifact types as dictionaries.
- Artifact types must use valid usage types.
- Prompt is optional but recommended.

AgenticProcessList
------------------

Purpose
~~~~~~~

Manages multiple processes.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import AgenticProcessList, AgenticProcess

   process = AgenticProcess(name="Process1")
   process_list = AgenticProcessList(processes=[process])
   print(process_list.to_dict())
   # Output: Dictionary with process list

**Via Dictionary (with Processes as dicts)**:

.. code-block:: python

   from pygeai.lab.models import AgenticProcessList

   process_list = AgenticProcessList(**{
       "processes": [
           {"name": "Process1"}
       ]
   })
   print(process_list.to_dict())
   # Output: Dictionary with process list

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Processes collection is required; can be empty.
- Accepts processes as dictionaries.
- Supports iteration and appending.

TaskList
--------

Purpose
~~~~~~~

Manages multiple tasks.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import TaskList, Task

   task = Task(name="Task1")
   task_list = TaskList(tasks=[task])
   print(task_list.to_dict())
   # Output: List of task dictionaries

**Via Dictionary (with Tasks as dicts)**:

.. code-block:: python

   from pygeai.lab.models import TaskList

   task_list = TaskList(**{
       "tasks": [
           {"name": "Task1"}
       ]
   })
   print(task_list.to_dict())
   # Output: List of task dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Tasks collection is required; can be empty.
- Accepts tasks as dictionaries.
- Supports iteration and appending.

ProcessInstance
---------------

Purpose
~~~~~~~

Tracks running process instances.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ProcessInstance, AgenticProcess

   process = AgenticProcess(name="SummaryProcess")
   instance = ProcessInstance(process=process, subject="Summary")
   print(instance.to_dict())
   # Output: Dictionary with instance settings

**Via Dictionary (with Process as dict)**:

.. code-block:: python

   from pygeai.lab.models import ProcessInstance

   instance = ProcessInstance(**{
       "process": {"name": "SummaryProcess"},
       "subject": "Summary"
   })
   print(instance.to_dict())
   # Output: Dictionary with instance settings

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Process and subject are required.
- Accepts process as a dictionary.
- API sets identifiers.
- Align variables with process needs.

ProcessInstanceList
-------------------

Purpose
~~~~~~~

Manages multiple process instances.

Usage Examples
~~~~~~~~~~~~~~

**Via Attributes**:

.. code-block:: python

   from pygeai.lab.models import ProcessInstanceList, ProcessInstance, AgenticProcess

   process = AgenticProcess(name="Process1")
   instance = ProcessInstance(process=process, subject="Instance1")
   instance_list = ProcessInstanceList(instances=[instance])
   print(instance_list.to_dict())
   # Output: List of instance dictionaries

**Via Dictionary (with Instances as dicts)**:

.. code-block:: python

   from pygeai.lab.models import ProcessInstanceList

   instance_list = ProcessInstanceList(**{
       "instances": [
           {"process": {"name": "Process1"}, "subject": "Instance1"}
       ]
   })
   print(instance_list.to_dict())
   # Output: List of instance dictionaries

Restrictions and Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Instances collection is required; can be empty.
- Accepts instances as dictionaries.
- Supports iteration and appending.
