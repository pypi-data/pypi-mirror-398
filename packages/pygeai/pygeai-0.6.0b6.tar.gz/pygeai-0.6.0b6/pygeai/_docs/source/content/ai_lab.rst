The Lab
=======

The Globant Enterprise AI Lab is a comprehensive framework designed to create, manage, and orchestrate autonomous AI agents capable of addressing complex tasks with minimal human intervention. It provides a structured environment for defining agents, their associated tools, reasoning strategies, and workflows, all integrated within a cohesive ecosystem. The PyGEAI SDK serves as the primary interface for developers to interact with the Lab, offering a Python-native experience through the `lab` module, which enables seamless management of the Lab’s resources and operations.

Overview
--------

The Globant Enterprise AI Lab enables the creation of intelligent AI agents, from collaborative co-pilots to fully
autonomous systems, capable of executing intricate tasks. Its modular design ensures flexibility, allowing developers
to define agent behaviors, orchestrate collaborative workflows, and manage knowledge artifacts. The PyGEAI SDK
streamlines these processes by providing an intuitive, Python-centric interface that abstracts the Lab’s underlying
APIs, making it accessible to developers familiar with Python conventions.

The Lab’s core modules are:

- **Agents & Tools Repository**: A centralized hub for defining and managing agents and their resources, such as skills, tools, and external API integrations.
- **Agentic Flows**: A system for creating workflows that combine tasks, agents, and knowledge artifacts to achieve broader objectives.
- **Knowledge Base**: A repository for storing and organizing artifacts (e.g., documents, data outputs) that agents consume or produce during workflows.
- **Agent Runtime**: The execution environment where agents perform tasks, interact with artifacts, and respond to events within defined workflows.


Interacting with the Lab via PyGEAI SDK
--------------------------------------

The PyGEAI SDK’s `lab` module provides a streamlined interface for developers to engage with the Globant Enterprise AI Lab. Designed to align with Python conventions, it offers a command-line tool that facilitates interaction with the Lab’s resources, including agents, tools, reasoning strategies, processes, tasks, and runtime instances. The `lab` module supports a range of operations, ensuring developers can efficiently manage the Lab’s ecosystem.

### Managing Agents

The `lab` module enables developers to define and manage AI agents within the Lab. Agents are entities configured with specific prompts, language models, and operational parameters to perform designated tasks. Through the `lab` module, developers can create agents with custom attributes, update their configurations, retrieve details, list available agents, publish revisions, share agents via links, or remove them as needed. This functionality allows for precise control over agent lifecycle and behavior within the Lab’s environment.

### Configuring Tools

Tools extend agent capabilities by providing access to external APIs, built-in functions, or custom logic. The `lab` module supports the creation and management of tools, allowing developers to define tools with specific scopes (e.g., API-based or external), configure their parameters, and control their accessibility. Developers can list tools, retrieve tool details, update configurations, publish revisions, set parameters, or delete tools, ensuring tools are seamlessly integrated into the Lab’s workflows.

### Defining Reasoning Strategies

Reasoning strategies guide how agents process information and make decisions. The `lab` module allows developers to create and manage these strategies, specifying system prompts and access scopes to tailor agent reasoning. Developers can list available strategies, retrieve details, update configurations, and ensure strategies align with project requirements, enhancing agent performance within the Lab.

### Orchestrating Processes

Processes in the Lab define workflows that combine agents, tasks, and knowledge artifacts to achieve complex objectives. The `lab` module facilitates process management by enabling developers to create processes, define their structure (including activities, signals, and sequence flows), and update configurations. Developers can list processes, retrieve details, publish revisions, or delete processes, providing full control over workflow orchestration within the Lab.

### Managing Tasks

Tasks are individual units of work within processes, assigned to agents for execution. The `lab` module supports task creation, allowing developers to specify task prompts, artifact types, and descriptions. Developers can list tasks, retrieve task details, update configurations, publish revisions, or delete tasks, ensuring tasks are effectively integrated into the Lab’s workflows.

### Controlling Runtime Instances

The Lab’s runtime environment executes processes, where agents perform tasks and interact with artifacts. The `lab` module provides commands to manage runtime instances, enabling developers to start process instances, monitor their progress, retrieve instance details, access execution history, send signals to influence workflow, or abort instances as needed. This ensures dynamic control over the Lab’s operational execution.

### Running Agents with the Runner

The `Runner` class in the `lab` module provides a direct interface for executing agent tasks asynchronously within the Lab’s runtime environment. It allows developers to run agents with flexible input formats—strings, `ChatMessage`, or `ChatMessageList`—and customizable LLM settings, enabling tailored interactions for testing or production use. The `Runner` simplifies agent execution by handling message processing and LLM configuration, returning a `ProviderResponse` object containing the agent’s response and metadata.

