GEAI CLI - AI Lab - Spec Command Documentation
==============================================

Name
----

geai - Command Line Interface for Globant Enterprise AI

Synopsis
--------

.. code-block:: bash

   geai spec <subcommand> --[flag] [flag.arg]

Description
-----------

The ``geai spec`` command is a utility within the Globant Enterprise AI (GEAI) CLI, designed to load components (agents, tools, tasks, and agentic processes) into the AI Lab from JSON specification files. It supports the following subcommands:

- ``help`` (or ``h``): Displays help text for the ``geai spec`` command.
- ``load-agent`` (or ``la``): Loads agent(s) from a JSON specification file.
- ``load-tool`` (or ``lt``): Loads tool(s) from a JSON specification file.
- ``load-task`` (or ``ltask``): Loads task(s) from a JSON specification file.
- ``load-agentic-process`` (or ``lap``): Loads agentic process(es) from a JSON specification file.

Each subcommand accepts specific options to configure the loading process, such as project ID (specified as a UUID), file path, and publication settings.

Subcommands and Options
----------------------

The following subcommands are available under ``geai spec``:

help
~~~~

- **Aliases**: ``help``, ``h``
- **Description**: Displays help text describing the ``geai spec`` command and its subcommands.
- **Options**: None
- **Usage**:

  .. code-block:: bash

     geai spec help

load-agent
~~~~~~~~~~

- **Aliases**: ``load-agent``, ``la``
- **Description**: Loads one or more agent specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.
- **Options**:

  +-------------------------+---------------------------+-------------------------------------------------------------+----------+
  | Option                  | Aliases                   | Description                                                 | Required |
  +=========================+===========================+=============================================================+==========+
  | project_id              | --project-id, --pid       | UUID of the project where the agent will be loaded          | Yes      |
  +-------------------------+---------------------------+-------------------------------------------------------------+----------+
  | file                    | --file, -f                | Path to the JSON file containing the agent definition        | Yes      |
  +-------------------------+---------------------------+-------------------------------------------------------------+----------+
  | automatic_publish       | --automatic-publish, --ap | Define if the agent is published (1) or created as draft (0) | Yes      |
  +-------------------------+---------------------------+-------------------------------------------------------------+----------+

- **Usage**:

  .. code-block:: bash

     geai spec load-agent --project-id 123e4567-e89b-12d3-a456-426614174000 --file agent.json --automatic-publish 0

load-tool
~~~~~~~~~

- **Aliases**: ``load-tool``, ``lt``
- **Description**: Loads one or more tool specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.
- **Options**:

  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | Option                  | Aliases                   | Description                                               | Required |
  +=========================+===========================+===========================================================+==========+
  | project_id              | --project-id, --pid       | UUID of the project where the tool will be loaded         | Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | file                    | --file, -f                | Path to the JSON file containing the tool definition       | Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | automatic_publish       | --automatic-publish, --ap | Define if the tool is published (1) or created as draft (0)| Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+

- **Usage**:

  .. code-block:: bash

     geai spec load-tool --pid 987fcdeb-1a2b-3c4d-5e6f-7890abcd1234 -f tool.json --ap 1

load-task
~~~~~~~~~

- **Aliases**: ``load-task``, ``ltask``
- **Description**: Loads one or more task specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.
- **Options**:

  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | Option                  | Aliases                   | Description                                               | Required |
  +=========================+===========================+===========================================================+==========+
  | project_id              | --project-id, --pid       | UUID of the project where the task will be loaded         | Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | file                    | --file, -f                | Path to the JSON file containing the task definition       | Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+
  | automatic_publish       | --automatic-publish, --ap | Define if the task is published (1) or created as draft (0)| Yes      |
  +-------------------------+---------------------------+-----------------------------------------------------------+----------+

- **Usage**:

  .. code-block:: bash

     geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 -f task.json --ap 0

load-agentic-process
~~~~~~~~~~~~~~~~~~~~

- **Aliases**: ``load-agentic-process``, ``lap``
- **Description**: Loads one or more agentic process specifications from a JSON file into the AI Lab for a specified project, identified by a UUID.
- **Options**:

  +-------------------------+---------------------------+---------------------------------------------------------------------+----------+
  | Option                  | Aliases                   | Description                                                         | Required |
  +=========================+===========================+=====================================================================+==========+
  | project_id              | --project-id, --pid       | UUID of the project where the agentic process will be loaded        | Yes      |
  +-------------------------+---------------------------+---------------------------------------------------------------------+----------+
  | file                    | --file, -f                | Path to the JSON file containing the agentic process definition      | Yes      |
  +-------------------------+---------------------------+---------------------------------------------------------------------+----------+
  | automatic_publish       | --automatic-publish, --ap | Define if the agentic process is published (1) or created as draft (0)| Yes      |
  +-------------------------+---------------------------+---------------------------------------------------------------------+----------+

