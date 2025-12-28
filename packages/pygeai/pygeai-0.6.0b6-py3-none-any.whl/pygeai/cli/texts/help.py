AUTHORS_SECTION = """
AUTHORS 
    Copyright 2026, Globant.

REPORTING BUGS
    To report any bug, request features or make any suggestions, the following email is available:
    geai-sdk@globant.com
"""


CLI_USAGE = """
geai <command> [<subcommand>] [--option] [option-arg]
"""


HELP_TEXT = f"""
GEAI CLI
--------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai <command> [<subcommand>] [--option] [option-arg]

DESCRIPTION
    geai is a cli utility that interacts with the PyGEAI SDK to handle common tasks in Globant Enterprise AI,
    such as creating organizations and projects, defining assistants, managing workflows, etc.
    
    The available subcommands are as follows:
    {{available_commands}}
    
    You can consult specific options for each command using with:
    geai <command> h
    or
    geai <command> help

ERROR CODES
Certain error descriptions can contain up to %n references specific to that error. 
These references are described with %1, %2,... ,%n.

    ErrorCode            Description    
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

{AUTHORS_SECTION}
"""

ORGANIZATION_HELP_TEXT = f"""
GEAI CLI - ORGANIZATION
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai organization <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai organization is a command from geai cli utility, developed to interact with key components of GEAI
    such as creating organizations and projects, defining assistants, managing workflows, etc.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        geai org list-projects
    lists available projects in your organization.
    
    The command:
        geai org list-projects -d full
    lists all projects with full details.
    
    The command:
        geai org create-project -n "SDKTest" -e "admin@example.com" -d "Test project for SDK"
    creates a new project with specified name, email and description.
    
    The command:
        geai org get-tokens --id <PROJECT_UUID>
    retrieves API tokens for a specific project
    
{AUTHORS_SECTION}
"""

ASSISTANT_HELP_TEXT = f"""
GEAI CLI - ASSISTANT
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai assistant <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai assistant is a command from geai cli utility, developed to interact with assistant in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        geai ast get-assistant --id <ASSISTANT_UUID>
    retrieves detailed information about a specific assistant.
    
    The command:
        geai ast create-assistant --type chat --name "MyAssistant" --prompt "You are a helpful assistant"
    creates a new assistant with the specified type, name and prompt.
    
    The command:
        geai ast chat --name "MyAssistant" --msg '[{{{{"role": "user", "content": "Hello"}}}}]'
    starts a chat session with the specified assistant
    
{AUTHORS_SECTION}
"""

RAG_ASSISTANT_HELP_TEXT = f"""
GEAI CLI - RAG ASSISTANT
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai rag <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai RAG assistant is a command from geai cli utility, developed to interact with RAG assistant in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        geai rag list-assistants
    lists all RAG assistants in the current project.
    
    The command:
        geai rag get-assistant --name "MyRAG"
    retrieves information about a specific RAG assistant.
    
    The command:
        geai rag upload-document --name "MyRAG" --file "document.pdf"
    uploads a document to a RAG assistant's knowledge base
    
{AUTHORS_SECTION}
"""

CHAT_HELP_TEXT = f"""
GEAI CLI - CHAT
----------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai chat <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai chat is a command from geai cli utility, developed to chat with assistant in GEAI.
    
    The model needs to specify an assistant_type and a specific_parameter whose format depends on that type. Its format is as follows:

    "model": "saia:<assistant_type>:<specific_parameter>"
    
    assistant_type can be:
    - agent: Identifies a Agent.
    - flow: Identifies a Flow.
    - assistant: Identifies an Assistant API, Data Analyst Assistant, Chat with Data Assistant and API Assistant.
    - search: Identifies a RAG Assistant.

    For more information, refer to the GEAI Wiki: https://wiki.genexus.com/enterprise-ai/wiki?34,Chat+API
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai chat iris
    starts an interactive chat session with Iris assistant.
    
    The command:
        geai chat agent --name "MyAgent"
    starts a chat session with a specific agent.
    
    The command:
        geai chat completion --model "saia:assistant:MyAssistant" --msg '[{{{{"role": "user", "content": "Hello"}}}}]' --stream 0
    sends a completion request to the specified assistant
    
{AUTHORS_SECTION}
"""

GAM_HELP_TEXT = f"""
GEAI CLI - GAM
----------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai gam <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai gam is a command from geai cli utility, developed to interact with GAM authentication mechanisms in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai gam get-access-token
    retrieves the current GAM access token.
    
    The command:
        geai gam get-user-info
    retrieves user information from GAM
    
{AUTHORS_SECTION}
"""

