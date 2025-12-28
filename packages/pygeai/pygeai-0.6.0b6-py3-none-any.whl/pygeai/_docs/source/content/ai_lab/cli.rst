Working with the GEAI Lab using the CLI
======================================

The `geai ai-lab` command-line interface (CLI) allows users to interact with the Globant Enterprise AI (GEAI) Lab to manage agents, tools, reasoning strategies, processes, tasks, and process instances. This guide provides step-by-step instructions for performing common operations using CLI commands.

.. contents:: Table of Contents
   :depth: 3
   :local:

Prerequisites
-------------

- **CLI Installation**: Ensure the `geai` CLI is installed. Contact your GEAI administrator for installation instructions.
- **Authentication**: Obtain your project ID and API token from the GEAI platform.
- **Environment**: A terminal with access to the `geai` command, typically on Linux, macOS, or Windows (via WSL or similar).

Set the project ID as an environment variable for convenience:

.. code-block:: bash

   export PROJECT_ID="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

Managing Agents
---------------

Agents are AI entities that perform tasks based on prompts and LLM configurations.

### List Agents

Retrieve a list of agents with filtering options.

.. code-block:: bash

   geai ai-lab list-agents \
     --project-id "$PROJECT_ID" \
     --status "active" \
     --access-scope "public" \
     --allow-drafts 0 \
     --allow-external 1

**Example Output**:

.. code-block:: text

   - Name: Public Translator V2, ID: 11111111-1111-1111-1111-111111111111, Status: active
   - Name: Jarvis, ID: 22222222-2222-2222-2222-222222222222, Status: active

### Create a Public Agent

Create a public agent with detailed configurations.

.. code-block:: bash

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

.. code-block:: bash

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

.. code-block:: bash

   geai ai-lab get-agent \
     --project-id "$PROJECT_ID" \
     --agent-id "11111111-1111-1111-1111-111111111111"

**Example Output**:

.. code-block:: text

   Name: Public Translator V2
   ID: 11111111-1111-1111-1111-111111111111
   Description: Agent that translates from any language to English.
   Access Scope: public

### Update an Agent

Update an existing agent's properties.

.. code-block:: bash

   geai ai-lab update-agent \
     --project-id "$PROJECT_ID" \
     --agent-id "33333333-3333-3333-3333-333333333333" \
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

.. code-block:: bash

   geai ai-lab create-sharing-link \
     --project-id "$PROJECT_ID" \
     --agent-id "44444444-4444-4444-4444-444444444444"

**Example Output**:

.. code-block:: text

   Shared Link: https://geai.example.com/share/44444444-4444-4444-4444-444444444444

### Delete an Agent

Remove an agent from the project.

.. code-block:: bash

   geai ai-lab delete-agent \
     --project-id "$PROJECT_ID" \
     --agent-id "55555555-5555-5555-5555-555555555555"

Managing Tools
--------------

Tools extend agent capabilities with external APIs or built-in functions.

### List Tools

Retrieve a list of tools with filtering options.

.. code-block:: bash

   geai ai-lab list-tools \
     --project-id "$PROJECT_ID" \
     --access-scope "public" \
     --scope "api" \
     --count "100" \
     --allow-drafts 1 \
     --allow-external 1

**Example Output**:

.. code-block:: text

   - Name: gdrive_create_docs_post, ID: 66666666-6666-6666-6666-666666666666
   - Name: create_image_post, ID: 77777777-7777-7777-7777-777777777777

### Create a Tool

Create a built-in tool with parameters.

.. code-block:: bash

   geai ai-lab create-tool \
     --project-id "$PROJECT_ID" \
     --name "sample tool V3" \
     --description "A builtin tool that does something but really does nothing." \
     --scope "builtin" \
     --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs.", "isRequired": true}' \
     --parameter '{"key": "some_nonsensitive_id", "dataType": "String", "description": "Configuration that is static.", "isRequired": true, "type": "config", "fromSecret": false, "value": "example-fake-config-value-12345"}' \
     --parameter '{"key": "api_token", "dataType": "String", "description": "Configuration that is sensitive.", "isRequired": true, "type": "config", "fromSecret": true, "value": "example-fake-secret-token-xxxxx"}' \
     --automatic-publish 0

### Get Tool Information