- **Usage**:

  .. code-block:: bash

     geai spec load-agentic-process --project-id 789a0bcd-2e3f-5c4d-6e7f-9012cdef3456 -f process.json --ap 1

Usage Examples
--------------

Below are example commands demonstrating the usage of ``geai spec`` subcommands, using UUIDs for project IDs.

**Example 1: Display Help**

Display the help text for the ``geai spec`` command.

.. code-block:: bash

   geai spec help

*Output* (example):

.. code-block:: text

   geai spec - Command Line Interface for Globant Enterprise AI
   Usage: geai spec <subcommand> --[flag] [flag.arg]
   Subcommands:
     help, h                    Display help text
     load-agent, la             Load agent from JSON specification
     load-tool, lt              Load tool from JSON specification
     load-task, ltask           Load task from JSON specification
     load-agentic-process, lap  Load agentic process from JSON specification
   ...

**Example 2: Load a Single Agent**

Load an agent from a JSON file into project with UUID ``123e4567-e89b-12d3-a456-426614174000`` as a draft.

.. code-block:: bash

   geai spec load-agent --project-id 123e4567-e89b-12d3-a456-426614174000 --file agent.json --automatic-publish 0

*Output* (example):

.. code-block:: text

   Created agent detail:
   <agent details>

**Example 3: Load and Publish a Tool**

Load a tool from a JSON file into project with UUID ``987fcdeb-1a2b-3c4d-5e6f-7890abcd1234`` and publish it.

.. code-block:: bash

   geai spec load-tool --pid 987fcdeb-1a2b-3c4d-5e6f-7890abcd1234 -f tool.json --ap 1

*Output* (example):

.. code-block:: text

   Created tool detail:
   <tool details>

**Example 4: Load a Task**

Load a task from a JSON file into project with UUID ``456e7890-f1a2-4b3c-5d6e-8901bcde2345`` as a draft.

.. code-block:: bash

   geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 -f task.json --ap 0

*Output* (example):

.. code-block:: text

   Created task detail:
   <task details>

**Example 5: Load and Publish an Agentic Process**

Load an agentic process from a JSON file into project with UUID ``789a0bcd-2e3f-5c4d-6e7f-9012cdef3456`` and publish it.

.. code-block:: bash

   geai spec load-agentic-process --project-id 789a0bcd-2e3f-5c4d-6e7f-9012cdef3456 -f process.json --ap 1

*Output* (example):

.. code-block:: text

   Created agentic process detail:
   <process details>

**Example 6: Missing File Path (Error Case)**

Attempt to load a task without specifying the file path.

.. code-block:: bash

   geai spec load-task --pid 456e7890-f1a2-4b3c-5d6e-8901bcde2345 --ap 0

*Output*:

.. code-block:: text

   Error: Cannot load task definition without specifying path to JSON file.

JSON Specification Formats
-------------------------

The ``load-agent``, ``load-tool``, ``load-task``, and ``load-agentic-process`` subcommands expect JSON files containing agent, tool, task, or agentic process specifications, respectively. The JSON file can contain a single specification (object) or multiple specifications (array).

**Agent Specification Example**

Below is an example of a single agent specification for a "Public Translator V2x" agent.

.. code-block:: json

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

**Tool Specification Example**

Below is an example of a single tool specification for a "Weather Forecaster" tool.

.. code-block:: json

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

**Task Specification Example**

Below is an example of a single task specification for an "Email Review v1" task.

.. code-block:: json

   {
     "name": "Email Review v1",
     "description": "A simple task to review and categorize email content, requiring no tools or prompts.",
     "titleTemplate": "Email Review Task"
   }

**Agentic Process Specification Example**

Below is an example of a single agentic process specification for a "Content Moderation Process."

.. code-block:: json

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

Error Handling
--------------

The ``geai spec`` subcommands may raise the following errors:

- **MissingRequirementException**:
  - Triggered if required options (``--project-id`` or ``--file``) are not provided.
  - Example: ``Cannot load task definition without specifying path to JSON file.``
- **File Loading Errors**:
  - Invalid or inaccessible JSON files will cause errors during loading, logged and displayed to stderr.
- **Parsing Errors**:
  - Malformed JSON specifications may fail during parsing, with errors output to stderr.

Notes
-----

- The ``project_id`` must be a valid UUID (e.g., ``123e4567-e89b-12d3-a456-426614174000``).
- JSON files must conform to the expected format for agents, tools, tasks, or agentic processes, as shown in the examples above.
- The ``automatic_publish`` option (0 or 1) determines whether the component is created as a draft or published immediately.
- Ensure the project UUID exists in the AI Lab and the JSON file path is valid before running the command.
- Multiple components can be loaded from a single JSON file if it contains an array of specifications.