SECRETS_HELP_TEXT = f"""
GEAI CLI - SECRETS
----------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai secrets <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai secrets is a command from geai cli utility, developed to handle secrets in in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai secrets create-secret --name "API_KEY" --value "secret_value"
    creates a new secret in the secrets manager.
    
    The command:
        geai secrets list-secrets
    lists all secrets stored in the project
    
{AUTHORS_SECTION}
"""

MIGRATE_HELP_TEXT = f"""
GEAI CLI - MIGRATE
------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai migrate <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai migrate is a command from geai cli utility, developed to migrate data between organizations and instances of GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai migrate agent --agent-id "UUID" --target-project "TARGET_UUID"
    migrates an agent to a different project.
    
    The command:
        geai migrate process --process-id "UUID" --target-project "TARGET_UUID"
    migrates an agentic process to another project
    
{AUTHORS_SECTION}
"""

RERANK_HELP_TEXT = f"""
GEAI CLI - RERANK
-----------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai rerank <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai rerank is a command from geai cli utility, developed to rerank a list of document chunks based on a query in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai rerank rerank-chunks --query "search term" --documents '["doc1", "doc2"]' --model "cohere/rerank-english-v3.0"
    reranks the provided documents based on relevance to the query.
    
    The command:
        geai rerank chunks -q "my query" -d "document text" --top-n 5
    reranks chunks and returns top 5 results
    
{AUTHORS_SECTION}
"""


EMBEDDINGS_HELP_TEXT = f"""
GEAI CLI - EMBEDDINGS
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai embeddings <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai embeddings is a command from geai cli utility, developed to generate embeddings in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai emb generate -i "Help me with Globant Enterprise AI" -m "openai/text-embedding-3-small"
    generates embeddings for the provided text.
    
    The command:
        geai emb generate -i "Help me with" -i "Globant Enterprise AI" -m "openai/text-embedding-3-small" --cache 1
    generates embeddings with caching enabled for multiple inputs.
    
    The command:
        geai emb generate -i "text" -m "vertex_ai/text-embedding-004" --input-type "SEMANTIC_SIMILARITY"
    generates embeddings with a specific input type
        
{AUTHORS_SECTION}
"""

FEEDBACK_HELP_TEXT = f"""
GEAI CLI - FEEDBACK
--------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai feedback <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai feedback is a command from geai cli utility, developed to send feedback from the assistant's answers.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai feedback send --request-id "UUID" --rating 5 --comment "Great response"
    sends positive feedback for an assistant response.
    
    The command:
        geai feedback list --assistant-id "UUID"
    lists all feedback for a specific assistant
        
{AUTHORS_SECTION}
"""

EVALUATION_HELP_TEXT = f"""
GEAI CLI - EVALUATION
----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai evaluation <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai evaluation is a command from geai cli utility, developed to interact with Dataset, Plan and Result APIs from
    the Evaluation module.
    
    Dataset rows have the following structure:
        {{{{
            "dataSetRowExpectedAnswer": "This is the expected answer", 
            "dataSetRowInput": "What is the capital of France?", 
            "dataSetRowContextDocument": "", 
            "expectedSources": [
                {{{{
                    "dataSetExpectedSourceId": "UUID", 
                    "dataSetExpectedSourceName": "Source Name", 
                    "dataSetExpectedSourceValue": "Some value", 
                    "dataSetexpectedSourceExtention": "pdf"
                }}}}
                ], 
                "filterVariables": [
                {{{{
                    "dataSetMetadataType": "Type", 
                    "dataSetRowFilterKey": "key", 
                    "dataSetRowFilterOperator": "equals", 
                    "dataSetRowFilterValue": "value", 
                    "dataSetRowFilterVarId": "UUID"
                }}}}
            ]
        }}}}
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        geai evaluation create-dataset \\
            --dataset-name "MyNewDataset" \\
            --dataset-description "A dataset for testing" \\
            --dataset-type "T" \\
            --dataset-active 1 \\
            --row '[
                {{{{
                "dataSetRowExpectedAnswer": "This is the expected answer", 
                "dataSetRowInput": "What is the capital of France?", 
                "dataSetRowContextDocument": ""
                }}}}
            ]'
        
    This will create a new dataset called "MyNewDataset" with a description, type "T" (test), and one row where the expected answer is provided along with the input question.

    The command:
        geai evaluation create-dataset \\
            --dataset-name "MyNewDataset" \\
            --dataset-description "A dataset for testing" \\
            --dataset-type "T" \\
            --dataset-active 1 \\
            --row '[
                {{{{
                    "dataSetRowExpectedAnswer": "This is the expected answer", 
                    "dataSetRowInput": "What is the capital of France?", 
                    "dataSetRowContextDocument": "", 
                    "expectedSources": [
                        {{{{
                            "dataSetExpectedSourceId": "UUID", 
                            "dataSetExpectedSourceName": "Source Name", 
                            "dataSetExpectedSourceValue": "Some value", 
                            "dataSetexpectedSourceExtention": "pdf"
                        }}}}
                        ], 
                        "filterVariables": [
                        {{{{
                            "dataSetMetadataType": "Type", 
                            "dataSetRowFilterKey": "key", 
                            "dataSetRowFilterOperator": "equals", 
                            "dataSetRowFilterValue": "value", 
                            "dataSetRowFilterVarId": "UUID"
                        }}}}
                        ]
                    }}}}
                ]'

    This will create a new dataset with rows that include optional "expectedSources" and "filterVariables".

        
{AUTHORS_SECTION}
"""