SDK Tools and Utilities
-----------------------

The PyGEAI SDK provides robust programmatic interfaces for interacting with the Globant Enterprise AI Lab, enabling developers to manage agents, tools, reasoning strategies, processes, tasks, and runtime instances directly within Python applications. Beyond the command-line interface, the SDK offers a high-level manager and low-level client classes, designed to integrate seamlessly into development workflows with structured, object-oriented access or flexible JSON-based interactions.

High-Level Interface: AILabManager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The AILabManager class serves as the primary high-level interface, offering a Pythonic, object-oriented approach to managing the Lab’s resources. It abstracts the underlying API complexity, mapping responses to structured Python objects such as Agent, Tool, ReasoningStrategy, AgenticProcess, Task, and ProcessInstance. This allows developers to work with strongly typed models, ensuring clarity and reducing errors when creating, updating, retrieving, or deleting Lab entities.

- Agent Management: Create, update, retrieve, list, publish, share, or delete agents using methods like create_agent, update_agent, get_agent, and delete_agent. Agents are represented as Agent objects, encapsulating properties like name, prompts, and LLM configurations.
- Tool Management: Define and manage tools with methods such as create_tool, update_tool, get_tool, list_tools, publish_tool_revision, and delete_tool. Tools are modeled as Tool objects, supporting API-based or custom configurations with parameters (ToolParameter).
- Reasoning Strategies: Configure agent reasoning with create_reasoning_strategy, update_reasoning_strategy, get_reasoning_strategy, and list_reasoning_strategies. Strategies are represented as ReasoningStrategy objects, defining system prompts and access scopes.
- Process Orchestration: Manage workflows through create_process, update_process, get_process, list_processes, publish_process_revision, and delete_process. Processes are encapsulated as AgenticProcess objects, detailing activities, signals, and sequence flows.
- Task Management: Create and manage tasks with create_task, update_task, get_task, list_tasks, publish_task_revision, and delete_task. Tasks are modeled as Task objects, specifying prompts and artifact types.
- Runtime Control: Start, monitor, and control process instances using start_instance, get_instance, list_process_instances, get_instance_history, send_user_signal, and abort_instance. Instances are represented as ProcessInstance objects, with execution details and thread information accessible via get_thread_information.

The AILabManager is initialized with an API key, base URL, and optional alias, providing a unified entry point for all Lab operations. Its methods handle error mapping (ErrorListResponse) and response validation, making it ideal for rapid development and integration into larger applications.

Low-Level Interface: Client Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For developers requiring fine-grained control or preferring to work directly with JSON responses, the SDK includes low-level client classes: AgentClient, ToolClient, ReasoningStrategyClient, and AgenticProcessClient. These clients interact with the Lab’s APIs without mapping responses to Python objects, returning raw JSON or text for maximum flexibility.

- AgentClient: Supports operations like create_agent, update_agent, get_agent, list_agents, publish_agent_revision, create_sharing_link, and delete_agent. It handles agent-specific API endpoints, passing parameters like project ID, agent name, prompts, and LLM configurations as dictionaries.
- ToolClient: Provides methods such as create_tool, update_tool, get_tool, list_tools, publish_tool_revision, get_parameter, set_parameter, and delete_tool. It manages tool configurations, including OpenAPI specifications and parameter lists, with validation for scopes and access levels.
- ReasoningStrategyClient: Includes create_reasoning_strategy, update_reasoning_strategy, get_reasoning_strategy, and list_reasoning_strategies, allowing direct manipulation of strategy definitions like system prompts and localized descriptions.
- AgenticProcessClient: Offers comprehensive process and task management with methods like create_process, update_process, get_process, list_processes, publish_process_revision, delete_process, create_task, update_task, get_task, list_tasks, publish_task_revision, delete_task, start_instance, get_instance, list_process_instances, get_instance_history, get_thread_information, send_user_signal, and abort_instance. It handles complex process structures and runtime operations in JSON format.

Each client is initialized with an API key and base URL, using a BaseClient for HTTP requests. They provide direct access to the Lab’s endpoints, enabling custom parsing or integration with external systems where object mapping is unnecessary.

Integration and Flexibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Both the AILabManager and client classes are installable via pip install pygeai and support cross-platform development. The high-level AILabManager is suited for structured applications requiring type safety and ease of use, while the low-level clients cater to scenarios demanding raw API responses or custom workflows. Developers can combine these interfaces within the same project, leveraging AILabManager for rapid prototyping and clients for specialized tasks.


PyGEAI SDK - Lab components
---------------------------

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    ai_lab/models
    ai_lab/runner
    ai_lab/usage
    ai_lab/cli
    ai_lab/spec