Retrieve details for a specific tool.

.. code-block:: bash

   geai ai-lab get-tool \
     --project-id "$PROJECT_ID" \
     --tool-id "66666666-6666-6666-6666-666666666666"

**Example Output**:

.. code-block:: text

   Name: gdrive_create_docs_post
   ID: 66666666-6666-6666-6666-666666666666
   Description: Create a new Google Docs document.

### Update a Tool

Update an API-based tool with OpenAPI specification.

.. code-block:: bash

   geai ai-lab update-tool \
     --project-id "$PROJECT_ID" \
     --tool-id "66666666-6666-6666-6666-666666666666" \
     --name "saia_models_get" \
     --description "Get all LLM models" \
     --scope "api" \
     --parameter '{"key": "Authorization", "dataType": "String", "description": "token with which you are going to connect to SAIA", "isRequired": true, "type": "config", "fromSecret": false, "value": "Bearer example_fake_token_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}' \
     --open-api-json '{"openapi": "3.0.0", "info": {"title": "LLM Providers API", "version": "2.0.0", "description": "API to retrieve information about models provided by OpenAI."}, "servers": [{"url": "https://api.beta.saia.ai", "description": "Production Server"}], "paths": {"/v2/llm/providers/openai/models": {"get": {"summary": "Retrieve models from OpenAI", "operationId": "saia_models", "description": "Fetches a list of available models along with their properties and configurations.", "responses": {"200": {"description": "Successful response with a list of models.", "content": {"application/json": {"schema": {"type": "object", "properties": {"models": {"type": "array", "items": {"type": "object", "properties": {"contextWindow": {"type": "integer", "description": "Maximum context window size for the model."}, "fullName": {"type": "string", "description": "Full name of the model."}, "id": {"type": "string", "format": "uuid", "description": "Unique identifier of the model."}, "isCustom": {"type": "boolean", "description": "Indicates whether the model is custom."}, "maxOutputTokens": {"type": "integer", "description": "Maximum number of output tokens the model can generate."}, "name": {"type": "string", "description": "Name of the model."}, "priority": {"type": "integer", "description": "Priority level of the model."}, "properties": {"type": "array", "items": {"type": "object", "properties": {"id": {"type": "string", "format": "uuid", "description": "Unique identifier for the property."}, "name": {"type": "string", "description": "Name of the property."}, "type": {"type": "string", "description": "Data type of the property (e.g., Boolean, String)."}, "value": {"type": "string", "description": "Value of the property."}}}}}, "type": {"type": "string", "description": "Type of the model (e.g., Chat)."}}}}}}}}}, "security": [{"bearerAuth": []}]}}}}' \
     --automatic-publish 1

### Publish a Tool Revision

Publish a specific revision of a tool.

.. code-block:: bash

   geai ai-lab publish-tool-revision \
     --project-id "$PROJECT_ID" \
     --tool-id "88888888-8888-8888-8888-888888888888" \
     --revision "2"

### Get Tool Parameters

Retrieve parameters for a tool.

.. code-block:: bash

   geai ai-lab get-parameter \
     --project-id "$PROJECT_ID" \
     --tool-public-name "sample_tool_V3" \
     --revision "0" \
     --version "0" \
     --allow-drafts 1

**Example Output**:

.. code-block:: text

   - Key: input, Description: some input that the tool needs HERE., Required: true
   - Key: api_token, Description: API token for authentication, Required: true

### Set Tool Parameters

Update parameters for a tool.

.. code-block:: bash

   geai ai-lab set-parameter \
     --project-id "$PROJECT_ID" \
     --tool-public-name "sample_tool_V3" \
     --parameter '{"key": "input", "dataType": "String", "description": "some input that the tool needs HERE.", "isRequired": true}' \
     --parameter '{"key": "api_token", "dataType": "String", "description": "API token for authentication", "isRequired": true, "type": "config", "fromSecret": true, "value": "example-fake-secret-token-xxxxx"}'

### Delete a Tool

Remove a tool from the project.

.. code-block:: bash

   geai ai-lab delete-tool \
     --project-id "$PROJECT_ID" \
     --tool-id "88888888-8888-8888-8888-888888888888"

Managing Reasoning Strategies
----------------------------

Reasoning strategies define how agents process information.

### List Reasoning Strategies