ADMIN_HELP_TEXT = f"""
GEAI CLI - ADMIN
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai admin <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai admin is a command from geai cli utility, developed to interact instance of GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai admin validate-token
    validates the current API token.
    
    The command:
        geai admin list-authorized-organizations
    lists all organizations the current user has access to.
    
    The command:
        geai admin project-visibility --project-id "UUID"
    retrieves visibility settings for a specific project
    
{AUTHORS_SECTION}
"""

AUTH_HELP_TEXT = f"""
GEAI CLI - AUTH
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai auth <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai auth is a command from geai cli utility, developed to manage authentication access tokens instance of GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai auth get-access-token
    retrieves an OAuth2 access token for authentication.
    
    The command:
        geai auth get-user-info
    retrieves the current user's profile information
    
{AUTHORS_SECTION}
"""


LLM_HELP_TEXT = f"""
GEAI CLI - LLM
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai llm <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai llm is a command from geai cli utility, developed to retrieve information about available models and providers 
    in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai llm list-models
    lists all available LLM models in GEAI.
    
    The command:
        geai llm list-providers
    lists all available LLM providers
    
{AUTHORS_SECTION}
"""

FILES_HELP_TEXT = f"""
GEAI CLI - FILES
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai files <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai files is a command from geai cli utility, developed to interact with files in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai files upload --file "document.pdf" --purpose "assistants"
    uploads a file to GEAI for use with assistants.
    
    The command:
        geai files list
    lists all uploaded files in the project
    
{AUTHORS_SECTION}
"""

USAGE_LIMIT_HELP_TEXT = f"""
GEAI CLI - USAGE LIMITS
-----------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai usage-limit <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai usage-limits is a command from geai cli utility, developed to manager usage limits in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai -a myorg usage-limit set-organization-limit --organization <ORG_UUID> --subscription-type Monthly --usage-unit Cost --soft-limit 1000 --hard-limit 5000 --renewal-status Renewable
    sets usage limits for an organization.
    
    The command:
        geai -a myorg usage-limit get-latest-org-lim --organization <ORG_UUID>
    retrieves the latest usage limit for an organization.
    
    The command:
        geai -a myorg usage-limit up-org-lim --organization <ORG_UUID> --lid <LIMIT_UUID> --renewal-status Renewable --soft-limit 5000 --hard-limit 8000
    updates an existing usage limit for an organization
    
{AUTHORS_SECTION}
"""

AI_LAB_HELP_TEXT = f"""
GEAI CLI - AI LAB
-----------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai ai-lab <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai ai-lab is a command from geai cli utility, developed to interact with AI Lab in GEAI.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai ai-lab create-agent --name "MyAgent" --instructions "You are a helpful agent"
    creates a new agent in the AI Lab.
    
    The command:
        geai ai-lab list-agents
    lists all agents in the current project.
    
    The command:
        geai ai-lab create-process --name "MyProcess" --description "Automated workflow"
    creates a new agentic process
    
{AUTHORS_SECTION}
"""

SPEC_HELP_TEXT = f"""
GEAI CLI - AI LAB - SPEC
------------------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai spec <subcommand> --[flag] [flag_arg]

DESCRIPTION
    geai spec is a command from geai cli utility, developed to load components to the AI Lab in GEAI from json specifications.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai spec load-agent --file "agent_spec.json"
    loads an agent from a JSON specification file.
    
    The command:
        geai spec load-process --file "process_spec.json"
    loads an agentic process from a JSON specification file
    
{AUTHORS_SECTION}
"""

DOCS_HELP_TEXT = f"""
GEAI CLI - DOCS
---------------

NAME
    geai - Command Line Interface for Globant Enterprise AI

SYNOPSIS
    geai docs <subcommand>

DESCRIPTION
    geai docs is a command from geai cli utility to view the PyGEAI SDK documentation.
    
    The options are as follows:
    {{available_commands}}
    
EXAMPLES
    The command:
        
        geai docs
    opens the HTML documentation in your web browser.
    
    If documentation dependencies are not installed, you will be prompted to install them.
    If the documentation is not built, it will be automatically generated.
    
{AUTHORS_SECTION}
"""
