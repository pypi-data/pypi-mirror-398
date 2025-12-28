The Lab - Usage
===============

The Globant Enterprise AI Lab enables developers to create and manage AI agents, tools, tasks, and processes.
The `AILabManager` class provides a high-level interface for these operations, while low-level clients
(`AgentClient`, `ToolClient`, `AgenticProcessClient`) offer direct API access, and the `geai ai-lab` CLI provides
command-line control. This section documents all Lab operations, grouped by resource type (Agents, Tools, Tasks,
Processes), with examples for command-line, low-level, and high-level usage.

Agents
------

Create Agent
~~~~~~~~~~~~

Creates a new AI agent in a specified project, defining its name, access scope, prompt instructions, LLM settings, and other configurations.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab create-agent \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
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

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.agents.clients import AgentClient

    client = AgentClient()
    response = client.create_agent(
        project_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
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

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        agent=agent,
        automatic_publish=False
    )
    print(created_agent)

Update Agent
~~~~~~~~~~~~

Updates an existing agent’s configuration, such as its name, prompt instructions, or LLM settings.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab update-agent \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --agent-id "agent-123" \
      --name "Public Translator V3" \
      --description "Updated agent for translations." \
      --agent-data-prompt-instructions "the user provides text, translate it to English accurately" \
      --agent-data-llm-temperature 0.7 \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.agents.clients import AgentClient

    client = AgentClient()
    response = client.update_agent(
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

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        agent_id="agent-123",
        agent=agent,
        automatic_publish=False
    )
    print(updated_agent)

List Agents
~~~~~~~~~~~

