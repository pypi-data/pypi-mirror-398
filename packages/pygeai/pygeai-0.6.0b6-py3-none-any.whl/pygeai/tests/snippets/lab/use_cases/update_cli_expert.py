from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent, AgentData, Prompt, LlmConfig, Model, Sampling, PromptExample, PromptOutput
import uuid

GEAI_CLI_HELP = """
# PyGEAI - SDK for Globant Enterprise AI

PyGEAI is a Software Development Kit (SDK) for interacting with [Globant Enterprise AI](https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI). It comprises libraries, tools, code samples, and documentation to simplify your experience with the platform.

## Repository

Find the PyGEAI source code and documentation in the following GitHub repository:

[GitHub repository](https://github.com/RT-GEN029-GI/pygeai)

## Configuration

Before using the SDK, you need to define `GEAI_API_KEY` (`$SAIA_APITOKEN`) and `GEAI_API_BASE_URL` (`$BASE_URL`). You can achieve this in three ways:

* **Environment variables:** Set `GEAI_API_KEY` and `GEAI_API_BASE_URL` as environment variables in your operating system.
* **Credentials file:** Create a file named credentials in the `.geai` directory within your user home directory (`$USER_HOME/.geai/credentials`) and define `GEAI_API_KEY` and `GEAI_API_BASE_URL` within this file.
* **Client instantiation:** Specify the `api_key` and `base_url` parameters directly when creating an instance of a client class.

**Note:** If you plan to use the [Evaluation Module](https://wiki.genexus.com/enterprise-ai/wiki?896,Evaluation), you must also define `GEAI_API_EVAL_URL`

## Modules

The SDK consists of several modules, all accessible through a meta-package:

- **`pygeai`**: This meta-package encapsulates all components of the SDK.
- **`pygeai-cli`**: This package provides a command-line tool for interacting with the SDK.
- **`pygeai-chat`**: This package offers facilities to chat with assistants/agents created in Globant Enterprise AI.
- **`pygeai-dbg`**: This package includes a debugger to troubleshoot potential SDK issues and gain detailed insights into its operations.
- **`pygeai-core`**: This package handles interactions with the fundamental components of Globant Enterprise AI, including users, groups, permissions, API keys, organizations, and [Projects](https://wiki.genexus.com/enterprise-ai/wiki?565,Projects).
- **`pygeai-admin`**: This package enables interactions with the Globant Enterprise AI instance.
- **`pygeai-lab`**: This package facilitates interactions with AI LAB.
- **`pygeai-evaluation`**: This package provides functionality from the evaluation module.
- **`pygeai-gam`**: This package allows interaction with [GAM] (https://wiki.genexus.com/commwiki/wiki?24746,Table+of+contents%3AGeneXus+Access+Manager+%28GAM%29,).
- **`pygeai-assistant`**: This package handles interactions with various Assistants, including [Data Analyst Assistants](https://wiki.genexus.com/enterprise-ai/wiki?886,Data+Analyst+Assistant+2.0), [RAG Assistants](https://wiki.genexus.com/enterprise-ai/wiki?44,RAG+Assistants+Introduction), [Chat with Data Assistants](https://wiki.genexus.com/enterprise-ai/wiki?159,Chat+with+Data+Assistant), [Chat with API Assistants](https://wiki.genexus.com/enterprise-ai/wiki?110,API+Assistant), and [Chat Assistants](https://wiki.genexus.com/enterprise-ai/wiki?708,Chat+Assistant).
- **`pygeai-organization`**: This package facilitates interactions with Organizations in Globant Enterprise AI.
- **`pygeai-flows`**: This package enables interactions with [Flows](https://wiki.genexus.com/enterprise-ai/wiki?321,Flows+in+Globant+Enterprise+AI) [in development]. 

## Usage

### Install PyGEAI
Use pip to install the package from PyPI:

```
(venv) ~$ pip install pygeai
```

To install pre-release versions, you can run:
```
(venv) ~$ pip install --pre pygeai
```

### Verify installation
To check the installed PyGEAI version, run:

```
(venv) ~$ geai v
```

### View help

To access the general help menu:

```
(venv) ~$ geai h
```
To view help for a specific command:

```
(venv) ~$ geai <command> h
```

### Debugger

The `pygeai-dbg` package provides a command-line debugger (`geai-dbg`) for troubleshooting and inspecting the `geai` CLI. 
It pauses execution at breakpoints, allowing you to inspect variables, execute Python code, and control program flow interactively.

To debug a `geai` command, replace `geai` with `geai-dbg`. For example:

```bash
(venv) ~$ geai-dbg ail lrs
```

This pauses at the `main` function in `pygeai.cli.geai`, displaying an interactive prompt `(geai-dbg)`. 
You can then use commands like `continue` (resume), `run` (run without pauses), `quit` (exit), or `help` (list commands).


### Man Pages Documentation

The package includes Unix manual pages (man pages) for detailed command-line documentation. 

To install man pages locally:

```bash
geai-install-man
```

To install man pages system-wide:

```bash
sudo geai-install-man --system
```

To access the man pages:

```bash
man geai
```

#### Setting up Man Pages Access

If you're using a virtual environment, you'll need to configure your system to find the man pages. Add the following to your shell configuration file (`.bashrc`, `.zshrc`, etc.):

```bash
# For macOS
if [ -n "$VIRTUAL_ENV" ]; then
    export MANPATH="$VIRTUAL_ENV/share/man:$MANPATH"
fi

# For Linux
if [ -n "$VIRTUAL_ENV" ]; then
    export MANPATH="$VIRTUAL_ENV/man:$MANPATH"
fi
```

After adding this configuration:
1. Reload your shell configuration: `source ~/.bashrc` or `source ~/.zshrc`
2. The man pages will be available when your virtual environment is active

## Bugs and suggestions
To report any bug, request features or make any suggestions, the following email is available:

<geai-sdk@globant.com>

## Authors
Copyright 2025, Globant. All rights reserved

GEAI CLI
--------


SYNOPSIS
    geai <command> [<subcommand>] [--option] [option-arg]

DESCRIPTION
    geai is a cli utility that interacts with the PyGEAI SDK to handle common tasks in Globant Enterprise AI,
    such as creating organizations and projects, defining assistants, managing workflows, etc.

    The available subcommands are as follows:
    help or h			Display help text
    version or v		Display version text
    check-updates or cu		Search for available updates

    configure or config or c		Setup the environment variables required to interact with GEAI
      	--key or -k		Set GEAI API KEY
    	--url or -u		Set GEAI API BASE URL
    	--eval-url or --eu		Set GEAI API EVAL URL for the evaluation module
    	--alias or -a		Set alias for settings section
    	--list or -l		List available alias
    organization or org		Invoke organization endpoints to handle project parameters
    assistant or ast		Invoke assistant endpoints to handle assistant parameters
    rag			Invoke rag assistant endpoints to handle RAG assistant parameters
    chat			Invoke chat endpoints to handle chat with assistants parameters
    admin or adm		Invoke admin endpoints designed for internal use
    llm			Invoke llm endpoints for provider's and model retrieval
    files			Invoke files endpoints for file handling
    usage-limit or ulim		Invoke usage limit endpoints for organization and project
    embeddings or emb		Invoke embeddings endpoints
    feedback or fbk		Invoke feedback endpoints
    rerank or rr		Invoke rerank endpoints
    evaluation or eval		Invoke evaluation endpoints
    gam			Invoke GAM authentication endpoints
    secrets or sec		Handle Globant Enterprise AI secrets
    ai-lab or ail		Invoke AI Lab endpoints
    ai-lab-spec or spec		Invoke AI Lab endpoints
    migrate or mig		Invoke migrate procedures


    You can consult specific options for each command using with:
    geai <command> h
    or
    geai <command> help

ERROR CODES
Certain error descriptions can contain up to %n references specific to that error. 
These references are described with %1, %2,... ,%n.

    ErrorCode     	 Description    
        1       Assistant Not Found 
        2       Provider Type Not Found 
        3       Request Not Found
        5       Api Key Not Found
        6       Api Token Not Found
        7       Api Token Out Of Scope
        10      Query Text Empty
        20      Bad Input Text
        100     Provider Request Timeout 
        150     Provider Unknown Error
        151     Provider Rate Limit
        152     Provider Quota Exceeded
        153     Provider Over Capacity
        154     Quota Exceeded
        401     Unauthorized
        404     Bad Endpoint
        405     Method Not Allowed
        500     Internal Server Error
        1001    Provider Configuration Error  
        1010    RAG Not Found
        1101    Search Index Profile Name Not Found  
        1102    Request Failed
        2000    Invalid ProjectName
        2001    Invalid OrganizationId
        2002    ProjectName %1 Already Exists In The Organization 
        2003    OrganizationName Already Exists
        2004    Organization Not Found
        2005    Project Not Found
        2006    Project Not In Organization
        2007    Name is Empty
        2008    Prompt is Empty
        2009    Invalid Type
        2010    Not Implemented
        2011    Assistant General Error
        2012    Assistant Not Implemented
        2013    Revision Is Empty
        2014    Assistant Revision Not Found
        2015    Assistant Revision Update Error
        2016    AIModel Id For %1 %2
        2017    RAG General Error
        2018    Vector Store Not Found
        2019    Index Profile General Error
        2020    RAG Already Exists
        2021    Document Not Found
        2022    Invalid DocumentId
        2023    Document General Error
        2024    RAG Invalid
        2025    Document Name Not Provided
        2026    Verb Not Supported
        2027    Document Extension Invalid
        2028    Invalid File Size
        2029    Project name already exists
        2030    Assistant name already exists
        2031    Assistant not in Project
        2032    The status value is unexpected
        2041    The assistant specified is of a different type than expected
        3000    Data Analyst APIError: The connection with DataAnalyst Server could not be established
        3003    The assistant is currently being updated and is not yet available
        3004    Error validating metadata: each uploaded file requires related JSON metadata and vice versa
        3005    Error validating metadata: no metadata was found for file 'nameOfFile'

EXAMPLES
    The command:
        geai --configure
    will help you setup the required environment variables to work with GEAI.

    The command:
        ...

INSTALL MAN PAGES
    To install the manual pages, run:
        sudo geai-install-man
    (requires superuser privileges)

GEAI CLI - ORGANIZATION
-----------------------


SYNOPSIS
    geai organization <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai organization is a command from geai cli utility, developed to interact with key components of GEAI
    such as creating organizations and projects, defining assistants, managing workflows, etc.

    The options are as follows:
    help or h			Display help text

    list-assistants		List assistant information
      	--organization-id or --oid		UUID of the organization
    	--project-id or --pid		UUID of the project

    list-projects		List project information
      	--detail or -d		Defines the level of detail required. The available options are summary (default) or full (optional).
    	--name or -n		Name of the project

    get-project		Get project information
      	--project-id or --pid		GUID of the project (required)

    create-project		Create new project
      	--name or -n		Name of the new project
    	--description or -d		Description of the new project
    	--email or -e		Project administrator's email
    	--subscription-type		string: Options: Freemium, Daily, Weekly, Monthly)
    	--usage-unit		string: Options: Requests, Cost)
    	--soft-limit		number: Soft limit for usage (lower threshold))
    	--hard-limit		number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.
    	--renewal-status		string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable

    update-project		Update existing project
      	--project-id or --pid		GUID of the project (required)
    	--name or -n		Name of the project
    	--description or -d		Description of the new project

    delete-project		Delete existing project
      	--project-id or --pid		GUID of the project (required)

    get-tokens			Get project tokens
      	--project-id or --pid		GUID of the project (required)

    export-request		Export request data
      	--assistant-name		string: Assistant name (optional)
    	--status			string: Status (optional)
    	--skip			integer: Number of entries to skip
    	--count			integer: Number of entries to retrieve


EXAMPLES
    The command:
        geai c
    starts an interactive tool to configure API KEY and BASE URL to work with GEAI.

    The command:
        geai organization list-projects
    list available projects. For this, an organization API KEY is required.

    The command:
        ...







GEAI CLI - ASSISTANT
-----------------------


SYNOPSIS
    geai assistant <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai assistant is a command from geai cli utility, developed to interact with assistant in GEAI.

    The options are as follows:
    help or h			Display help text

    get-assistant		Get assistant detail
      	--detail or -d		Defines the level of detail required. The available options are summary (default) or full.
    	--assistant-id or --id		Assistant ID.

    create-assistant		Create new assistant
      	--type or -t		string: Type of assistant. Possible values: text, chat. (Required)
    	--name or -n		string: Name of the assistant (Required)
    	--description or -d		string: Description of the assistant.
    	--prompt			string: Prompt for the assistant  (Required)
    	--provider-name or --provider or -p		string: provider to be used
    	--model-name or -m		string: name of model according to selected provider
    	--temperature		decimal: Volatility of the assistant
    	--max-tokens		integer: Max number of tokens
    	--wd-title			Title for welcome data
    	--wd-description		Description for welcome data
    	--wd-feature		Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and "description". Example: '{"title": "title of feature", "description": "Description of feature"}'
    	--wd-example-prompt		Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description"  and "prompt_text". Example: '{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}'

    update-assistant		Update existing assistant
      	--assistant-id or --id		Assistant ID.
    	--status			integer: Possible values: 1:Enabled, 2:Disabled (Optional)
    	--action			string: Possible values: save, saveNewRevision (default), savePublishNewRevision
    	--revision-id		integer: Required if user needs to update an existent revision when action = save
    	--name or -n		string: Name of the assistant (Required)
    	--description or -d		string: Description of the assistant.
    	--prompt			string: Prompt for the assistant  (Required)
    	--provider-name or --provider or -p		string: provider to be used
    	--model-name or -m		string: name of model according to selected provider
    	--temperature		decimal: Volatility of the assistant
    	--max-tokens		integer: Max number of tokens
    	--wd-title			Title for welcome data
    	--wd-description		Description for welcome data
    	--wd-feature		Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and "description". Example: '{"title": "title of feature", "description": "Description of feature"}'
    	--wd-example-prompt		Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description"  and "prompt_text". Example: '{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}'

    delete-assistant		Delete existing assistant
      	--assistant-id or --id		Assistant ID.

    chat			Sends a chat request to the Globant Enterprise AI Assistant.
      	--name or -n		string: Name of the assistant.
    	--messages or --msg		array: Chat request data. It can be passed multiple times with single dictionary each time, or a single time as a list of dictionaries. Each dictionary instance must contain 'role' and 'content'
    	--revision			integer: Revision number.
    	--revision-name		string:	Name of the revision.
    	--variables or --var		collection: A list of key/value properties (optional)

    request-status		Retrieves the status of a request.
      	--request-id or --id		Request ID.

    cancel-request		Cancels a request.
      	--request-id or --id		Request ID.


GEAI CLI - RAG ASSISTANT
-----------------------


SYNOPSIS
    geai rag <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai RAG assistant is a command from geai cli utility, developed to interact with RAG assistant in GEAI.

    The options are as follows:
    help or h			Display help text
    list-assistants		Gets all RAG assistants from a project

    get-assistant		Gets a specific RAG assistant
      	--name or -n		RAG assistant name (required)

    create-assistant		Create a new RAG assistant
      	--name or -n		RAG assistant name (required)
    	--description or -d		string: Description of the RAG assistant
    	--template or --tpl		string: Name of an existing RAG to base the configuration (optional), empty by default
    	--history-count or --hc		integer: history count
    	--cache or -c		boolean: cache
    	--frequency-penalty or --fp		decimal: frequency penalty
    	--max-tokens or --mt		integer: max tokens
    	--model-name or -m		string: model name
    	-n			integer: n
    	--presence-penalty or --pp		decimal: presence penalty
    	--provider or -p		string: provider
    	--stream			boolean: stream
    	--temperature or --temp or -t		decimal: temperature
    	--top-p			decimal: top P
    	--llm-type			string: /: type* empty value (default) or json_object */
    	--verbose or -v		boolean: verbose
    	-k			integer: k
    	--search-type		string: /: type* similarity (default) or mmr */
    	--fetch-k or --fk		number: fetchK (valid when using mmr type)
    	--lambda or -l		decimal: lambda (valid when using mmr type)
    	--search-prompt or --sp		string: prompt
    	--return-source-documents or --rsd		boolean: return source documents
    	--score-threshold or --st		decimal: score threshold
    	--search-template or --stpl		string: template
    	--retriever-type		string: /: type* vectorStore, multiQuery, selfQuery, hyde, contextualCompression */
    	--retriever-search-type		string: searchType (similarity | similarity_hybrid | semantic_hybrid). Azure AISearch specific, defaults to similarity
    	--step			string: /: step* all (default) or documents */
    	--retriever-prompt or --rp		string: prompt (not needed when using vectorStore)
    	--chunk-overlap		Overlap size between chunks in the main document.
    	--chunk-size		Size of each chunk in the main document.
    	--use-parent-document		Whether to enable parent-child document relationships.
    	--child-k			Parameter to configure child document processing, such as relevance or retrieval count.
    	--child-chunk-size		Size of each chunk in the child document.
    	--child-chunk-overlap		Overlap size between chunks in the child document.
    	--wd-title			Title for welcome data
    	--wd-description		Description for welcome data
    	--wd-feature		Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and "description". Example: '{"title": "title of feature", "description": "Description of feature"}'
    	--wd-example-prompt		Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description"  and "prompt_text". Example: '{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}'

    update-assistant		Update existing RAG assistant
      	--name or -n		RAG assistant name (required)
    	--status			RAG assistant status (defaults to 1). 1: enabled; 0: disabled
    	--description or -d		string: Description of the RAG assistant
    	--template or --tpl		string: Name of an existing RAG to base the configuration (optional), empty by default
    	--history-count or --hc		integer: history count
    	--cache or -c		boolean: cache
    	--frequency-penalty or --fp		decimal: frequency penalty
    	--max-tokens or --mt		integer: max tokens
    	--model-name or -m		string: model name
    	-n			integer: n
    	--presence-penalty or --pp		decimal: presence penalty
    	--provider or -p		string: provider
    	--stream			boolean: stream
    	--temperature or --temp or -t		decimal: temperature
    	--top-p			decimal: top P
    	--llm-type			string: /: type* empty value (default) or json_object */
    	--verbose or -v		boolean: verbose
    	-k			integer: k
    	--search-type		string: /: type* similarity (default) or mmr */
    	--fetch-k or --fk		number: fetchK (valid when using mmr type)
    	--lambda or -l		decimal: lambda (valid when using mmr type)
    	--search-prompt or --sp		string: prompt
    	--return-source-documents or --rsd		boolean: return source documents
    	--score-threshold or --st		decimal: score threshold
    	--search-template or --stpl		string: template
    	--retriever-type		string: /: type* vectorStore, multiQuery, selfQuery, hyde, contextualCompression */
    	--retriever-search-type		string: searchType (similarity | similarity_hybrid | semantic_hybrid). Azure AISearch specific, defaults to similarity
    	--step			string: /: step* all (default) or documents */
    	--retriever-prompt or --rp		string: prompt (not needed when using vectorStore)
    	--wd-title			Title for welcome data
    	--wd-description		Description for welcome data
    	--wd-feature		Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and "description". Example: '{"title": "title of feature", "description": "Description of feature"}'
    	--wd-example-prompt		Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionaryeach time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description"  and "prompt_text". Example: '{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}'

    delete-assistant		Delete existing RAG assistant
      	--name or -n		RAG assistant name (required)

    list-documents		List documents for RAG assistant
      	--name or -n		RAG assistant name (required)
    	--skip or -s		Number of documents to skip
    	--count or -c		Number of documents to return (defaults to 10)

    delete-all-documents or del-docs		Delete all documents for RAG assistant
      	--name or -n		RAG assistant name (required)

    get-document or get-doc		Get document for RAG assistant
      	--name or -n		RAG assistant name (required)
    	--document-id or --id		Document id (required)

    upload-document or up-doc		Upload document for RAG assistant
      	--name or -n		RAG assistant name (required)
    	--file-path or -f		Path to document file (required)
    	--upload-type or -t		Upload type. Available options: binary or multipart (multipart/form-data). Defaults to multipart
    	--metadata or -m		Document metadata (only available for multipart/form-data). Can be valid JSON or a path to metadata file.
    	--content-type or --ct		Document content type

    delete-document or del-doc		Delete document for RAG assistant by id
      	--name or -n		RAG assistant name (required)
    	--document-id or --id		Document id (required)


GEAI CLI - CHAT
----------------


SYNOPSIS
    geai chat <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai chat is a command from geai cli utility, developed to chat with assistant in GEAI.

    The options are as follows:
    help or h			Display help text

    completion or comp		Get chat completion
      	--model or -m		The model needs to address the assistant type and name or bot_id, depending on the Type. Then, the parameters will vary depending on the type. Its format is as follows: 
	"model": "saia:<assistant_type>:<assistant_name>|<bot_id>"
    	--messages or --msg		The messages element defines the desired messages to be added. The minimal value needs to be the following, where the content details the user input.
	{ 
		"role": "string", /* user, system and may support others depending on the selected model */ 
		"content": "string" 
	}

    	--stream			If response should be streamed. Possible values: 0: OFF; 1: ON
    	--temperature or --temp		Float value to set volatility of the assistant's answers (between 0 and 2)
    	--max-tokens		Integer value to set max tokens to use
    	--thread-id		Optional UUID for conversation identifier
    	--frequency-penalty		Optional number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    	--presence-penalty		Optional number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
    	--top-p			Optional float value for nucleus sampling, where the model considers tokens with top_p probability mass (between 0 and 1). An alternative to temperature.
    	--stop			Optional string or JSON array of up to 4 sequences where the API will stop generating further tokens.
    	--response-format		Optional JSON object specifying the output format, e.g., {"type": "json_schema", "json_schema": {...}} for structured outputs.
    	--tools			Optional JSON array of tools (e.g., functions) the model may call.
    	--tool-choice		Optional string (e.g., "none", "auto") or JSON object to control which tool is called.
    	--logprobs			Optional boolean to return log probabilities of output tokens. Possible values: 0: OFF; 1: ON
    	--top-logprobs		Optional integer (0-20) specifying the number of most likely tokens to return with log probabilities.
    	--seed			Optional integer for deterministic sampling (in Beta).
    	--stream-options		Optional JSON object for streaming options, e.g., {"include_usage": true}.
    	--store			Optional boolean to store the output for model distillation or evals. Possible values: 0: OFF; 1: ON
    	--metadata			Optional JSON object with up to 16 key-value pairs to attach to the object.
    	--user			Optional string identifier for the end-user to monitor abuse.
    iris			Interactive chat with Iris

    agent			Interactive chat with Agent
      	--agent-name or --name or -n	You can use the internal name, public name and agent id in order to chat interactively with any agent	
    	--gui or -g		Launch a Streamlit GUI chat interface. Possible values: 0: OFF; 1: ON


GEAI CLI - ADMIN
-----------------------


SYNOPSIS
    geai admin <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai admin is a command from geai cli utility, developed to interact instance of GEAI.

    The options are as follows:
    help or h			Display help text
    validate-token or vt		Validate API Token: Obtains organization and project information related to the provided apitoken.
    list-authorized-organizations or auth-org		Obtain the list of organizations that a user is permitted to access.

    list-authorized-projects or auth-proj		Obtain the list of projects that a user is permitted to access in a particular organization.
      	--organization or --org or -o		ID of the organization.

    project-visibility or pv		Determines if a GAM user has visibility of a project
      	--organization or --org or -o		ID of the organization.
    	--project or -p		ID of the project.
    	--access-token or --token or --at		GAM access token.

    project-token or pt		Returns Project's API Token
      	--organization or --org or -o		ID of the organization.
    	--project or -p		ID of the project.
    	--access-token or --token or --at		GAM access token.


GEAI CLI - LLM
-----------------------


SYNOPSIS
    geai llm <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai llm is a command from geai cli utility, developed to retrieve information about available models and providers 
    in GEAI.

    The options are as follows:
    help or h			Display help text
    list-providers or lp		Retrieve providers list

    get-provider or gp		Retrieve provider data
      	--provider-name or --pn		LLM Provider name (required)

    list-models or lm		Retrieve provider models
      	--provider-name or --pn		LLM Provider name (required)

    get-model or gm		Retrieve model data
      	--provider-name or --pn		LLM Provider name (required)
    	--model-name or --mn		LLM Model name
    	--model-id or --mid		LLM Model ID


GEAI CLI - FILES
-----------------------


SYNOPSIS
    geai files <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai files is a command from geai cli utility, developed to interact with files in GEAI.

    The options are as follows:
    help or h			Display help text

    upload-file or uf		Upload file
      	--organization or --org or -o		Organization ID (required)
    	--project or --proj or -p		Project ID (required)
    	--file-name or --fn		File name (optional). If not provided, the name of the uploaded file will be used.
    	--file-path or --fp		File path to the file you want to upload (required)
    	--folder or -f		Destination folder (optional). If not provided, the file will be temporarily saved.

    get-file or gf		Get file data
      	--organization or --org or -o		Organization ID (required)
    	--project or --proj or -p		Project ID (required)
    	--file-id or --fid		File ID (required)

    delete-file or df		Delete file data
      	--organization or --org or -o		Organization ID (required)
    	--project or --proj or -p		Project ID (required)
    	--file-id or --fid		File ID (required)

    get-file-content or gfc		Get file content
      	--organization or --org or -o		Organization ID (required)
    	--project or --proj or -p		Project ID (required)
    	--file-id or --fid		File ID (required)

    list-files or lf		Retrieve file list
      	--organization or --org or -o		Organization ID (required)
    	--project or --proj or -p		Project ID (required)


GEAI CLI - USAGE LIMITS
-----------------------


SYNOPSIS
    geai usage-limit <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai usage-limits is a command from geai cli utility, developed to manager usage limits in GEAI.

    The options are as follows:
    help or h			Display help text

    set-organization-limit or set-org-lim		Set organization usage limit
      	--organization or --org or -o		Organization ID (Required)
    	--subscription-type		string: Options: Freemium, Daily, Weekly, Monthly)
    	--usage-unit		string: Options: Requests, Cost)
    	--soft-limit		number: Soft limit for usage (lower threshold))
    	--hard-limit		number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.
    	--renewal-status		string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable

    get-latest-organization-limit or get-latest-org-lim		Get latest organization usage limit
      	--organization or --org or -o		Organization ID (Required)

    get-all-organization-limit or get-all-org-lim		Get all organization usage limit
      	--organization or --org or -o		Organization ID (Required)

    delete-organization-limit or del-org-lim		Delete organization usage limit
      	--organization or --org or -o		Organization ID (Required)
    	--limit-id or --lid		Usage limit ID (Required)

    update-organization-limit or up-org-lim		Update organization usage limit
      	--organization or --org or -o		Organization ID (Required)
    	--limit-id or --lid		Usage limit ID (Required)
    	--hard-limit		number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.
    	--soft-limit		number: Soft limit for usage (lower threshold))
    	--renewal-status		string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable

    set-project-limit or set-proj-lim		Set project usage limit
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)
    	--subscription-type		string: Options: Freemium, Daily, Weekly, Monthly)
    	--usage-unit		string: Options: Requests, Cost)
    	--soft-limit		number: Soft limit for usage (lower threshold))
    	--hard-limit		number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.
    	--renewal-status		string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable

    get-all-project-limit or get-all-proj-lim		Get all usage limits for project
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)

    get-latest-project-limit or get-latest-proj-lim		Get latest usage limit for project
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)

    get-active-project-limit or get-active-proj-lim		Get active usage limit for project
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)

    delete-project-limit or del-proj-lim		Get active usage limit for project
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)
    	--limit-id or --lid		Usage limit ID (Required)

    update-project-limit or up-proj-lim		Update project usage limit
      	--organization or --org or -o		Organization ID (Required)
    	--project or --proj or -p		Project ID (Required)
    	--limit-id or --lid		Usage limit ID (Required)
    	--hard-limit		number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.
    	--soft-limit		number: Soft limit for usage (lower threshold))
    	--renewal-status		string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable


GEAI CLI - EMBEDDINGS
-----------------------


SYNOPSIS
    geai embeddings <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai embeddings is a command from geai cli utility, developed to generate embeddings in GEAI.

    The options are as follows:
    help or h			Display help text

    generate or gen		Get embeddings
      	--input or -i		string: Input to embed, encoded as a string. To embed multiple inputs in a single request, pass the string inputs multiple times using -i. The input must not exceed the max input tokens for the model and cannot be an empty string
    	--model or -m		string: provider/modelId to use
    	--encoding-format or --enc-for		string: The format to return the embeddings. It can be either float (default) or base64 (optional)
    	--dimensions or --dim		integer: The number of dimensions the resulting output embeddings should have. Only supported in text-embedding-3* and later models (optional)
    	--user or -u		string: A unique identifier representing your end-user
    	--input-type or --it		string: Defines how the input data will be used when generating embeddings (optional)
    	--timeout or -t		integer: The maximum time, in seconds, to wait for the API to respond. Defaults to 600 seconds
    	--cache			Enable X-Saia-Cache-Enabled to cache the embeddings for the model; it applies by Organization/Project.1 to set to True and 0 to false. 0 is default


GEAI CLI - FEEDBACK
--------------------


SYNOPSIS
    geai feedback <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai feedback is a command from geai cli utility, developed to send feedback from the assistant's answers.

    The options are as follows:
    help or h			Display help text

    send or sf			Send feedback
      	--request-id or --rid		The request associated with a user's execution. Integer
    	--origin			Origin for the feedback. Defaults to user-feedback
    	--answer-score or --ans-score or --score		Associated feedback: 1 good, 2 bad
    	--comments			Associated feedback comment (optional)


GEAI CLI - RERANK
-----------------


SYNOPSIS
    geai rerank <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai rerank is a command from geai cli utility, developed to rerank a list of document chunks based on a query in GEAI.

    The options are as follows:
    help or h			Display help text

    rerank-chunks or chunks or rc		Rerank chunks based on a query
      	--query or -q		string: Input query
    	--model or -m		string: provider/modelName reranker to use; supported values: cohere/rerank-v3.5, awsbedrock/cohere.rerank-v3.5, awsbedrock/amazon.rerank-v1
    	--documents or --doc or -d		string or array: A list of text chunks
    	--top-n			string: Count of best n results to return


GEAI CLI - EVALUATION
----------------------


SYNOPSIS
    geai evaluation <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai evaluation is a command from geai cli utility, developed to interact with Dataset, Plan and Result APIs from
    the Evaluation module.

    Dataset rows have the following structure:
        {
            "dataSetRowExpectedAnswer": "This is the expected answer", 
            "dataSetRowInput": "What is the capital of France?", 
            "dataSetRowContextDocument": "", 
            "expectedSources": [
                {
                    "dataSetExpectedSourceId": "UUID", 
                    "dataSetExpectedSourceName": "Source Name", 
                    "dataSetExpectedSourceValue": "Some value", 
                    "dataSetexpectedSourceExtention": "pdf"
                }
                ], 
                "filterVariables": [
                {
                    "dataSetMetadataType": "Type", 
                    "dataSetRowFilterKey": "key", 
                    "dataSetRowFilterOperator": "equals", 
                    "dataSetRowFilterValue": "value", 
                    "dataSetRowFilterVarId": "UUID"
                }
            ]
        }

    The options are as follows:
    help or h			Display help text
    list-datasets or ld		List all datasets

    create-dataset or cd		Create dataset
      	--dataset-name or --dn		dataSetName: string
    	--dataset-description or --dd		dataSetDescription: string
    	--dataset-type or --dt		dataSetType: string //e.g., 'T' for test, 'E' for evaluation, etc.
    	--dataset-active or --da		dataSetActive: boolean. 0: False; 1: True
    	--row or -r		JSON object containing row data
    	--dataset-file or --df		dataSetActive: Creates a new dataset from a JSON file. The file must contain the complete dataset structure, including header information and rows.

    get-dataset or gd		Get dataset by ID
      	--dataset-id or --did		UUID representing the dataset to retrieve

    update-dataset or ud		Update dataset by ID
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--dataset-name or --dn		dataSetName: string
    	--dataset-description or --dd		dataSetDescription: string
    	--dataset-type or --dt		dataSetType: string //e.g., 'T' for test, 'E' for evaluation, etc.
    	--dataset-active or --da		dataSetActive: boolean. 0: False; 1: True
    	--row or -r		JSON object containing row data

    delete-dataset or dd		Delete dataset by ID
      	--dataset-id or --did		UUID representing the dataset to retrieve

    create-dataset-row or cdr		Create dataset row
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row or -r		JSON object containing row data

    list-dataset-rows or ldr		List dataset rows
      	--dataset-id or --did		UUID representing the dataset to retrieve

    get-dataset-row or gdr		Get dataset row
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve

    update-dataset-row or udr		Update dataset row
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--row or -r		JSON object containing row data

    delete-dataset-row or ddr		Delete dataset row
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve

    create-expected-source or ces		Create dataset row expected source
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--name or -n		dataSetExpectedSourceName: string
    	--value or -v		dataSetExpectedSourceValue: string
    	--extension or -e		dataSetExpectedSourceExtension: string //e.g., 'txt', 'pdf', 'json'

    list-expected-sources or les		List dataset row expected sources
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve

    get-expected-source or ges		Get dataset row expected source
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--expected-source-id or --esid		UUID representing the expected source to retrieve

    update-expected-source or ues		Update dataset row expected source
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--expected-source-id or --esid		UUID representing the expected source to retrieve
    	--name or -n		dataSetExpectedSourceName: string
    	--value or -v		dataSetExpectedSourceValue: string
    	--extension or -e		dataSetExpectedSourceExtension: string //e.g., 'txt', 'pdf', 'json'

    delete-expected-source or des		Delete dataset row expected source
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--expected-source-id or --esid		UUID representing the expected source to retrieve

    create-filter-variable or cfv		Create dataset row filter variable
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--metadata-type or --mt		dataSetMetadataType: string //e.g., 'V' for variable, 'F' for flag, etc.
    	--key or -k		dataSetRowFilterKey: string. The name of the filter key
    	--value or -v		dataSetRowFilterValue: string. The value to filter by
    	--operator or -o		dataSetRowFilterOperator: string ///e.g., '=', '!=', '>', '<', 'contains', etc.

    list-filter-variables or lfv		List dataset row filter variables
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve

    get-filter-variable or gfv		Get dataset row filter variable
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--filter-variable-id or --fvid		UUID representing the filter variable to retrieve

    update-filter-variable or ufv		Update dataset row filter variable
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--filter-variable-id or --fvid		UUID representing the filter variable to retrieve
    	--metadata-type or --mt		dataSetMetadataType: string //e.g., 'V' for variable, 'F' for flag, etc.
    	--key or -k		dataSetRowFilterKey: string. The name of the filter key
    	--value or -v		dataSetRowFilterValue: string. The value to filter by
    	--operator or -o		dataSetRowFilterOperator: string ///e.g., '=', '!=', '>', '<', 'contains', etc.

    delete-filter-variable or dfv		Delete dataset row filter variable
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--row-id or --rid		UUID representing the row dataset to retrieve
    	--filter-variable-id or --fvid		UUID representing the filter variable to retrieve

    upload-dataset-rows or udrf		Upload dataset rows file
      	--dataset-id or --did		UUID representing the dataset to retrieve
    	--rows-file or --rf		The JSON file should contain an array of DatasetRow objects
    list-evaluation-plans or lep		Retrieves a list of all evaluation plans.

    create-evaluation-plan or cep		Creates a new evaluation plan.
      	--name or --epn		Name of the evaluation plan
    	--assistant-type or --epat		Type of assistant (e.g., 'TextPromptAssistant', 'RAG Assistant')
    	--assistant-id or --epai		UUID of the assistant (optional, required for TextPromptAssistant)
    	--assistant-name or --epan		Name of the assistant (optional, required for TextPromptAssistant)
    	--assistant-revision or --epar		Revision of the assistant (optional, required for TextPromptAssistant)
    	--profile-name or --eppn		Name of the RAG profile (optional, required for RAG Assistant)
    	--dataset-id or --did		ID of the dataset (optional)
    	--system-metrics or --sm		Array of system metrics (each with 'systemMetricId' and 'systemMetricWeight')Alternatively, multiple instances of --sm can be passes as arguments for a single list.

    get-evaluation-plan or gep		Retrieve evaluation plan by ID.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve

    update-evaluation-plan or uep		Update evaluation plan by ID.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve
    	--name or --epn		Name of the evaluation plan
    	--assistant-type or --epat		Type of assistant (e.g., 'TextPromptAssistant', 'RAG Assistant')
    	--assistant-id or --epai		UUID of the assistant (optional, required for TextPromptAssistant)
    	--assistant-name or --epan		Name of the assistant (optional, required for TextPromptAssistant)
    	--assistant-revision or --epar		Revision of the assistant (optional, required for TextPromptAssistant)
    	--profile-name or --eppn		Name of the RAG profile (optional, required for RAG Assistant)
    	--dataset-id or --did		ID of the dataset (optional)
    	--system-metrics or --sm		Array of system metrics (each with 'systemMetricId' and 'systemMetricWeight')Alternatively, multiple instances of --sm can be passes as arguments for a single list.

    delete-evaluation-plan or dep		Delete evaluation plan by ID.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve

    list-evaluation-plan-system-metrics or lepsm		List system metrics for evaluation plan by ID.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve

    add-evaluation-plan-system-metric or aepsm		Adds a new system metric to an existing evaluation plan.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve
    	--system-metric-id or --smid		systemMetricId: string. ID of the system metric
    	--system-metric-weight or --smw		systemMetricWeight: number. Weight of the system metric (between 0 and 1)

    get-evaluation-plan-system-metric or gepsm		Retrieves a specific system metric from a given evaluation plan.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve
    	--system-metric-id or --smid		ID of the system metric

    update-evaluation-plan-system-metric or uepsm		Updates a specific system metric within an existing evaluation plan.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve
    	--system-metric-id or --smid		systemMetricId: string. ID of the system metric
    	--system-metric-weight or --smw		systemMetricWeight: number. Weight of the system metric (between 0 and 1)

    delete-evaluation-plan-system-metric or depsm		Delete a specific system metric within an existing evaluation plan.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve
    	--system-metric-id or --smid		ID of the system metric
    list-available-system-metrics or lsm		Retrieves a list of all available system metrics that can be used in evaluation plans

    get-system-metrics or gsm		Retrieves a specific system metric using its ID.
      	--system-metric-id or --smid		ID of the system metric

    execute-evaluation-plan or xep		Initiates the execution of a previously defined evaluation plan. The evaluation plan's configuration (assistant, dataset, metrics, and weights) determines how the assessment is performed.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve

    list-evaluation-results or ler		Retrieves a list of evaluation results associated with a specific evaluation plan.
      	--evaluation-plan-id or --epid		UUID representing the evaluation plan to retrieve

    get-evaluation-result or ger		Retrieves a specific evaluation result by its ID.
      	--evaluation-result-id or --erid		UUID representing the evaluation result to retrieve


EXAMPLES
    The command:
        geai evaluation create-dataset \
            --dataset-name "MyNewDataset" \
            --dataset-description "A dataset for testing" \
            --dataset-type "T" \
            --dataset-active 1 \
            --row '[
                {
                "dataSetRowExpectedAnswer": "This is the expected answer", 
                "dataSetRowInput": "What is the capital of France?", 
                "dataSetRowContextDocument": ""
                }
            ]'

    This will create a new dataset called "MyNewDataset" with a description, type "T" (test), and one row where the expected answer is provided along with the input question.

    The command:
        geai evaluation create-dataset \
            --dataset-name "MyNewDataset" \
            --dataset-description "A dataset for testing" \
            --dataset-type "T" \
            --dataset-active 1 \
            --row '[
                {
                    "dataSetRowExpectedAnswer": "This is the expected answer", 
                    "dataSetRowInput": "What is the capital of France?", 
                    "dataSetRowContextDocument": "", 
                    "expectedSources": [
                        {
                            "dataSetExpectedSourceId": "UUID", 
                            "dataSetExpectedSourceName": "Source Name", 
                            "dataSetExpectedSourceValue": "Some value", 
                            "dataSetexpectedSourceExtention": "pdf"
                        }
                        ], 
                        "filterVariables": [
                        {
                            "dataSetMetadataType": "Type", 
                            "dataSetRowFilterKey": "key", 
                            "dataSetRowFilterOperator": "equals", 
                            "dataSetRowFilterValue": "value", 
                            "dataSetRowFilterVarId": "UUID"
                        }
                        ]
                    }
                ]'

    This will create a new dataset with rows that include optional "expectedSources" and "filterVariables".

GEAI CLI - GAM
----------------

SYNOPSIS
    geai gam <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai gam is a command from geai cli utility, developed to interact with GAM authentication mechanisms in GEAI.

    The options are as follows:
    help or h			Display help text

    get-access-token or gat		Get access token
      	--client-id or --cid		Application Client ID.
    	--client-secret or --cs		Application Client Secret.
    	--grant-type or --gt		Grant type for authentication. Default: "password"
    	--authentication-type-name or --atn		Authentication type name. Default: "local"
    	--scope or -s		Scope of the user account you want to access. gam_user_data+gam_user_roles. Default: "gam_user_data"
    	--username or -u		Username of the user to be authenticated.
    	--password or -p		Password of the user to be authenticated.
    	--initial-properties or --ip		User custom properties array.
    	--repository or -r		Only use if the IDP is multitenant.
    	--request-token-type or --rtt		Determines the token type to return and, based on that, the Security Policy to be applied. Default: "OAuth"

    get-user-info or gui		Get user info
      	--access-token or --at		The access_token obtained in the previous request.

    refresh-access-token or rat		Refresh access token
      	--client-id or --cid		Application Client ID.
    	--client-secret or --cs		Application Client Secret.
    	--grant-type or --gt		Grant type for authentication. Must be: "refresh_token"
    	--refresh-token or --rt		Refresh token.


GEAI CLI - SECRETS
----------------


SYNOPSIS
    geai secrets <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai secrets is a command from geai cli utility, developed to handle secrets in in GEAI.

    The options are as follows:
    help or h			Display help text

    get-secret or gs		Retrieve a secret by its ID
      	--secret-id or --sid		The unique identifier of the secret to retrieve (required)

    create-secret or cs		Create a new secret
      	--name or -n		The name of the secret (required)
    	--secret-string or -ss		The secret value to store (required)
    	--description or -d		A description of the secret (optional)

    update-secret or us		Update an existing secret by its ID
      	--secret-id or --sid		The unique identifier of the secret to update (required)
    	--name or -n		The updated name of the secret (required)
    	--secret-string or -ss		The updated secret value (required)
    	--description or -d		The updated description of the secret (optional)

    list-secrets or ls		List secrets with optional filtering and pagination
      	--name or -n		Filter secrets by name (optional)
    	--id			Filter secrets by ID (optional)
    	--start			Starting index for pagination (integer, default: 0)
    	--count			Number of secrets to return (integer, default: 10)


GEAI CLI - AI LAB
-----------------


SYNOPSIS
    geai ai-lab <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai ai-lab is a command from geai cli utility, developed to interact with AI Lab in GEAI.

    The options are as follows:
    help or h			Display help text

    list-agents or la		List agents
      	--project-id or --pid		ID of the project
    	--status			Status of the agents to filter by. Defaults to an empty string (no filtering).
    	--start			Starting index for pagination. Defaults to an empty string (no offset).
    	--count			Number of agents to retrieve. Defaults to an empty string (no limit).
    	--access-scope		Access scope of the agents, either "public" or "private". Defaults to "public".
    	--allow-drafts		Whether to include draft agents. Defaults to 1 (True).
    	--allow-external		Whether to include external agents. Defaults to 0 (False).

    create-agent or ca		Create agent
      	--project-id or --pid		Unique identifier of the project where the agent will be created
    	--name or -n		Name of the agent, must be unique within the project and exclude ':' or '/'
    	--access-scope or --as		Access scope of the agent, either 'public' or 'private' (defaults to 'private')
    	--public-name or --pn		Public name of the agent, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.example.my-agent') with only alphanumeric characters, periods, dashes, or underscores
    	--job-description or --jd		Description of the agent's role
    	--avatar-image or --aimg		URL for the agent's avatar image
    	--description or -d		Detailed description of the agent's purpose
    	--agent-data-prompt-instructions or --adp-inst		Instructions defining what the agent does and how, required for publication if context is not provided
    	--agent-data-prompt-input or --adp-input		Agent Data prompt input: Prompt input as a list of strings (e.g., '["input1", "input2"]') or multiple single strings via repeated flags, each representing an input name
    	--agent-data-prompt-output or --adp-out		Prompt output in JSON format (e.g., '[{"key": "output_key", "description": "output description"}]'), as a dictionary or list of dictionaries with 'key' and 'description' fields
    	--agent-data-prompt-example or --adp-ex		Prompt example in JSON format (e.g., '[{"inputData": "example input", "output": "example output"}]'), as a dictionary or list of dictionaries with 'inputData' and 'output' fields
    	--agent-data-llm-max-tokens or --adl-max-tokens		Maximum number of tokens the LLM can generate, used to control costs
    	--agent-data-llm-timeout or --adl-timeout		Timeout in seconds for LLM responses
    	--agent-data-llm-temperature or --adl-temperature		Sampling temperature for LLM (0.0 to 1.0), lower values for focused responses, higher for more random outputs
    	--agent-data-llm-top-k or --adl-top-k		TopK sampling parameter for LLM (currently unused)
    	--agent-data-llm-top-p or --adl-top-p		TopP sampling parameter for LLM (currently unused)
    	--agent-data-model-name or --adm-name		Name of the LLM model (e.g., 'gpt-4o' or 'openai/gpt-4o'), at least one valid model required for publication
    	--agent-data-resource-pools or --adr-pools		Resource pools in JSON format (e.g., '[{"name": "pool_name", "tools": [{"name": "tool_name", "revision": int}], "agents": [{"name": "agent_name", "revision": int}]}]'), as a list of dictionaries with 'name' (required) and optional 'tools' and 'agents' lists
    	--automatic-publish or --ap		Whether to publish the agent after creation (0: create as draft, 1: create and publish)

    get-agent or ga		Get agent
      	--project-id or --pid		ID of the project
    	--agent-id or --aid		ID of the agent to retrieve
    	--revision or -r		Revision of agent.
    	--version or -v		Version of agent.
    	--allow-drafts		Whether to include draft agents. Defaults to 1 (True).

    create-sharing-link or csl		Create sharing link
      	--project-id or --pid		ID of the project
    	--agent-id or --aid		ID of the agent to retrieve

    publish-agent-revision or par		Publish agent revision
      	--project-id or --pid		ID of the project
    	--agent-id or --aid		ID of the agent to retrieve
    	--revision or -r		Revision of agent.

    delete-agent or da		Delete agent
      	--project-id or --pid		ID of the project
    	--agent-id or --aid		ID of the agent to retrieve

    update-agent or ua		Update agent by ID or name
      	--project-id or --pid		Unique identifier of the project where the agent will be created
    	--agent-id or --aid		Unique identifier of the agent to update
    	--name or -n		Name of the agent, must be unique within the project and exclude ':' or '/'
    	--access-scope or --as		Access scope of the agent, either 'public' or 'private' (defaults to 'private')
    	--public-name or --pn		Public name of the agent, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.example.my-agent') with only alphanumeric characters, periods, dashes, or underscores
    	--job-description or --jd		Description of the agent's role
    	--avatar-image or --aimg		URL for the agent's avatar image
    	--description or -d		Detailed description of the agent's purpose
    	--agent-data-prompt-instructions or --adp-inst		Instructions defining what the agent does and how, required for publication if context is not provided
    	--agent-data-prompt-input or --adp-input		Agent Data prompt input: Prompt input as a list of strings (e.g., '["input1", "input2"]') or multiple single strings via repeated flags, each representing an input name
    	--agent-data-prompt-output or --adp-out		Prompt output in JSON format (e.g., '[{"key": "output_key", "description": "output description"}]'), as a dictionary or list of dictionaries with 'key' and 'description' fields
    	--agent-data-prompt-example or --adp-ex		Prompt example in JSON format (e.g., '[{"inputData": "example input", "output": "example output"}]'), as a dictionary or list of dictionaries with 'inputData' and 'output' fields
    	--agent-data-llm-max-tokens or --adl-max-tokens		Maximum number of tokens the LLM can generate, used to control costs
    	--agent-data-llm-timeout or --adl-timeout		Timeout in seconds for LLM responses
    	--agent-data-llm-temperature or --adl-temperature		Sampling temperature for LLM (0.0 to 1.0), lower values for focused responses, higher for more random outputs
    	--agent-data-llm-top-k or --adl-top-k		TopK sampling parameter for LLM (currently unused)
    	--agent-data-llm-top-p or --adl-top-p		TopP sampling parameter for LLM (currently unused)
    	--agent-data-model-name or --adm-name		Name of the LLM model (e.g., 'gpt-4o' or 'openai/gpt-4o'), at least one valid model required for publication
    	--agent-data-resource-pools or --adr-pools		Resource pools in JSON format (e.g., '[{"name": "pool_name", "tools": [{"name": "tool_name", "revision": int}], "agents": [{"name": "agent_name", "revision": int}]}]'), as a list of dictionaries with 'name' (required) and optional 'tools' and 'agents' lists
    	--automatic-publish or --ap		Whether to publish the agent after creation (0: create as draft, 1: create and publish)
    	--upsert			Define if agent must be created if it doesn't exist (0: Update only if it exists. 1: Insert if doesn't exists)

    create-tool or ct		Create tool
      	--project-id or --pid		Unique identifier of the project where the tool will be created
    	--name or -n		Name of the tool, must be unique within the project and exclude ':' or '/'
    	--description or -d		Description of the tool’s purpose, helps agents decide when to use it
    	--scope or -s		Scope of the tool, one of 'builtin', 'external', or 'api'
    	--access-scope or --as		Access scope of the tool, either 'public' or 'private' (defaults to 'private')
    	--public-name or --pn		Public name of the tool, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores
    	--icon or -i		URL for the tool’s icon or avatar image
    	--open-api or --oa		URL where the OpenAPI specification can be loaded, required for 'api' scope if open_api_json is not provided
    	--open-api-json or --oaj		OpenAPI specification in JSON format (e.g., '{"openapi": "3.0.0", "info": {"title": "example", "version": "1.0.0"}, ...}'), required for 'api' scope if open_api is not provided
    	--report-events or --re		Event reporting mode for tool progress, one of 'None', 'All', 'Start', 'Finish', 'Progress' (defaults to 'None')
    	--parameter or -p		Tool parameter in JSON format (e.g., '{"key": "param_name", "description": "param description", "isRequired": true, "type": "app"}' or for config parameters: '{"key": "config_name", "description": "config description", "isRequired": true, "type": "config", "value": "config_value", "fromSecret": false}'). Multiple parameters can be specified by using this option multiple times
    	--automatic-publish or --ap		Whether to publish the tool after creation (0: create as draft, 1: create and publish)

    list-tools or lt		List tools
      	--project-id or --pid		ID of the project
    	--id			ID of the tool to filter by. Defaults to an empty string (no filtering).
    	--count			Number of tools to retrieve. Defaults to '100'.
    	--access-scope		Access scope of the tools, either "public" or "private". Defaults to "public".
    	--allow-drafts		Whether to include draft tools. Defaults to 1 (True).
    	--scope			Scope of the tools, must be 'builtin', 'external', or 'api'. Defaults to 'api'.
    	--allow-external		Whether to include external tools. Defaults to 1 (True).

    get-tool or gt		Get tool
      	--project-id or --pid		ID of the project
    	--tool-id or --tid		ID of the tool to retrieve
    	--revision or -r		Revision of agent.
    	--version or -v		Version of agent.
    	--allow-drafts		Whether to include draft agents. Defaults to 1 (True).

    delete-tool or dt		Delete tool
      	--project-id or --pid		ID of the project
    	--tool-id or --tid		ID of the tool to delete
    	--tool-name or --tname		Name of the tool to delete

    update-tool or ut		Update tool
      	--project-id or --pid		Unique identifier of the project containing the tool
    	--tool-id or --tid		Unique identifier of the tool to update
    	--name or -n		Updated name of the tool, must be unique within the project and exclude ':' or '/' if provided
    	--description or -d		Updated description of the tool’s purpose, helps agents decide when to use it
    	--scope or -s		Updated scope of the tool, one of 'builtin', 'external', or 'api'
    	--access-scope or --as		Updated access scope of the tool, either 'public' or 'private'
    	--public-name or --pn		Updated public name of the tool, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores
    	--icon or -i		Updated URL for the tool’s icon or avatar image
    	--open-api or --oa		Updated URL where the OpenAPI specification can be loaded, required for 'api' scope in upsert mode if open_api_json is not provided
    	--open-api-json or --oaj		Updated OpenAPI specification in JSON format (e.g., '{"openapi": "3.0.0", "info": {"title": "example", "version": "1.0.0"}, ...}'), required for 'api' scope in upsert mode if open_api is not provided
    	--report-events or --re		Updated event reporting mode for tool progress, one of 'None', 'All', 'Start', 'Finish', 'Progress'
    	--parameter or -p		Updated tool parameter in JSON format (e.g., '{"key": "param_name", "description": "param description", "isRequired": true, "type": "app"}' or for config parameters: '{"key": "config_name", "description": "config description", "isRequired": true, "type": "config", "value": "config_value", "fromSecret": false}'). Multiple parameters can be specified by using this option multiple times
    	--automatic-publish or --ap		Whether to publish the tool after updating (0: update as draft, 1: update and publish)
    	--upsert			Whether to create the tool if it doesn’t exist (0: update only if exists, 1: insert if doesn’t exist)

    publish-tool-revision or ptr		Publish tool revision
      	--project-id or --pid		ID of the project
    	--tool-id or --tid		ID of the tool to retrieve
    	--revision or -r		Revision of tool. Use 0 to retrieve the latest revision.

    get-parameter or gp		Get tool parameter
      	--project-id or --pid		ID of the project
    	--tool-id or --tid		ID of the tool to set parameters for
    	--tool-public-name or --tpn		Public name of the tool
    	--revision or -r		Revision of the parameter. Use 0 to retrieve the latest revision.
    	--version or -v		Version of the parameter. Use 0 to retrieve the latest version.
    	--allow-drafts		Whether to include draft parameters. Defaults to 1 (True).

    set-parameter or sp		Set tool parameter
      	--project-id or --pid		ID of the project
    	--tool-id or --tid		ID of the tool to set parameters for
    	--tool-public-name or --tpn		Public name of the tool
    	--parameter or -p		Tool parameter in JSON format. For regular parameters: '{"key": "param_name", "dataType": "String", "description": "param description", "isRequired": true}' For config parameters: '{"key": "config_name", "dataType": "String", "description": "config description", "isRequired": true, "type": "config", "fromSecret": false, "value": "config_value"}' Multiple parameters can be specified by using this option multiple times.

    list-reasoning-strategies or lrs		List reasoning strategies
      	--name or -n		Name of the reasoning strategy to filter by. Defaults to an empty string (no filtering).
    	--start			Starting index for pagination. Defaults to '0'.
    	--count			Number of reasoning strategies to retrieve. Defaults to '100'.
    	--allow-external		Whether to include external reasoning strategies. Defaults to 1 (True).
    	--access-scope		Access scope of the reasoning strategies, either 'public' or 'private'. Defaults to 'public'.

    create-reasoning-strategy or crs		Create reasoning strategy
      	--project-id or --pid		ID of the project
    	--name or -n		Name of the reasoning strategy
    	--system-prompt or --sp		System prompt for the reasoning strategy
    	--access-scope or --as		Access scope of the reasoning strategy, either 'public' or 'private'. Defaults to 'public'.
    	--type or -t		Type of the reasoning strategy, e.g., 'addendum'. Defaults to 'addendum'.
    	--localized-description or --ld		Localized description in JSON format: '{"language": "english", "description": "description text"}'. Multiple descriptions can be specified by using this option multiple times.
    	--automatic-publish or --ap		Define if reasoning strategy must be published besides being created. 0: Create as draft. 1: Create and publish.

    update-reasoning-strategy or urs		Update reasoning strategy
      	--project-id or --pid		ID of the project
    	--reasoning-strategy-id or --rsid		ID of the reasoning strategy to update
    	--name or -n		Name of the reasoning strategy (optional for update)
    	--system-prompt or --sp		System prompt for the reasoning strategy (optional for update)
    	--access-scope or --as		Access scope of the reasoning strategy, either 'public' or 'private' (optional for update)
    	--type or -t		Type of the reasoning strategy, e.g., 'addendum' (optional for update)
    	--localized-description or --ld		Localized description in JSON format: '{"language": "english", "description": "description text"}'. Multiple descriptions can be specified by using this option multiple times (optional for update).
    	--automatic-publish or --ap		Define if reasoning strategy must be published after being updated. 0: Update as draft. 1: Update and publish. Defaults to 0.
    	--upsert			Define if reasoning strategy must be created if it doesn't exist. 0: Update only if it exists. 1: Insert if it doesn't exist. Defaults to 0.

    get-reasoning-strategy or grs		Get reasoning strategy
      	--project-id or --pid		ID of the project
    	--reasoning-strategy-id or --rsid		ID of the reasoning strategy to retrieve (optional if name is provided)
    	--reasoning-strategy-name or --rsn		Name of the reasoning strategy to retrieve (optional if ID is provided)

    create-process or cp		Create process
      	--project-id or --pid		ID of the project
    	--key or -k		Unique key for the process
    	--name or -n		Name of the process
    	--description or -d		Description of the process (optional)
    	--kb			Knowledge base in JSON format: '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' (optional)
    	--agentic-activity or --aa		Agentic activity in JSON format: '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' or '[]' to clear all activities. Multiple activities can be specified by using this option multiple times.
    	--artifact-signal or --as		Artifact signal in JSON format: '{"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}'. Multiple signals can be specified by using this option multiple times (optional).
    	--user-signal or --us		User signal in JSON format: '{"key": "signal_done", "name": "process-completed"}'. Multiple signals can be specified by using this option multiple times (optional).
    	--start-event or --se		Start event in JSON format: '{"key": "artifact.upload.1", "name": "artifact.upload"}' (optional)
    	--end-event or --ee		End event in JSON format: '{"key": "end", "name": "Done"}' (optional)
    	--sequence-flow or --sf		Sequence flow in JSON format: '{"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"}'. Multiple flows can be specified by using this option multiple times (optional).
    	--automatic-publish or --ap		Define if process must be published after being created. 0: Create as draft. 1: Create and publish. Defaults to 0.

    update-process or up		Update process
      	--project-id or --pid		ID of the project
    	--process-id or --pid		ID of the process to update (optional if name is provided)
    	--name or -n		Name of the process to update (optional if process_id is provided)
    	--key or -k		Unique key for the process (optional for update)
    	--description or -d		Description of the process (optional for update)
    	--kb			Knowledge base in JSON format: '{"name": "basic-sample", "artifactTypeName": ["sample-artifact"]}' (optional for update)
    	--agentic-activity or --aa		Agentic activity in JSON format: '{"key": "activityOne", "name": "First Step", "taskName": "basic-task", "agentName": "sample-translator", "agentRevisionId": 0}' or '[]' to clear all activities. Multiple activities can be specified by using this option multiple times (optional for update).
    	--artifact-signal or --as		Artifact signal in JSON format: '{"key": "artifact.upload.1", "name": "artifact.upload", "handlingType": "C", "artifactTypeName": ["sample-artifact"]}'. Multiple signals can be specified by using this option multiple times (optional for update).
    	--user-signal or --us		User signal in JSON format: '{"key": "signal_done", "name": "process-completed"}'. Multiple signals can be specified by using this option multiple times (optional for update).
    	--start-event or --se		Start event in JSON format: '{"key": "artifact.upload.1", "name": "artifact.upload"}' (optional for update)
    	--end-event or --ee		End event in JSON format: '{"key": "end", "name": "Done"}' (optional for update)
    	--sequence-flow or --sf		Sequence flow in JSON format: '{"key": "step1", "sourceKey": "artifact.upload.1", "targetKey": "activityOne"}'. Multiple flows can be specified by using this option multiple times (optional for update).
    	--automatic-publish or --ap		Define if process must be published after being updated. 0: Update as draft. 1: Update and publish. Defaults to 0.
    	--upsert			Define if process must be created if it doesn't exist. 0: Update only if it exists. 1: Insert if it doesn't exist. Defaults to 0.

    get-process or gp		Get process
      	--project-id or --pid		ID of the project
    	--process-id or --pid		ID of the process to retrieve (optional if process_name is provided)
    	--process-name or --pn		Name of the process to retrieve (optional if process_id is provided)
    	--revision or -r		Revision of the process to retrieve. Defaults to '0' (latest revision).
    	--version or -v		Version of the process to retrieve. Defaults to 0 (latest version).
    	--allow-drafts or --ad		Whether to include draft processes in the retrieval. Defaults to 1 (True).

    list-processes or lp		List processes
      	--project-id or --pid		ID of the project
    	--id			ID of the process to filter by (optional)
    	--name or -n		Name of the process to filter by (optional)
    	--status or -s		Status of the processes to filter by (e.g., 'active', 'inactive') (optional)
    	--start			Starting index for pagination. Defaults to '0'.
    	--count			Number of processes to retrieve. Defaults to '100'.
    	--allow-draft or --ad		Whether to include draft processes in the list. Defaults to 1 (True).

    list-processes-instances or lpi		List processes instances
      	--project-id or --pid		ID of the project
    	--process-id or --pid		ID of the process to list instances for
    	--is-active or --ia		Whether to list only active process instances. Defaults to 1 (True).
    	--start			Starting index for pagination. Defaults to '0'.
    	--count			Number of process instances to retrieve. Defaults to '10'.

    delete-process or dp		Delete process
      	--project-id or --pid		ID of the project
    	--process-id or --pid		ID of the process to delete (optional if process_name is provided)
    	--process-name or --pn		Name of the process to delete (optional if process_id is provided)

    publish-process-revision or ppr		Publish process revision
      	--project-id or --pid		ID of the project
    	--process-id or --pid		ID of the process to publish (optional if process_name is provided)
    	--process-name or --pn		Name of the process to publish (optional if process_id is provided)
    	--revision or -r		Revision of the process to publish

    create-task or ctsk		Create task
      	--project-id or --pid		ID of the project
    	--name or -n		Name of the task (required, must be unique within the project, no ':' or '/')
    	--description or -d		Description of what the task does (optional)
    	--title-template or --tt		Title template for task instances (optional, e.g., 'specs for {{issue}}')
    	--id			Custom ID for the task (optional, used instead of system-assigned ID)
    	--prompt-data or --pd		Prompt configuration as JSON (optional, e.g., '{"instructions": "Do this", "inputs": ["x"]}')
    	--artifact-types or --at		Artifact types as JSON array (optional, e.g., '[{"name": "doc", "description": "Docs", "isRequired": true, "usageType": "output", "artifactVariableKey": "doc_prefix"}]')
    	--automatic-publish or --ap		Define if task must be published after creation. 0: Create as draft. 1: Create and publish. Defaults to 0.

    get-task or gtsk		Get task
      	--project-id or --pid		ID of the project
    	--task-id or --tid		ID of the task to retrieve
    	--task-name or --tn		Name of the task to retrieve (optional if task_id is provided)

    list-tasks or ltsk		List tasks
      	--project-id or --pid		ID of the project
    	--id			ID of the task to filter by (optional)
    	--start			Starting index for pagination. Defaults to '0'.
    	--count			Number of tasks to retrieve. Defaults to '100'.
    	--allow-drafts or --ad		Whether to include draft tasks in the list. Defaults to 1 (True).

    update-task or utsk		Update task
      	--project-id or --pid		ID of the project
    	--task-id or --tid		ID of the task to update
    	--name or -n		Updated name of the task (optional, must be unique within the project, no ':' or '/' if provided)
    	--description or -d		Updated description of what the task does (optional)
    	--title-template or --tt		Updated title template for task instances (optional, e.g., 'specs for {{issue}}')
    	--id			Custom ID for the task (optional, used in upsert mode if creating a new task)
    	--prompt-data or --pd		Updated prompt configuration as JSON (optional, e.g., '{"instructions": "Do this", "inputs": ["x"]}')
    	--artifact-types or --at		Updated artifact types as JSON array (optional, e.g., '[{"name": "doc", "description": "Docs", "isRequired": true, "usageType": "output", "artifactVariableKey": "doc_prefix"}]')
    	--automatic-publish or --ap		Define if task must be published after update. 0: Update as draft. 1: Update and publish. Defaults to 0.
    	--upsert			Define if task must be created if it doesn't exist. 0: Update only if exists. 1: Insert if doesn't exist. Defaults to 0.

    delete-task or dtsk		Delete task
      	--project-id or --pid		ID of the project
    	--task-id or --tid		ID of the task to delete
    	--task-name or --tn		Name of the task to delete (optional if task_id is provided)

    publish-task-revision or ptskr		Publish task revision
      	--project-id or --pid		ID of the project
    	--task-id or --tid		ID of the task to publish
    	--task-name or --tn		Name of the task to publish (optional if task_id is provided)
    	--revision or -r		Revision of the task to publish

    start-instance or si		Start process instance
      	--project-id or --pid		ID of the project
    	--process-name or --pn		Name of the process to start an instance for
    	--subject or -s		Subject of the process instance (optional)
    	--variables or -v		Variables for the process instance in JSON list format: '[{"key": "location", "value": "Paris"}]' (optional)

    abort-instance or ai		Abort process instance
      	--project-id or --pid		ID of the project
    	--instance-id or --iid		ID of the instance to abort

    get-instance or gi		Get process instance
      	--project-id or --pid		ID of the project
    	--instance-id or --iid		ID of the instance to retrieve

    get-instance-history or gih		Get process instance history
      	--project-id or --pid		ID of the project
    	--instance-id or --iid		ID of the instance to retrieve history for

    get-thread-information or gti		Get thread information
      	--project-id or --pid		ID of the project
    	--thread-id or --tid		ID of the thread to retrieve information for

    send-user-signal or sus		Send user signal to process instance
      	--project-id or --pid		ID of the project
    	--instance-id or --iid		ID of the instance to send the signal to
    	--signal-name or --sn		Name of the user signal to send (e.g., 'approval')

    create-kb or ckb		Create knowledge base
      	--project-id or --pid		ID of the project
    	--name or -n		Name of the knowledge base
    	--artifacts or -a		List of artifact names in JSON format: '["artifact1", "artifact2"]'. Optional.
    	--metadata or -m		List of metadata fields in JSON format: '["meta1", "meta2"]'. Optional.

    get-kb or gkb		Get knowledge base
      	--project-id or --pid		ID of the project
    	--kb-id or --kid		ID of the knowledge base to retrieve (optional if kb_name is provided)
    	--kb-name or --kn		Name of the knowledge base to retrieve (optional if kb_id is provided)

    list-kbs or lkb		List knowledge bases
      	--project-id or --pid		ID of the project
    	--name or -n		Name of the knowledge base to filter by (optional)
    	--start			Starting index for pagination. Defaults to '0'.
    	--count			Number of knowledge bases to retrieve. Defaults to '100'.

    delete-kb or dkb		Delete knowledge base
      	--project-id or --pid		ID of the project
    	--kb-id or --kid		ID of the knowledge base to delete (optional if kb_name is provided)
    	--kb-name or --kn		Name of the knowledge base to delete (optional if kb_id is provided)

    list-jobs or lj		List runtime jobs
      	--project-id or --pid		ID of the project
    	--start or -s		Starting index for pagination. Defaults to '0'.
    	--count or -c		Number of jobs to retrieve. Defaults to '100'.
    	--topic			Topic of the jobs to filter by (optional).
    	--token or -t		Token of the jobs to filter by (optional).
    	--name or -n		Name of the jobs to filter by (optional).

GEAI CLI - AI LAB - SPEC
------------------------


SYNOPSIS
    geai spec <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai spec is a command from geai cli utility, developed to load components to the AI Lab in GEAI from json specifications.

    The options are as follows:
    help or h			Display help text

    load-agent or la		Load agent from JSON specification
      	--project-id or --pid		ID of the project
    	--file or -f		Path to the file containing agent definition in JSON format.
    	--automatic-publish or --ap		Define if reasoning strategy must be published besides being created. 0: Create as draft. 1: Create and publish.

    load-tool or lt		Load tool from JSON specification
      	--project-id or --pid		ID of the project
    	--file or -f		Path to the file containing tool definition in JSON format.
    	--automatic-publish or --ap		Define if tool must be published besides being created. 0: Create as draft. 1: Create and publish.

    load-task			Load task from JSON specification
      	--project-id or --pid		ID of the project
    	--file or -f		Path to the file containing task definition in JSON format.
    	--automatic-publish or --ap		Define if task must be published besides being created. 0: Create as draft. 1: Create and publish.

    load-agentic-process or lap		Load agentic process from JSON specification
      	--project-id or --pid		ID of the project
    	--file or -f		Path to the file containing agentic process definition in JSON format.
    	--automatic-publish or --ap		Define if agentic process must be published besides being created. 0: Create as draft. 1: Create and publish.

GEAI CLI - MIGRATE
------------------
SYNOPSIS
    geai migrate <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai migrate is a command from geai cli utility, developed to migrate data between organizations and instances of GEAI.

    The options are as follows:
    help or h			Display help text

    clone-project		Clone project from instance
      	--from-api-key or --fak		API key for the source instance
    	--from-project-id or --fpid		ID of the source project to migrate from
    	--from-instance or --fi		URL from the source instance to migrate from
    	--to-api-key or --tak		API key for the destination instance. If not specified, the same instance's API key will be used
    	--to-project-name or --tpn		Name of the destination project to migrate to
    	--to-instance or --ti		URL from the destination instance to migrate to. If not specified, the same instance's URL will be used
    	--admin-email or --ae		Email from destination project's administrator

    clone-agent		Clone agentt from instance
      	--from-api-key or --fak		API key for the source instance
    	--from-project-id or --fpid		ID of the source project to migrate from
    	--from-instance or --fi		URL from the source instance to migrate from
    	--to-api-key or --tak		API key for the destination instance. If not specified, the same instance's API key will be used
    	--to-project-id or --tpid		ID of the destination project to migrate to
    	--to-instance or --ti		URL from the destination instance to migrate to. If not specified, the same instance's URL will be used
    	--agent-id or --aid		Unique identifier from the agent to be migrated

    clone-tool			Clone tool from instance
      	--from-api-key or --fak		API key for the source instance
    	--from-project-id or --fpid		ID of the source project to migrate from
    	--from-instance or --fi		URL from the source instance to migrate from
    	--to-api-key or --tak		API key for the destination instance. If not specified, the same instance's API key will be used
    	--to-project-id or --tpid		ID of the destination project to migrate to
    	--to-instance or --ti		URL from the destination instance to migrate to. If not specified, the same instance's URL will be used
    	--tool-id or --tid		Unique identifier from the tool to be migrated

    clone-process		Clone process from instance
      	--from-api-key or --fak		API key for the source instance
    	--from-project-id or --fpid		ID of the source project to migrate from
    	--from-instance or --fi		URL from the source instance to migrate from
    	--to-api-key or --tak		API key for the destination instance. If not specified, the same instance's API key will be used
    	--to-project-id or --tpid		ID of the destination project to migrate to
    	--to-instance or --ti		URL from the destination instance to migrate to. If not specified, the same instance's URL will be used
    	--process-id or --pid		Unique identifier from the process to be migrated


PyGEAI Debugger
Overview
geai-dbg is a command-line debugger for the geai CLI tool, part of the pygeai package. It allows developers to pause execution at specified points (breakpoints) in the geai codebase, inspect local variables, execute arbitrary Python code in the current context, and control program flow interactively. Breakpoints can be set by module or function name, providing flexibility for debugging complex CLI workflows.

The debugger is invoked by running the geai-dbg command, typically with the same arguments as the geai CLI. It pauses execution at predefined or user-specified breakpoints, presenting an interactive prompt (geai-dbg) for issuing commands.

Installation and Setup
geai-dbg is included in the pygeai package. Ensure pygeai is installed in your Python environment:

pip install pygeai
No additional setup is required. The debugger script (debugger.py) is located in the pygeai.dbg module and can be invoked via the geai-dbg command.

Usage
To use geai-dbg, run it with the same arguments you would pass to the geai CLI. For example:

geai-dbg ail lrs
This command runs the geai CLI with the arguments ail lrs under the debugger. The debugger automatically sets a breakpoint at the main function in the pygeai.cli.geai module, pausing execution before the geai command processes the arguments.

Upon hitting a breakpoint, the debugger displays:

The location (module and function) where execution is paused.

Local variables in the current context.

An interactive prompt (geai-dbg) for entering commands.

You can then inspect variables, add breakpoints, execute code, or control execution using the available commands.

Commands
At the (geai-dbg) prompt, the following commands are available:

continue, c
Resume execution until the next breakpoint is hit or the program completes.

quit, q, Ctrl+D
Exit the debugger, terminating the program with a clean exit status (0).

run, r
Run the program to completion, disabling all breakpoints and skipping further pauses.

breakpoint-module, bm
Add a breakpoint for a specific module. Prompts for a module name (e.g., pygeai.cli.commands). Press Enter to set a wildcard breakpoint (any module).

breakpoint-function, bf
Add a breakpoint for a specific function, optionally scoped to a module. Prompts for a function name (e.g., main) and an optional module name. Press Enter for wildcards (any function or module).

list-modules, lm
List all loaded modules starting with pygeai, useful for identifying valid module names for breakpoints.

help, h
Display a list of available commands and their descriptions.

<Python code>
Execute arbitrary Python code in the current context. For example, print(sys.argv) displays the command-line arguments. Errors are caught and logged without crashing the debugger.

Ctrl+C
Interrupt the current command input and resume execution, equivalent to continue.

Examples
Example 1: Debugging a geai Command

Suppose you want to debug the geai ail lrs command to inspect its execution. Run:

geai-dbg ail lrs
Output:

2025-05-12 15:04:57,263 - geai - INFO - GEAI debugger started.
2025-05-12 15:04:57,263 - geai - INFO - geai module: pygeai.cli.geai
2025-05-12 15:04:57,263 - geai - INFO - Breakpoint added: pygeai.cli.geai:main
2025-05-12 15:04:57,264 - geai - INFO - Setting trace and running geai
2025-05-12 15:04:57,264 - geai - INFO - Breakpoint hit at pygeai.cli.geai.main
2025-05-12 15:04:57,264 - geai - INFO - Local variables: {}

Paused at pygeai.cli.geai.main
Enter commands to execute in the current context (type 'continue' to resume, 'quit' to exit, 'help' to display available commands):
(geai-dbg)
List available commands:

(geai-dbg) h
Available commands:
  continue, c: Resume execution until next breakpoint
  quit, q: Exit the debugger
  run, r: Run program without further pauses
  breakpoint-module, bm: Add a module breakpoint
  breakpoint-function, bf: Add a function breakpoint
  list-modules, lm: List available modules
  <Python code>: Execute arbitrary Python code in the current context
List modules to find valid breakpoint targets:

(geai-dbg) lm
2025-05-12 15:05:03,595 - geai - INFO - Listing available modules
Available modules: ['pygeai', 'pygeai.dbg', 'pygeai.cli', ...]
Continue to the next breakpoint (e.g., another hit on main in a different context):

(geai-dbg) c
2025-05-12 15:05:18,424 - geai - DEBUG - Alias: default
2025-05-12 15:05:18,424 - geai - DEBUG - Base URL: api.beta.saia.ai/
2025-05-12 15:05:18,425 - geai - INFO - Breakpoint hit at pygeai.cli.geai.main
2025-05-12 15:05:18,425 - geai - INFO - Local variables: {'self': <pygeai.cli.geai.CLIDriver object at 0x100f34080>, 'args': None}

Paused at pygeai.cli.geai.main
Enter commands to execute in the current context (type 'continue' to resume, 'quit' to exit, 'help' to display available commands):
(geai-dbg)
Run the program to completion:

(geai-dbg) run
2025-05-12 15:05:21,221 - geai - INFO - Running program without further pauses.
2025-05-12 15:05:21,222 - geai - DEBUG - Running geai with: /Users/alejandro.trinidad/globant/genexus/sdk/venv/bin/geai-dbg ail lrs
2025-05-12 15:05:21,222 - geai - DEBUG - Listing reasoning strategies
[geai output listing reasoning strategies]
2025-05-12 15:05:21,878 - geai - INFO - Cleaning up trace
Example 2: Inspecting Variables

At a breakpoint, inspect command-line arguments:

(geai-dbg) print(sys.argv)
2025-05-12 15:05:21,300 - geai - INFO - Executing interactive command: print(sys.argv)
['/Users/alejandro.trinidad/globant/genexus/sdk/venv/bin/geai-dbg', 'ail', 'lrs']
Example 3: Adding a Breakpoint

Add a breakpoint for the pygeai.cli.commands module:

(geai-dbg) bm
2025-05-12 15:05:21,400 - geai - INFO - Adding breakpoint on module
(geai-dbg) Enter module name (or press Enter for any module): pygeai.cli.commands
2025-05-12 15:05:21,500 - geai - INFO - Breakpoint added: pygeai.cli.commands:*
Notes
Ctrl+D and Ctrl+C: - Pressing Ctrl+D at the (geai-dbg) prompt terminates the debugger gracefully, logging “Debugger terminated by user (EOF).” and exiting with status 0. - Pressing Ctrl+C resumes execution, equivalent to the continue command.

Python Code Execution: - Arbitrary Python code executed at the prompt runs in the context of the paused frame, with access to local and global variables. Use with caution, as it can modify program state.

Breakpoint Wildcards: - Use bm or bf with empty inputs to set wildcard breakpoints, pausing on any module or function. This is useful for exploratory debugging.

Logging: - The debugger logs to stdout with timestamps, including breakpoint hits, local variables, and command execution. Errors in Python code execution are logged without crashing the debugger.

For issues or feature requests, contact the pygeai development team.

See also

geai CLI documentation for details on the underlying command-line tool.

Python’s sys.settrace documentation for technical details on the debugging mechanism.
"""