Retrieve a list of reasoning strategies.

.. code-block:: bash

   geai ai-lab list-reasoning-strategies \
     --start "0" \
     --count "50" \
     --allow-external 1 \
     --access-scope "public"

**Example Output**:

.. code-block:: text

   - Name: RSName2, Access Scope: public
   - Name: test1, Access Scope: public

### Create a Reasoning Strategy

Create a reasoning strategy with localized descriptions.

.. code-block:: bash

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

.. code-block:: bash

   geai ai-lab update-reasoning-strategy \
     --project-id "$PROJECT_ID" \
     --reasoning-strategy-id "aaaabbbb-cccc-dddd-eeee-ffffffffffff" \
     --name "test1" \
     --system-prompt "Let's think step by step." \
     --access-scope "private" \
     --type "addendum" \
     --automatic-publish 0 \
     --upsert 1

### Get a Reasoning Strategy

Retrieve details for a specific reasoning strategy.

.. code-block:: bash

   geai ai-lab get-reasoning-strategy \
     --project-id "$PROJECT_ID" \
     --reasoning-strategy-name "test1"

**Example Output**:

.. code-block:: text

   Name: test1
   System Prompt: Let's think step by step.
   Access Scope: private

Managing Processes
------------------

Processes define workflows involving agents, tasks, and events.

### Create a Process

Create a process with agentic activities and signals.

.. code-block:: bash

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

.. code-block:: bash

   geai ai-lab create-task \
     --project-id "$PROJECT_ID" \
     --name "basic-task" \
     --description "Basic task for process" \
     --title-template "Basic Task" \
     --automatic-publish 1

### Update a Process

Update an existing process.

.. code-block:: bash

   geai ai-lab update-process \
     --project-id "$PROJECT_ID" \
     --process-id "bbbbcccc-dddd-eeee-ffff-000000000000" \
     --name "Basic Process V3" \
     --kb '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' \
     --agentic-activity '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' \
     --automatic-publish 0 \
     --upsert 0

### Get a Process

Retrieve process details by ID or name.

.. code-block:: bash

   geai ai-lab get-process \
     --project-id "$PROJECT_ID" \
     --process-id "ccccddd-eeee-ffff-0000-111111111111" \
     --revision "0" \
     --version 0 \
     --allow-drafts 1

**Example Output**:

.. code-block:: text

   Name: Basic Process V4
   ID: ccccddd-eeee-ffff-0000-111111111111
   Description: This is a sample process

### List Processes

Retrieve a list of processes.

.. code-block:: bash

   geai ai-lab list-processes \
     --project-id "$PROJECT_ID" \
     --start "0" \
     --count "100" \
     --allow-draft 1

**Example Output**:

.. code-block:: text

   - Name: Basic Process V4, ID: ccccddd-eeee-ffff-0000-111111111111
   - Name: Basic Process V3, ID: bbbbcccc-dddd-eeee-ffff-000000000000

### Publish a Process Revision

Publish a specific revision of a process.

.. code-block:: bash

   geai ai-lab publish-process-revision \
     --project-id "$PROJECT_ID" \
     --process-id "ddddeeee-ffff-0000-1111-222222222222" \
     --revision "1"

### Delete a Process

Remove a process from the project.

.. code-block:: bash

   geai ai-lab delete-process \
     --project-id "$PROJECT_ID" \
     --process-id "ccccddd-eeee-ffff-0000-111111111111"

Managing Tasks
--------------

Tasks define specific actions within processes.

### Create a Task

Create a task with minimal configuration.

.. code-block:: bash

   geai ai-lab create-task \
     --project-id "$PROJECT_ID" \
     --name "Sample v2" \
     --description "A simple task that requires no tools and defines no prompt" \
     --title-template "Sample Task" \
     --automatic-publish 0

### List Tasks

Retrieve a list of tasks.

.. code-block:: bash

   geai ai-lab list-tasks \
     --project-id "$PROJECT_ID" \
     --start "0" \
     --count "50" \
     --allow-drafts 1

**Example Output**:

.. code-block:: text

   - Name: Sample v2, ID: eeeeffff-0000-1111-2222-333333333333
   - Name: basic-task, ID: <task-id>

### Get a Task

Retrieve details for a specific task.