Retrieves a list of agents in a specified project, with optional filters for status, pagination, scope, and draft inclusion.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab list-agents \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --status "active" \
      --allow-drafts 0 \
      --allow-external 1

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.agents.clients import AgentClient

    client = AgentClient()
    response = client.list_agents(
        status="active",
        allow_drafts=False,
        allow_external=True
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager
    from pygeai.lab.models import FilterSettings

    manager = AILabManager()

    filters = FilterSettings(
        status="active",
        allow_drafts=False,
        allow_external=True
    )
    agent_list = manager.get_agent_list(
        filter_settings=filters
    )
    print(agent_list)

Delete Agent
~~~~~~~~~~~~

Deletes an agent from a specified project by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab delete-agent \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --agent-id "agent-123"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.agents.clients import AgentClient

    client = AgentClient()
    response = client.delete_agent(
        agent_id="agent-123"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.delete_agent(
        agent_id="agent-123"
    )
    print(response)

Publish Agent Revision
~~~~~~~~~~~~~~~~~~~~~~

Publishes a revision of an agent, making it available for use.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab publish-agent-revision \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --agent-id "agent-123"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.agents.clients import AgentClient

    client = AgentClient()
    response = client.publish_agent_revision(
        agent_id="agent-123"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.publish_agent_revision(
        agent_id="agent-123"
    )
    print(response)

Tools
-----

Create Tool
~~~~~~~~~~~

Creates a new tool in a specified project, defining its name, description, scope, and parameters for agent use.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab create-tool \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --name "sample tool V3" \
      --description "a builtin tool that does something but really does nothing cos it does not exist." \
      --scope "builtin" \
      --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": true}' \
      --parameter '{"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.", "isRequired": true, "type": "config", "fromSecret": false, "value": "example-fake-config-value-12345"}' \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.tools.clients import ToolClient

    client = ToolClient()
    response = client.create_tool(
        name="sample tool V3",
        description="a builtin tool that does something but really does nothing cos it does not exist.",
        scope="builtin",
        parameters=[
            {"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": True},
            {"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.", "isRequired": True, "type": "config", "fromSecret": False, "value": "example-fake-config-value-12345"}
        ],
        automatic_publish=False
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
                value="example-fake-config-value-12345"
            )
        ]
    )

    created_tool = manager.create_tool(
        tool=tool,
        automatic_publish=False
    )
    print(created_tool)

Update Tool
~~~~~~~~~~~

Updates an existing tool’s configuration, such as its name, description, or parameters.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab update-tool \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --tool-id "tool-456" \
      --name "sample tool V4" \
      --description "Updated builtin tool." \
      --scope "builtin" \
      --parameter '{"key": "input", "dataType": "String", "description": "updated input.", "isRequired": true}' \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.tools.clients import ToolClient

    client = ToolClient()
    response = client.update_tool(
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

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        tool_id="tool-456",
        tool=tool,
        automatic_publish=False
    )
    print(updated_tool)

Delete Tool
~~~~~~~~~~~

Deletes a tool from a specified project by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab delete-tool \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --tool-id "tool-456"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.tools.clients import ToolClient

    client = ToolClient()
    response = client.delete_tool(
        tool_id="tool-456"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.delete_tool(
        tool_id="tool-456"
    )
    print(response)

Publish Tool Revision
~~~~~~~~~~~~~~~~~~~~~

Publishes a revision of a tool, making it available for use.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab publish-tool-revision \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --tool-id "tool-456"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.tools.clients import ToolClient

    client = ToolClient()
    response = client.publish_tool_revision(
        tool_id="tool-456"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.publish_tool_revision(
        tool_id="tool-456"
    )
    print(response)

Tasks
-----

Create Task
~~~~~~~~~~~

Creates a new task in a specified project, defining its name, description, prompt configuration, and artifact types.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab create-task \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --name "Sample v2" \
      --description "A simple task that requires no tools and define no prompt" \
      --title-template "Sample Task" \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.create_task(
        name="Sample v2",
        description="A simple task that requires no tools and define no prompt",
        title_template="Sample Task",
        prompt_data={},
        artifact_types=[],
        automatic_publish=False
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        task=task,
        automatic_publish=False
    )
    print(created_task)

Update Task
~~~~~~~~~~~

Updates an existing task’s configuration, such as its name, description, or prompt settings.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab update-task \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --task-id "task-789" \
      --name "Sample v3" \
      --description "Updated simple task." \
      --title-template "Updated Sample Task" \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.update_task(
        task_id="task-789",
        name="Sample v3",
        description="Updated simple task.",
        title_template="Updated Sample Task",
        prompt_data={},
        artifact_types=[],
        automatic_publish=False
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        task_id="task-789",
        task=task,
        automatic_publish=False
    )
    print(updated_task)

Delete Task
~~~~~~~~~~~

Deletes a task from a specified project by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab delete-task \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --task-id "task-789"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.delete_task(
        task_id="task-789"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.delete_task(
        task_id="task-789"
    )
    print(response)

Publish Task Revision
~~~~~~~~~~~~~~~~~~~~~

Publishes a revision of a task, making it available for use.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab publish-task-revision \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --task-id "task-789"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.publish_task_revision(
        task_id="task-789"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.publish_task_revision(
        task_id="task-789"
    )
    print(response)

Processes
---------

Create Process
~~~~~~~~~~~~~~

Creates a new agentic process in a specified project, defining its workflow with activities, signals, events, and sequence flows.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab create-process \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
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

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.create_process(
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

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        process=process,
        automatic_publish=False
    )
    print(created_process)

Update Process
~~~~~~~~~~~~~~

Updates an existing process’s configuration, such as its name, description, or workflow components.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab update-process \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --process-id "process-101" \
      --key "product_def" \
      --name "Basic Process V5" \
      --description "Updated sample process" \
      --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
      --automatic-publish 0

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.update_process(
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

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

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
        process_id="process-101",
        process=process,
        automatic_publish=False
    )
    print(updated_process)

Delete Process
~~~~~~~~~~~~~~

Deletes a process from a specified project by its ID.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab delete-process \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --process-id "process-101"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.delete_process(
        process_id="process-101"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.delete_process(
        process_id="process-101"
    )
    print(response)

Publish Process Revision
~~~~~~~~~~~~~~~~~~~~~~~~

Publishes a revision of a process, making it available for use.

Command Line
^^^^^^^^^^^^

.. code-block:: shell

    geai ai-lab publish-process-revision \
      --project-id "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee" \
      --process-id "process-101"

Low-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.processes.clients import AgenticProcessClient

    client = AgenticProcessClient()
    response = client.publish_process_revision(
        process_id="process-101"
    )
    print(response)

High-Level Service Layer
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pygeai.lab.managers import AILabManager

    manager = AILabManager()
    response = manager.publish_process_revision(
        process_id="process-101"
    )
    print(response)