agent_id = "79c78da6-3d11-4fde-ac01-05bbc0817fd0"   # Existing Agent

agent = Agent(
    id=agent_id,
    status="active",
    name="PyGEAI CLI Expert",
    access_scope="public",
    public_name="com.globant.geai.pygeai_cli_expert",
    job_description="Assists with PyGEAI CLI queries",
    avatar_image="https://www.shareicon.net/data/128x128/2016/11/09/851447_logo_512x512.png",
    description="Agent that provides guidance on using the PyGEAI command-line interface, including commands, subcommands, options, and error handling, based on comprehensive CLI documentation.",
    is_draft=False,
    is_readonly=False,
    revision=1,
    version=None,
    agent_data=AgentData(
        prompt=Prompt(
            instructions=f"""\
You are an expert assistant for the PyGEAI CLI, designed to answer queries about its commands, subcommands, options, and error codes. Use the following GEAI CLI documentation as your knowledge base to provide accurate, clear, and concise responses in plain text. Tailor the response tone based on the 'style' input (formal or informal). If the query is unclear, ask for clarification. Provide examples where relevant. If an error code is mentioned, explain its meaning and suggest solutions.
IMPORTANT: Answers should be short, clear and concise.

The documentation is provided below for reference:

{GEAI_CLI_HELP}

Respond with a detailed answer to the query and a brief summary. Ensure responses are accurate and aligned with the documentation.
            """,
            inputs=["query", "style"],
            outputs=[
                PromptOutput(key="response", description="Answer to the user's query about PyGEAI CLI, in plain text."),
            ],
            examples=[
                PromptExample(
                    input_data="How do I create a new project in PyGEAI CLI? [formal]",
                    output='Use `geai organization create-project` with required flags like --name and --email.'
                ),
                PromptExample(
                    input_data="What does error code 401 mean? [informal]",
                    output='Error code 401 in PyGEAI CLI means \'Unauthorized\'. It happens when your API key or token is missing or invalid. Double-check your API key with `geai configure --key <your_key>` or verify your token with `geai admin validate-token`'
                ),
                PromptExample(
                    input_data="How to list all assistants in a project? [formal]",
                    output='To list all assistants in a project, use the command: `geai organization list-assistants --organization-id <org_id> --project-id <project_id>`. Example: `geai organization list-assistants --organization-id org123 --project-id proj456`. Ensure you have configured the API key using `geai configure`.'
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
    automatic_publish=True
)

if isinstance(result, Agent):
    print(f"Agent updated successfully: {agent.to_dict()}")
else:
    print("Errors:", result.errors)