.. code-block:: bash

   geai ai-lab get-task \
     --project-id "$PROJECT_ID" \
     --task-id "eeeeffff-0000-1111-2222-333333333333"

**Example Output**:

.. code-block:: text

   Name: Sample v2
   ID: eeeeffff-0000-1111-2222-333333333333
   Description: A simple task that requires no tools and defines no prompt

### Update a Task

Update an existing task.

.. code-block:: bash

   geai ai-lab update-task \
     --project-id "$PROJECT_ID" \
     --task-id "eeeeffff-0000-1111-2222-333333333333" \
     --name "Sample v2 Updated" \
     --description "Updated description" \
     --title-template "Updated Sample Task" \
     --automatic-publish 1 \
     --upsert 0

### Publish a Task Revision

Publish a specific revision of a task.

.. code-block:: bash

   geai ai-lab publish-task-revision \
     --project-id "$PROJECT_ID" \
     --task-id "eeeeffff-0000-1111-2222-333333333333" \
     --revision "1"

### Delete a Task

Remove a task from the project.

.. code-block:: bash

   geai ai-lab delete-task \
     --project-id "$PROJECT_ID" \
     --task-id "eeeeffff-0000-1111-2222-333333333333"

Managing Process Instances
-------------------------

Process instances represent running workflows.

### Start a Process Instance

Start a new instance of a process.

.. code-block:: bash

   geai ai-lab start-instance \
     --project-id "$PROJECT_ID" \
     --process-name "Basic Process V2" \
     --subject "should we talk about the weather?" \
     --variables '[{"key": "location", "value": "Paris"}]'

**Example Output**:

.. code-block:: text

   Instance ID: <instance-id>
   Status: active

### List Process Instances

Retrieve a list of process instances.

.. code-block:: bash

   geai ai-lab list-processes-instances \
     --project-id "$PROJECT_ID" \
     --process-id "ccccddd-eeee-ffff-0000-111111111111" \
     --is-active 1 \
     --start "0" \
     --count "10"

**Example Output**:

.. code-block:: text

   - Instance ID: <instance-id>, Status: active, Subject: should we talk about the weather?

### Get a Process Instance

Retrieve details for a specific instance.

.. code-block:: bash

   geai ai-lab get-instance \
     --project-id "$PROJECT_ID" \
     --instance-id "<instance-id>"

**Example Output**:

.. code-block:: text

   Instance ID: <instance-id>
   Process: Basic Process V2
   Subject: should we talk about the weather?

### Get Instance History

Retrieve the history of a process instance.

.. code-block:: bash

   geai ai-lab get-instance-history \
     --project-id "$PROJECT_ID" \
     --instance-id "<instance-id>"

**Example Output**:

.. code-block:: text

   - Event: Started, Timestamp: 2025-04-15T10:00:00Z
   - Event: Artifact Uploaded, Timestamp: 2025-04-15T10:01:00Z

### Send a User Signal

Send a signal to a running process instance.

.. code-block:: bash

   geai ai-lab send-user-signal \
     --project-id "$PROJECT_ID" \
     --instance-id "<instance-id>" \
     --signal-name "approval"

### Abort a Process Instance

Stop a running process instance.

.. code-block:: bash

   geai ai-lab abort-instance \
     --project-id "$PROJECT_ID" \
     --instance-id "<instance-id>"

Complete Example Workflow
------------------------

This example demonstrates creating an agent, a task, a process, and starting an instance.

1. **Create an Agent**:

.. code-block:: bash

   geai ai-lab create-agent \
     --project-id "$PROJECT_ID" \
     --name "sample-translator" \
     --description "Translator agent for processes" \
     --access-scope "public" \
     --automatic-publish 1

2. **Create a Task**:

.. code-block:: bash

   geai ai-lab create-task \
     --project-id "$PROJECT_ID" \
     --name "basic-task" \
     --description "Basic task for process" \
     --title-template "Basic Task" \
     --automatic-publish 1

3. **Create a Process**:

.. code-block:: bash

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

4. **Start a Process Instance**:

.. code-block:: bash

   geai ai-lab start-instance \
     --project-id "$PROJECT_ID" \
     --process-name "Basic Process V4" \
     --subject "should we talk about the weather?" \
     --variables '[{"key": "location", "value": "Paris"}]'
