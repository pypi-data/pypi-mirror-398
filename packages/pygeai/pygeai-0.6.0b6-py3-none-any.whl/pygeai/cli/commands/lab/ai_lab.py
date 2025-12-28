import json

from pygeai import logger
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.common import get_boolean_value
from pygeai.cli.commands.lab.common import get_agent_data_prompt_inputs, get_agent_data_prompt_outputs, \
    get_agent_data_prompt_examples, get_tool_parameters
from pygeai.cli.texts.help import AI_LAB_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console
from pygeai.cli.commands.lab.options import PROJECT_ID_OPTION
from pygeai.lab.agents.clients import AgentClient
from pygeai.lab.processes.clients import AgenticProcessClient
from pygeai.lab.strategies.clients import ReasoningStrategyClient
from pygeai.lab.tools.clients import ToolClient
from pygeai.lab.constants import VALID_SCOPES


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(ai_lab_commands, AI_LAB_HELP_TEXT)
    Console.write_stdout(help_text)


def list_agents(option_list: list):
    project_id = None
    status = ""
    start = ""
    count = ""
    access_scope = "public"
    allow_drafts = True
    allow_external = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "status":
            status = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)
        if option_flag.name == "allow_external":
            allow_external = get_boolean_value(option_arg)

    client = AgentClient(project_id=project_id)
    result = client.list_agents(
        status=status,
        start=start,
        count=count,
        access_scope=access_scope,
        allow_drafts=allow_drafts,
        allow_external=allow_external,
    )
    Console.write_stdout(f"Agent list: \n{result}")


list_agents_options = [
    PROJECT_ID_OPTION,
    Option(
        "status",
        ["--status"],
        "Status of the agents to filter by. Defaults to an empty string (no filtering).",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to an empty string (no offset).",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of agents to retrieve. Defaults to an empty string (no limit).",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope"],
        'Access scope of the agents, either "public" or "private". Defaults to "public".',
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts"],
        "Whether to include draft agents. Defaults to 1 (True).",
        True
    ),
    Option(
        "allow_external",
        ["--allow-external"],
        "Whether to include external agents. Defaults to 0 (False).",
        True
    )
]


def create_agent(option_list: list):
    project_id = None
    name = None
    access_scope = None
    public_name = None
    job_description = None
    avatar_image = None
    description = None
    agent_data_prompt_instructions = None
    agent_data_prompt_inputs = list()
    agent_data_prompt_outputs = list()
    agent_data_prompt_examples = list()
    agent_data_llm_max_tokens = None
    agent_data_llm_timeout = None
    agent_data_llm_temperature = None
    agent_data_llm_top_k = None
    agent_data_llm_top_p = None
    agent_data_strategy_name = None
    agent_data_model_name = None
    agent_data_resource_pools = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "public_name":
            public_name = option_arg
        if option_flag.name == "job_description":
            job_description = option_arg
        if option_flag.name == "avatar_image":
            avatar_image = option_arg
        if option_flag.name == "description":
            description = option_arg

        if option_flag.name == "agent_data_prompt_instructions":
            agent_data_prompt_instructions = option_arg
        if option_flag.name == "agent_data_prompt_input":

            if "[" not in option_arg:
                agent_data_prompt_inputs.append(option_arg)
            else:
                try:
                    input_json = json.loads(option_arg)
                    if not isinstance(input_json, list):
                        raise ValueError

                    agent_data_prompt_inputs = input_json
                except Exception as e:
                    raise WrongArgumentError(
                        "Inputs must be a list of strings: '[\"input_name\", \"another_input\"]'. "
                        "Each element in the list must be a string representing an input name."
                    )
        if option_flag.name == "agent_data_prompt_output":
            try:
                output_json = json.loads(option_arg)
                if isinstance(output_json, list):
                    agent_data_prompt_outputs = output_json
                elif isinstance(output_json, dict):
                    agent_data_prompt_outputs.append(output_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each output must be in JSON format: '{\"key\": \"output_key\", \"description\": \"description of the output\"}' "
                    "It must be a dictionary or a list of dictionaries. Each dictionary must contain 'key' and 'description'."
                )

        if option_flag.name == "agent_data_prompt_example":
            try:
                examples_json = json.loads(option_arg)
                if isinstance(examples_json, list):
                    agent_data_prompt_examples = examples_json
                elif isinstance(examples_json, dict):
                    agent_data_prompt_examples.append(examples_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each example must be in JSON format: '{\"inputData\": \"example input\", \"output\": \"expected output in JSON string format\"}' "
                    "It must be a dictionary or a list of dictionaries. Each dictionary must contain 'inputData' and 'output'."
                )

        if option_flag.name == "agent_data_llm_max_tokens":
            agent_data_llm_max_tokens = option_arg
        if option_flag.name == "agent_data_llm_timeout":
            agent_data_llm_timeout = option_arg
        if option_flag.name == "agent_data_llm_temperature":
            agent_data_llm_temperature = option_arg
        if option_flag.name == "agent_data_llm_top_k":
            agent_data_llm_top_k = option_arg
        if option_flag.name == "agent_data_llm_top_p":
            agent_data_llm_top_p = option_arg
        if option_flag.name == "agent_data_strategy_name":
            agent_data_strategy_name = option_arg
        if option_flag.name == "agent_data_model_name":
            agent_data_model_name = option_arg
        if option_flag.name == "agent_data_resource_pools":
            try:
                pools_json = json.loads(option_arg)
                if not isinstance(pools_json, list):
                    raise ValueError
                agent_data_resource_pools = pools_json
            except Exception as e:
                raise WrongArgumentError(
                    "Resource pools must be in JSON format: '[{\"name\": \"pool_name\", \"tools\": [{\"name\": \"tool_name\", \"revision\": int}], \"agents\": [{\"name\": \"agent_name\", \"revision\": int}]}]' "
                    "It must be a list of dictionaries. Each dictionary must contain 'name' and optional 'tools' and 'agents' lists."
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)

    if not (name and access_scope and public_name):
        raise MissingRequirementException("Cannot create assistant without specifying name, access scope and public name")

    prompt_inputs = get_agent_data_prompt_inputs(agent_data_prompt_inputs)
    prompt_outputs = get_agent_data_prompt_outputs(agent_data_prompt_outputs)
    prompt_examples = get_agent_data_prompt_examples(agent_data_prompt_examples)

    agent_data_prompt = {
        "instructions": agent_data_prompt_instructions,
        "inputs": prompt_inputs,
        "outputs": prompt_outputs,
        "examples": prompt_examples
    }
    agent_data_llm_config = {
        "maxTokens": agent_data_llm_max_tokens,
        "timeout": agent_data_llm_timeout,
        "sampling": {
            "temperature": agent_data_llm_temperature,
            "topK": agent_data_llm_top_k,
            "topP": agent_data_llm_top_p,
        }
    }
    agent_data_models = [
        {"name": agent_data_model_name}
    ]

    client = AgentClient(project_id=project_id)
    result = client.create_agent(
        name=name,
        access_scope=access_scope,
        public_name=public_name,
        job_description=job_description,
        avatar_image=avatar_image,
        description=description,
        agent_data_prompt=agent_data_prompt,
        agent_data_llm_config=agent_data_llm_config,
        agent_data_strategy_name=agent_data_strategy_name,
        agent_data_models=agent_data_models,
        agent_data_resource_pools=agent_data_resource_pools,
        automatic_publish=automatic_publish
    )
    Console.write_stdout(f"New agent detail: \n{result}")


create_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "name",
        ["--name", "-n"],
        "Name of the agent, must be unique within the project and exclude ':' or '/'",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Access scope of the agent, either 'public' or 'private' (defaults to 'private')",
        True
    ),
    Option(
        "public_name",
        ["--public-name", "--pn"],
        "Public name of the agent, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.example.my-agent') with only alphanumeric characters, periods, dashes, or underscores",
        True
    ),
    Option(
        "job_description",
        ["--job-description", "--jd"],
        "Description of the agent's role",
        True
    ),
    Option(
        "avatar_image",
        ["--avatar-image", "--aimg"],
        "URL for the agent's avatar image",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Detailed description of the agent's purpose",
        True
    ),
    Option(
        "agent_data_prompt_instructions",
        ["--agent-data-prompt-instructions", "--adp-inst"],
        "Instructions defining what the agent does and how, required for publication if context is not provided",
        True
    ),
    Option(
        "agent_data_prompt_input",
        ["--agent-data-prompt-input", "--adp-input"],
        "Agent Data prompt input: "
        "Prompt input as a list of strings (e.g., '[\"input1\", \"input2\"]') or multiple single strings via repeated flags, each representing an input name",
        True
    ),
    Option(
        "agent_data_prompt_output",
        ["--agent-data-prompt-output", "--adp-out"],
        "Prompt output in JSON format (e.g., '[{\"key\": \"output_key\", \"description\": \"output description\"}]'), as a dictionary or list of dictionaries with 'key' and 'description' fields",
        True
    ),
    Option(
        "agent_data_prompt_example",
        ["--agent-data-prompt-example", "--adp-ex"],
        "Prompt example in JSON format (e.g., '[{\"inputData\": \"example input\", \"output\": \"example output\"}]'), as a dictionary or list of dictionaries with 'inputData' and 'output' fields",
        True
    ),
    Option(
        "agent_data_llm_max_tokens",
        ["--agent-data-llm-max-tokens", "--adl-max-tokens"],
        "Maximum number of tokens the LLM can generate, used to control costs",
        True
    ),
    Option(
        "agent_data_llm_timeout",
        ["--agent-data-llm-timeout", "--adl-timeout"],
        "Timeout in seconds for LLM responses",
        True
    ),
    Option(
        "agent_data_llm_temperature",
        ["--agent-data-llm-temperature", "--adl-temperature"],
        "Sampling temperature for LLM (0.0 to 1.0), lower values for focused responses, higher for more random outputs",
        True
    ),
    Option(
        "agent_data_llm_top_k",
        ["--agent-data-llm-top-k", "--adl-top-k"],
        "TopK sampling parameter for LLM (currently unused)",
        True
    ),
    Option(
        "agent_data_llm_top_p",
        ["--agent-data-llm-top-p", "--adl-top-p"],
        "TopP sampling parameter for LLM (currently unused)",
        True
    ),
    Option(
        "agent_data_strategy_name",
        ["--agent-data-strategy-name", "--strategy-name"],
        "Name of the reasoning strategy to use",
        True
    ),
    Option(
        "agent_data_model_name",
        ["--agent-data-model-name", "--adm-name"],
        "Name of the LLM model (e.g., 'gpt-4o' or 'openai/gpt-4o'), at least one valid model required for publication",
        True
    ),
    Option(
        "agent_data_resource_pools",
        ["--agent-data-resource-pools", "--adr-pools"],
        "Resource pools in JSON format (e.g., '[{\"name\": \"pool_name\", \"tools\": [{\"name\": \"tool_name\", \"revision\": int}], \"agents\": [{\"name\": \"agent_name\", \"revision\": int}]}]'), "
        "as a list of dictionaries with 'name' (required) and optional 'tools' and 'agents' lists",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Whether to publish the agent after creation (0: create as draft, 1: create and publish)",
        True
    ),
]


def get_agent(option_list: list):
    project_id = None
    agent_id = None
    revision = 0
    version = 0
    allow_drafts = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg
        if option_flag.name == "revision":
            revision = option_arg
        if option_flag.name == "version":
            version = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)

    if not agent_id:
        raise MissingRequirementException("Agent ID must be specified.")

    client = AgentClient(project_id=project_id)
    result = client.get_agent(
        agent_id=agent_id,
        revision=revision,
        version=version,
        allow_drafts=allow_drafts,
    )
    Console.write_stdout(f"Agent detail: \n{result}")


get_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "ID of the agent to retrieve",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of agent.",
        True
    ),
    Option(
        "version",
        ["--version", "-v"],
        'Version of agent.',
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts"],
        "Whether to include draft agents. Defaults to 1 (True).",
        True
    ),
]


def export_agent(option_list: list):
    project_id = None
    agent_id = None
    file = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg
        if option_flag.name == "file":
            file = option_arg

    if not agent_id:
        raise MissingRequirementException("Agent ID must be specified.")

    client = AgentClient(project_id=project_id)
    result = client.export_agent(
        agent_id=agent_id,
    )
    if file:
        try:
            data = json.loads(result) if isinstance(result, str) else result
            with open(file, "w") as f:
                json.dump(data, f, indent=4)
            Console.write_stdout(f"Result from API saved to {file}.")
        except json.JSONDecodeError as e:
            logger.error(f"Result from API endpoint is not in JSON format: {e}")
            Console.write_stderr(f"Result from API endpoint is not in JSON format.")
    else:
        Console.write_stdout(f"Agent spec: \n{result}")



export_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "ID of the agent to retrieve",
        True
    ),
    Option(
        "file",
        ["--file", "-f"],
        "File path to save export specification for agent",
        True
    ),
]


def import_agent(option_list: list):
    project_id = None
    file = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "file":
            file = option_arg


    if not file:
        raise MissingRequirementException("File path to spec must be specified.")

    try:
        with open(file, "r") as f:
            agent_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"File is not in JSON format: {e}")
        Console.write_stderr(f"File is not in JSON format.")

    client = AgentClient(project_id=project_id)
    result = client.import_agent(
        data=agent_data
    )

    Console.write_stdout(f"Agent import details: {result}")



import_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "file",
        ["--file", "-f"],
        "File path to save export specification for agent",
        True
    ),
]


def create_sharing_link(option_list: list):
    project_id = None
    agent_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg

    if not agent_id:
        raise MissingRequirementException("Agent ID must be specified.")

    client = AgentClient(project_id=project_id)
    result = client.create_sharing_link(
        agent_id=agent_id,
    )
    Console.write_stdout(f"Sharing token: \n{result}")


create_sharing_link_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "ID of the agent to retrieve",
        True
    ),
]


def publish_agent_revision(option_list: list):
    project_id = None
    agent_id = None
    revision = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg
        if option_flag.name == "revision":
            revision = option_arg

    if not (agent_id and revision):
        raise MissingRequirementException("Agent ID and revision must be specified.")

    client = AgentClient(project_id=project_id)
    result = client.publish_agent_revision(
        agent_id=agent_id,
        revision=revision
    )
    Console.write_stdout(f"Published revision detail: \n{result}")


publish_agent_revision_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "ID of the agent to retrieve",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of agent.",
        True
    ),
]


def delete_agent(option_list: list):
    project_id = None
    agent_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg

    if not agent_id:
        raise MissingRequirementException("Agent ID must be specified.")

    client = AgentClient(project_id=project_id)
    result = client.delete_agent(
        agent_id=agent_id,
    )
    Console.write_stdout(f"Deleted agent detail: \n{result}")


delete_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "ID of the agent to retrieve",
        True
    ),
]


def update_agent(option_list: list):
    project_id = None
    agent_id = None
    name = None
    access_scope = None
    public_name = None
    job_description = None
    avatar_image = None
    description = None
    agent_data_prompt_instructions = None
    agent_data_prompt_inputs = list()
    agent_data_prompt_outputs = list()
    agent_data_prompt_examples = list()
    agent_data_llm_max_tokens = None
    agent_data_llm_timeout = None
    agent_data_llm_temperature = None
    agent_data_llm_top_k = None
    agent_data_llm_top_p = None
    agent_data_strategy_name = None
    agent_data_model_name = None
    agent_data_resource_pools = None
    automatic_publish = False
    upsert = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "agent_id":
            agent_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "public_name":
            public_name = option_arg
        if option_flag.name == "job_description":
            job_description = option_arg
        if option_flag.name == "avatar_image":
            avatar_image = option_arg
        if option_flag.name == "description":
            description = option_arg

        if option_flag.name == "agent_data_prompt_instructions":
            agent_data_prompt_instructions = option_arg
        if option_flag.name == "agent_data_prompt_input":

            if "[" not in option_arg:
                agent_data_prompt_inputs.append(option_arg)
            else:
                try:
                    input_json = json.loads(option_arg)
                    if not isinstance(input_json, list):
                        raise ValueError

                    agent_data_prompt_inputs = input_json
                except Exception as e:
                    raise WrongArgumentError(
                        "Inputs must be a list of strings: '[\"input_name\", \"another_input\"]'. "
                        "Each element in the list must be a string representing an input name."
                    )
        if option_flag.name == "agent_data_prompt_output":
            try:
                output_json = json.loads(option_arg)
                if isinstance(output_json, list):
                    agent_data_prompt_outputs = output_json
                elif isinstance(output_json, dict):
                    agent_data_prompt_outputs.append(output_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each output must be in JSON format: '{\"key\": \"output_key\", \"description\": \"description of the output\"}' "
                    "It must be a dictionary or a list of dictionaries. Each dictionary must contain 'key' and 'description'."
                )

        if option_flag.name == "agent_data_prompt_example":
            try:
                examples_json = json.loads(option_arg)
                if isinstance(examples_json, list):
                    agent_data_prompt_examples = examples_json
                elif isinstance(examples_json, dict):
                    agent_data_prompt_examples.append(examples_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each example must be in JSON format: '{\"inputData\": \"example input\", \"output\": \"expected output in JSON string format\"}' "
                    "It must be a dictionary or a list of dictionaries. Each dictionary must contain 'inputData' and 'output'."
                )

        if option_flag.name == "agent_data_llm_max_tokens":
            agent_data_llm_max_tokens = option_arg
        if option_flag.name == "agent_data_llm_timeout":
            agent_data_llm_timeout = option_arg
        if option_flag.name == "agent_data_llm_temperature":
            agent_data_llm_temperature = option_arg
        if option_flag.name == "agent_data_llm_top_k":
            agent_data_llm_top_k = option_arg
        if option_flag.name == "agent_data_llm_top_p":
            agent_data_llm_top_k = option_arg
        if option_flag.name == "agent_data_strategy_name":
            agent_data_strategy_name = option_arg
        if option_flag.name == "agent_data_model_name":
            agent_data_model_name = option_arg
        if option_flag.name == "agent_data_resource_pools":
            try:
                pools_json = json.loads(option_arg)
                if not isinstance(pools_json, list):
                    raise ValueError
                agent_data_resource_pools = pools_json
            except Exception as e:
                raise WrongArgumentError(
                    "Resource pools must be in JSON format: '[{\"name\": \"pool_name\", \"tools\": [{\"name\": \"tool_name\", \"revision\": int}], \"agents\": [{\"name\": \"agent_name\", \"revision\": int}]}]' "
                    "It must be a list of dictionaries. Each dictionary must contain 'name' and optional 'tools' and 'agents' lists."
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)
        if option_flag.name == "upsert":
            upsert = get_boolean_value(option_arg)

    if not (name and access_scope and public_name):
        raise MissingRequirementException("Cannot update assistant without specifying name, access scope and public name")

    prompt_inputs = get_agent_data_prompt_inputs(agent_data_prompt_inputs)
    prompt_outputs = get_agent_data_prompt_outputs(agent_data_prompt_outputs)
    prompt_examples = get_agent_data_prompt_examples(agent_data_prompt_examples)

    agent_data_prompt = {
        "instructions": agent_data_prompt_instructions,
        "inputs": prompt_inputs,
        "outputs": prompt_outputs,
        "examples": prompt_examples
    }
    agent_data_llm_config = {
        "maxTokens": agent_data_llm_max_tokens,
        "timeout": agent_data_llm_timeout,
        "sampling": {
            "temperature": agent_data_llm_temperature,
            "topK": agent_data_llm_top_k,
            "topP": agent_data_llm_top_p,
        }
    }
    agent_data_models = [
        {"name": agent_data_model_name}
    ]

    client = AgentClient(project_id=project_id)
    result = client.update_agent(
        agent_id=agent_id,
        name=name,
        access_scope=access_scope,
        public_name=public_name,
        job_description=job_description,
        avatar_image=avatar_image,
        description=description,
        agent_data_prompt=agent_data_prompt,
        agent_data_llm_config=agent_data_llm_config,
        agent_data_strategy_name=agent_data_strategy_name,
        agent_data_models=agent_data_models,
        agent_data_resource_pools=agent_data_resource_pools,
        automatic_publish=automatic_publish,
        upsert=upsert
    )
    Console.write_stdout(f"Updated agent detail: \n{result}")


update_agent_options = [
    PROJECT_ID_OPTION,
    Option(
        "agent_id",
        ["--agent-id", "--aid"],
        "Unique identifier of the agent to update",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the agent, must be unique within the project and exclude ':' or '/'",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Access scope of the agent, either 'public' or 'private' (defaults to 'private')",
        True
    ),
    Option(
        "public_name",
        ["--public-name", "--pn"],
        "Public name of the agent, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.example.my-agent') with only alphanumeric characters, periods, dashes, or underscores",
        True
    ),
    Option(
        "job_description",
        ["--job-description", "--jd"],
        "Description of the agent's role",
        True
    ),
    Option(
        "avatar_image",
        ["--avatar-image", "--aimg"],
        "URL for the agent's avatar image",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Detailed description of the agent's purpose",
        True
    ),
    Option(
        "agent_data_prompt_instructions",
        ["--agent-data-prompt-instructions", "--adp-inst"],
        "Instructions defining what the agent does and how, required for publication if context is not provided",
        True
    ),
    Option(
        "agent_data_prompt_input",
        ["--agent-data-prompt-input", "--adp-input"],
        "Agent Data prompt input: "
        "Prompt input as a list of strings (e.g., '[\"input1\", \"input2\"]') or multiple single strings via repeated flags, each representing an input name",
        True
    ),
    Option(
        "agent_data_prompt_output",
        ["--agent-data-prompt-output", "--adp-out"],
        "Prompt output in JSON format (e.g., '[{\"key\": \"output_key\", \"description\": \"output description\"}]'), as a dictionary or list of dictionaries with 'key' and 'description' fields",
        True
    ),
    Option(
        "agent_data_prompt_example",
        ["--agent-data-prompt-example", "--adp-ex"],
        "Prompt example in JSON format (e.g., '[{\"inputData\": \"example input\", \"output\": \"example output\"}]'), as a dictionary or list of dictionaries with 'inputData' and 'output' fields",
        True
    ),
    Option(
        "agent_data_llm_max_tokens",
        ["--agent-data-llm-max-tokens", "--adl-max-tokens"],
        "Maximum number of tokens the LLM can generate, used to control costs",
        True
    ),
    Option(
        "agent_data_llm_timeout",
        ["--agent-data-llm-timeout", "--adl-timeout"],
        "Timeout in seconds for LLM responses",
        True
    ),
    Option(
        "agent_data_llm_temperature",
        ["--agent-data-llm-temperature", "--adl-temperature"],
        "Sampling temperature for LLM (0.0 to 1.0), lower values for focused responses, higher for more random outputs",
        True
    ),
    Option(
        "agent_data_llm_top_k",
        ["--agent-data-llm-top-k", "--adl-top-k"],
        "TopK sampling parameter for LLM (currently unused)",
        True
    ),
    Option(
        "agent_data_llm_top_p",
        ["--agent-data-llm-top-p", "--adl-top-p"],
        "TopP sampling parameter for LLM (currently unused)",
        True
    ),
    Option(
        "agent_data_strategy_name",
        ["--agent-data-strategy-name", "--strategy-name"],
        "Name of the reasoning strategy to use",
        True
    ),
    Option(
        "agent_data_model_name",
        ["--agent-data-model-name", "--adm-name"],
        "Name of the LLM model (e.g., 'gpt-4o' or 'openai/gpt-4o'), at least one valid model required for publication",
        True
    ),
    Option(
        "agent_data_resource_pools",
        ["--agent-data-resource-pools", "--adr-pools"],
        "Resource pools in JSON format (e.g., '[{\"name\": \"pool_name\", \"tools\": [{\"name\": \"tool_name\", \"revision\": int}], \"agents\": [{\"name\": \"agent_name\", \"revision\": int}]}]'), "
        "as a list of dictionaries with 'name' (required) and optional 'tools' and 'agents' lists",
        False
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Whether to publish the agent after creation (0: create as draft, 1: create and publish)",
        True
    ),
    Option(
        "upsert",
        ["--upsert"],
        "Define if agent must be created if it doesn't exist (0: Update only if it exists. 1: Insert if doesn't exists)",
        True
    ),

]


def create_tool(option_list: list):
    project_id = None
    name = None
    description = None
    scope = None
    access_scope = "private"
    public_name = None
    icon = None
    open_api = None
    open_api_json = None
    report_events = "None"
    parameters = list()
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "scope":
            scope = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "public_name":
            public_name = option_arg
        if option_flag.name == "icon":
            icon = option_arg
        if option_flag.name == "open_api":
            open_api = option_arg
        if option_flag.name == "open_api_json":
            try:
                open_api_json = json.loads(option_arg)
                if not isinstance(open_api_json, dict):
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "open_api_json must be a valid JSON object (e.g., '{\"openapi\": \"3.0.0\", \"info\": {\"title\": \"example\", \"version\": \"1.0.0\"}, ...}')"
                )
        if option_flag.name == "report_events":
            report_events = option_arg
        if option_flag.name == "parameter":
            try:
                param_json = json.loads(option_arg)
                if not isinstance(param_json, dict):
                    raise ValueError
                parameters.append(param_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each parameter must be in JSON format (e.g., "
                    "'{\"key\": \"param_name\", \"description\": \"param description\", \"isRequired\": true, \"type\": \"app\"}' "
                    "or for config parameters: "
                    "'{\"key\": \"config_name\", \"description\": \"config description\", \"isRequired\": true, \"type\": \"config\", \"value\": \"config_value\", \"fromSecret\": false}')"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)

    if not name:
        raise MissingRequirementException("Tool name must be specified.")
    if access_scope == "public" and not public_name:
        raise MissingRequirementException("Public name is required when access_scope is 'public'.")
    if scope == "api" and not (open_api or open_api_json):
        raise MissingRequirementException(
            "For tools with scope 'api', either open_api or open_api_json must be provided."
        )

    tool_parameters = get_tool_parameters(parameters)

    client = ToolClient(project_id=project_id)
    result = client.create_tool(
        name=name,
        description=description,
        scope=scope,
        access_scope=access_scope,
        public_name=public_name,
        icon=icon,
        open_api=open_api,
        open_api_json=open_api_json,
        report_events=report_events,
        parameters=tool_parameters,
        automatic_publish=automatic_publish
    )
    Console.write_stdout(f"New tool detail: \n{result}")


create_tool_options = [
    PROJECT_ID_OPTION,
    Option(
        "name",
        ["--name", "-n"],
        "Name of the tool, must be unique within the project and exclude ':' or '/'",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of the tool’s purpose, helps agents decide when to use it",
        True
    ),
    Option(
        "scope",
        ["--scope", "-s"],
        "Scope of the tool, one of 'builtin', 'external', or 'api'",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Access scope of the tool, either 'public' or 'private' (defaults to 'private')",
        True
    ),
    Option(
        "public_name",
        ["--public-name", "--pn"],
        "Public name of the tool, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores",
        True
    ),
    Option(
        "icon",
        ["--icon", "-i"],
        "URL for the tool’s icon or avatar image",
        True
    ),
    Option(
        "open_api",
        ["--open-api", "--oa"],
        "URL where the OpenAPI specification can be loaded, required for 'api' scope if open_api_json is not provided",
        True
    ),
    Option(
        "open_api_json",
        ["--open-api-json", "--oaj"],
        "OpenAPI specification in JSON format (e.g., '{\"openapi\": \"3.0.0\", \"info\": {\"title\": \"example\", \"version\": \"1.0.0\"}, ...}'), required for 'api' scope if open_api is not provided",
        True
    ),
    Option(
        "report_events",
        ["--report-events", "--re"],
        "Event reporting mode for tool progress, one of 'None', 'All', 'Start', 'Finish', 'Progress' (defaults to 'None')",
        True
    ),
    Option(
        "parameter",
        ["--parameter", "-p"],
        "Tool parameter in JSON format (e.g., '{\"key\": \"param_name\", \"description\": \"param description\", \"isRequired\": true, \"type\": \"app\"}' or for config parameters: '{\"key\": \"config_name\", \"description\": \"config description\", \"isRequired\": true, \"type\": \"config\", \"value\": \"config_value\", \"fromSecret\": false}'). Multiple parameters can be specified by using this option multiple times",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Whether to publish the tool after creation (0: create as draft, 1: create and publish)",
        True
    ),
]


def list_tools(option_list: list):
    project_id = None
    id = ""
    count = "100"
    access_scope = "public"
    allow_drafts = True
    scope = "api"
    allow_external = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "id":
            id = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)
        if option_flag.name == "scope":
            scope = option_arg
        if option_flag.name == "allow_external":
            allow_external = get_boolean_value(option_arg)

    if scope and scope not in VALID_SCOPES:
        raise ValueError(f"Scope must be one of {', '.join(VALID_SCOPES)}.")

    client = ToolClient(project_id=project_id)
    result = client.list_tools(
        id=id,
        count=count,
        access_scope=access_scope,
        allow_drafts=allow_drafts,
        scope=scope,
        allow_external=allow_external,
    )
    Console.write_stdout(f"Tool list: \n{result}")


list_tools_options = [
    PROJECT_ID_OPTION,
    Option(
        "id",
        ["--id"],
        "ID of the tool to filter by. Defaults to an empty string (no filtering).",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of tools to retrieve. Defaults to '100'.",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope"],
        'Access scope of the tools, either "public" or "private". Defaults to "public".',
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts"],
        "Whether to include draft tools. Defaults to 1 (True).",
        True
    ),
    Option(
        "scope",
        ["--scope"],
        "Scope of the tools, must be 'builtin', 'external', or 'api'. Defaults to 'api'.",
        True
    ),
    Option(
        "allow_external",
        ["--allow-external"],
        "Whether to include external tools. Defaults to 1 (True).",
        True
    )
]


def get_tool(option_list: list):
    project_id = None
    tool_id = None
    revision = 0
    version = 0
    allow_drafts = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "revision":
            revision = option_arg
        if option_flag.name == "version":
            version = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)

    if not tool_id:
        raise MissingRequirementException("Tool ID must be specified.")

    client = ToolClient(project_id=project_id)
    result = client.get_tool(
        tool_id=tool_id,
        revision=revision,
        version=version,
        allow_drafts=allow_drafts,
    )
    Console.write_stdout(f"Tool detail: \n{result}")


get_tool_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to retrieve",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of agent.",
        True
    ),
    Option(
        "version",
        ["--version", "-v"],
        'Version of agent.',
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts"],
        "Whether to include draft agents. Defaults to 1 (True).",
        True
    ),
]


def export_tool(option_list: list):
    project_id = None
    tool_id = None
    file = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "file":
            file = option_arg


    if not tool_id:
        raise MissingRequirementException("Tool ID must be specified.")

    client = ToolClient(project_id=project_id)
    result = client.export_tool(
        tool_id=tool_id,
    )
    Console.write_stdout(f"Tool spec: \n{result}")
    if file:
        try:
            data = json.loads(result) if isinstance(result, str) else result
            with open(file, "w") as f:
                json.dump(data, f, indent=4)
            Console.write_stdout(f"Result from API saved to {file}.")
        except json.JSONDecodeError as e:
            logger.error(f"Result from API endpoint is not in JSON format: {e}")
            Console.write_stderr(f"Result from API endpoint is not in JSON format.")



export_tool_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to retrieve",
        True
    ),
    Option(
        "file",
        ["--file", "-f"],
        "File path to save export specification for tool",
        True
    ),
]



def delete_tool(option_list: list):
    project_id = None
    tool_id = None
    tool_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        elif option_flag.name == "tool_name":
            tool_name = option_arg

    if not (tool_id or tool_name):
        raise MissingRequirementException("Either Tool ID or Tool Name must be specified.")

    client = ToolClient(project_id=project_id)
    result = client.delete_tool(
        tool_id=tool_id,
        tool_name=tool_name
    )
    Console.write_stdout(f"Deleted tool detail: \n{result}")


delete_tool_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to delete",
        True
    ),
    Option(
        "tool_name",
        ["--tool-name", "--tname"],
        "Name of the tool to delete",
        True
    ),
]


def update_tool(option_list: list):
    project_id = None
    tool_id = None
    name = None
    description = None
    scope = None
    access_scope = None
    public_name = None
    icon = None
    open_api = None
    open_api_json = None
    report_events = "None"
    parameters = list()
    automatic_publish = False
    upsert = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "scope":
            scope = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "public_name":
            public_name = option_arg
        if option_flag.name == "icon":
            icon = option_arg
        if option_flag.name == "open_api":
            open_api = option_arg
        if option_flag.name == "open_api_json":
            try:
                open_api_json = json.loads(option_arg)
                if not isinstance(open_api_json, dict):
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "open_api_json must be a valid JSON object (e.g., '{\"openapi\": \"3.0.0\", \"info\": {\"title\": \"example\", \"version\": \"1.0.0\"}, ...}')"
                )
        if option_flag.name == "report_events":
            report_events = option_arg
        if option_flag.name == "parameter":
            try:
                param_json = json.loads(option_arg)
                if not isinstance(param_json, dict):
                    raise ValueError
                parameters.append(param_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each parameter must be in JSON format (e.g., "
                    "'{\"key\": \"param_name\", \"description\": \"param description\", \"isRequired\": true, \"type\": \"app\"}' "
                    "or for config parameters: "
                    "'{\"key\": \"config_name\", \"description\": \"config description\", \"isRequired\": true, \"type\": \"config\", \"value\": \"config_value\", \"fromSecret\": false}')"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)
        if option_flag.name == "upsert":
            upsert = get_boolean_value(option_arg)

    if not tool_id:
        raise MissingRequirementException("Tool ID must be specified.")
    if access_scope == "public" and not public_name:
        raise MissingRequirementException("Public name is required when access_scope is 'public'.")
    if upsert and scope == "api" and not (open_api or open_api_json):
        raise MissingRequirementException(
            "For tools with scope 'api' in upsert mode, either open_api or open_api_json must be provided."
        )

    tool_parameters = get_tool_parameters(parameters)

    client = ToolClient(project_id=project_id)
    result = client.update_tool(
        tool_id=tool_id,
        name=name,
        description=description,
        scope=scope,
        access_scope=access_scope,
        public_name=public_name,
        icon=icon,
        open_api=open_api,
        open_api_json=open_api_json,
        report_events=report_events,
        parameters=tool_parameters,
        automatic_publish=automatic_publish,
        upsert=upsert
    )
    Console.write_stdout(f"Updated tool detail: \n{result}")


update_tool_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "Unique identifier of the tool to update",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Updated name of the tool, must be unique within the project and exclude ':' or '/' if provided",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Updated description of the tool’s purpose, helps agents decide when to use it",
        True
    ),
    Option(
        "scope",
        ["--scope", "-s"],
        "Updated scope of the tool, one of 'builtin', 'external', or 'api'",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Updated access scope of the tool, either 'public' or 'private'",
        True
    ),
    Option(
        "public_name",
        ["--public-name", "--pn"],
        "Updated public name of the tool, required if access_scope is 'public', must be unique and follow a domain/library convention (e.g., 'com.globant.geai.web-search') with only alphanumeric characters, periods, dashes, or underscores",
        True
    ),
    Option(
        "icon",
        ["--icon", "-i"],
        "Updated URL for the tool’s icon or avatar image",
        True
    ),
    Option(
        "open_api",
        ["--open-api", "--oa"],
        "Updated URL where the OpenAPI specification can be loaded, required for 'api' scope in upsert mode if open_api_json is not provided",
        True
    ),
    Option(
        "open_api_json",
        ["--open-api-json", "--oaj"],
        "Updated OpenAPI specification in JSON format (e.g., '{\"openapi\": \"3.0.0\", \"info\": {\"title\": \"example\", \"version\": \"1.0.0\"}, ...}'), required for 'api' scope in upsert mode if open_api is not provided",
        True
    ),
    Option(
        "report_events",
        ["--report-events", "--re"],
        "Updated event reporting mode for tool progress, one of 'None', 'All', 'Start', 'Finish', 'Progress'",
        True
    ),
    Option(
        "parameter",
        ["--parameter", "-p"],
        "Updated tool parameter in JSON format (e.g., '{\"key\": \"param_name\", \"description\": \"param description\", \"isRequired\": true, \"type\": \"app\"}' or for config parameters: '{\"key\": \"config_name\", \"description\": \"config description\", \"isRequired\": true, \"type\": \"config\", \"value\": \"config_value\", \"fromSecret\": false}'). Multiple parameters can be specified by using this option multiple times",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Whether to publish the tool after updating (0: update as draft, 1: update and publish)",
        True
    ),
    Option(
        "upsert",
        ["--upsert"],
        "Whether to create the tool if it doesn’t exist (0: update only if exists, 1: insert if doesn’t exist)",
        True
    ),
]


def publish_tool_revision(option_list: list):
    project_id = None
    tool_id = None
    revision = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "revision":
            revision = option_arg

    if not (tool_id and revision):
        raise MissingRequirementException("Tool ID and revision must be specified.")

    client = ToolClient(project_id=project_id)
    result = client.publish_tool_revision(
        tool_id=tool_id,
        revision=revision
    )
    Console.write_stdout(f"Published revision detail: \n{result}")


publish_tool_revision_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to retrieve",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of tool. Use 0 to retrieve the latest revision.",
        True
    ),
]


def get_parameter(option_list: list):
    project_id = None
    tool_id = None
    tool_public_name = None
    allow_drafts = True
    revision = 0
    version = 0

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "tool_public_name":
            tool_public_name = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)
        if option_flag.name == "revision":
            revision = option_arg
        if option_flag.name == "version":
            version = option_arg

    if not (tool_public_name or tool_id):
        raise MissingRequirementException("Tool public name or ID must be specified.")

    client = ToolClient(project_id=project_id)
    result = client.get_parameter(
        tool_id=tool_id,
        tool_public_name=tool_public_name,
        revision=revision,
        version=version,
        allow_drafts=allow_drafts,
    )
    Console.write_stdout(f"Parameter detail: \n{result}")


get_parameter_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to set parameters for",
        True
    ),
    Option(
        "tool_public_name",
        ["--tool-public-name", "--tpn"],
        "Public name of the tool",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of the parameter. Use 0 to retrieve the latest revision.",
        True
    ),
    Option(
        "version",
        ["--version", "-v"],
        "Version of the parameter. Use 0 to retrieve the latest version.",
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts"],
        "Whether to include draft parameters. Defaults to 1 (True).",
        True
    ),
]


def set_parameter(option_list: list):
    project_id = None
    tool_public_name = None
    tool_id = None
    parameters = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "tool_id":
            tool_id = option_arg
        if option_flag.name == "tool_public_name":
            tool_public_name = option_arg
        if option_flag.name == "parameter":
            try:
                param_json = json.loads(option_arg)
                if not isinstance(param_json, dict):
                    raise ValueError
                parameters.append(param_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each parameter must be in JSON format: "
                    "'{\"key\": \"param_name\", \"dataType\": \"String\", \"description\": \"param description\", \"isRequired\": true}' "
                    "or for config parameters: "
                    "'{\"key\": \"config_name\", \"dataType\": \"String\", \"description\": \"config description\", "
                    "\"isRequired\": true, \"type\": \"config\", \"fromSecret\": false, \"value\": \"config_value\"}'"
                )

    if not (tool_public_name or tool_id):
        raise MissingRequirementException("Tool public name or ID must be specified.")
    if not parameters:
        raise MissingRequirementException("At least one parameter must be specified.")

    tool_parameters = get_tool_parameters(parameters)

    client = ToolClient(project_id=project_id)
    result = client.set_parameter(
        tool_id=tool_id,
        tool_public_name=tool_public_name,
        parameters=tool_parameters
    )
    Console.write_stdout(f"Set parameter detail: \n{result}")


set_parameter_options = [
    PROJECT_ID_OPTION,
    Option(
        "tool_id",
        ["--tool-id", "--tid"],
        "ID of the tool to set parameters for",
        True
    ),
    Option(
        "tool_public_name",
        ["--tool-public-name", "--tpn"],
        "Public name of the tool",
        True
    ),
    Option(
        "parameter",
        ["--parameter", "-p"],
        "Tool parameter in JSON format. "
        "For regular parameters: '{\"key\": \"param_name\", \"dataType\": \"String\", \"description\": \"param description\", \"isRequired\": true}' "
        "For config parameters: '{\"key\": \"config_name\", \"dataType\": \"String\", \"description\": \"config description\", "
        "\"isRequired\": true, \"type\": \"config\", \"fromSecret\": false, \"value\": \"config_value\"}' "
        "Multiple parameters can be specified by using this option multiple times.",
        True
    ),
]

# REASONING STRATEGIES


def list_reasoning_strategies(option_list: list):
    name = ""
    start = "0"
    count = "100"
    allow_external = True
    access_scope = "public"

    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "allow_external":
            allow_external = get_boolean_value(option_arg)
        if option_flag.name == "access_scope":
            access_scope = option_arg

    valid_access_scopes = ["public", "private"]
    if access_scope not in valid_access_scopes:
        raise WrongArgumentError(
            "Access scope must be either 'public' or 'private'."
        )

    client = ReasoningStrategyClient()
    result = client.list_reasoning_strategies(
        name=name,
        start=start,
        count=count,
        allow_external=allow_external,
        access_scope=access_scope,
    )
    Console.write_stdout(f"Reasoning strategies list: \n{result}")


list_reasoning_strategies_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Name of the reasoning strategy to filter by. Defaults to an empty string (no filtering).",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of reasoning strategies to retrieve. Defaults to '100'.",
        True
    ),
    Option(
        "allow_external",
        ["--allow-external"],
        "Whether to include external reasoning strategies. Defaults to 1 (True).",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope"],
        "Access scope of the reasoning strategies, either 'public' or 'private'. Defaults to 'public'.",
        True
    ),
]


def create_reasoning_strategy(option_list: list):
    name = None
    system_prompt = None
    access_scope = "public"
    strategy_type = "addendum"
    localized_descriptions = list()
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "system_prompt":
            system_prompt = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "type":
            strategy_type = option_arg
        if option_flag.name == "localized_description":
            try:
                desc_json = json.loads(option_arg)
                if not isinstance(desc_json, dict) or "language" not in desc_json or "description" not in desc_json:
                    raise ValueError
                localized_descriptions.append(desc_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each localized description must be in JSON format: "
                    "'{\"language\": \"english\", \"description\": \"description text\"}'"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)

    if not name:
        raise MissingRequirementException("Name must be specified.")
    if not system_prompt:
        raise MissingRequirementException("System prompt must be specified.")

    valid_access_scopes = ["public", "private"]
    if access_scope not in valid_access_scopes:
        raise WrongArgumentError(
            "Access scope must be either 'public' or 'private'."
        )

    valid_types = ["addendum"]
    if strategy_type not in valid_types:
        raise WrongArgumentError(
            "Type must be 'addendum'."
        )

    client = ReasoningStrategyClient()
    result = client.create_reasoning_strategy(
        name=name,
        system_prompt=system_prompt,
        access_scope=access_scope,
        strategy_type=strategy_type,
        localized_descriptions=localized_descriptions,
        automatic_publish=automatic_publish
    )
    Console.write_stdout(f"Created reasoning strategy detail: \n{result}")


create_reasoning_strategy_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Name of the reasoning strategy",
        True
    ),
    Option(
        "system_prompt",
        ["--system-prompt", "--sp"],
        "System prompt for the reasoning strategy",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Access scope of the reasoning strategy, either 'public' or 'private'. Defaults to 'public'.",
        True
    ),
    Option(
        "type",
        ["--type", "-t"],
        "Type of the reasoning strategy, e.g., 'addendum'. Defaults to 'addendum'.",
        True
    ),
    Option(
        "localized_description",
        ["--localized-description", "--ld"],
        "Localized description in JSON format: "
        "'{\"language\": \"english\", \"description\": \"description text\"}'. "
        "Multiple descriptions can be specified by using this option multiple times.",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if reasoning strategy must be published besides being created. 0: Create as draft. 1: Create and publish.",
        True
    ),
]


def update_reasoning_strategy(option_list: list):
    reasoning_strategy_id = None
    name = None
    system_prompt = None
    access_scope = None
    strategy_type = None
    localized_descriptions = list()
    automatic_publish = False
    upsert = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "reasoning_strategy_id":
            reasoning_strategy_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "system_prompt":
            system_prompt = option_arg
        if option_flag.name == "access_scope":
            access_scope = option_arg
        if option_flag.name == "type":
            strategy_type = option_arg
        if option_flag.name == "localized_description":
            try:
                desc_json = json.loads(option_arg)
                if not isinstance(desc_json, dict) or "language" not in desc_json or "description" not in desc_json:
                    raise ValueError
                localized_descriptions.append(desc_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each localized description must be in JSON format: "
                    "'{\"language\": \"english\", \"description\": \"description text\"}'"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)
        if option_flag.name == "upsert":
            # upsert = get_boolean_value(option_arg)
            Console.write_stdout("Upsert is not yet supported for reasoning strategies. Coming soon.")

    if not reasoning_strategy_id:
        raise MissingRequirementException("Reasoning strategy ID must be specified.")

    if access_scope is not None:
        valid_access_scopes = ["public", "private"]
        if access_scope not in valid_access_scopes:
            raise WrongArgumentError(
                "Access scope must be either 'public' or 'private'."
            )

    if strategy_type is not None:
        valid_types = ["addendum"]
        if strategy_type not in valid_types:
            raise WrongArgumentError(
                "Type must be 'addendum'."
            )

    client = ReasoningStrategyClient()
    result = client.update_reasoning_strategy(
        reasoning_strategy_id=reasoning_strategy_id,
        name=name,
        system_prompt=system_prompt,
        access_scope=access_scope,
        strategy_type=strategy_type,
        localized_descriptions=localized_descriptions if localized_descriptions else None,
        automatic_publish=automatic_publish,
        upsert=upsert
    )
    Console.write_stdout(f"Updated reasoning strategy detail: \n{result}")


update_reasoning_strategy_options = [
    Option(
        "reasoning_strategy_id",
        ["--reasoning-strategy-id", "--rsid"],
        "ID of the reasoning strategy to update",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the reasoning strategy (optional for update)",
        True
    ),
    Option(
        "system_prompt",
        ["--system-prompt", "--sp"],
        "System prompt for the reasoning strategy (optional for update)",
        True
    ),
    Option(
        "access_scope",
        ["--access-scope", "--as"],
        "Access scope of the reasoning strategy, either 'public' or 'private' (optional for update)",
        True
    ),
    Option(
        "type",
        ["--type", "-t"],
        "Type of the reasoning strategy, e.g., 'addendum' (optional for update)",
        True
    ),
    Option(
        "localized_description",
        ["--localized-description", "--ld"],
        "Localized description in JSON format: "
        "'{\"language\": \"english\", \"description\": \"description text\"}'. "
        "Multiple descriptions can be specified by using this option multiple times (optional for update).",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if reasoning strategy must be published after being updated. 0: Update as draft. 1: Update and publish. Defaults to 0.",
        True
    ),
    Option(
        "upsert",
        ["--upsert"],
        "Define if reasoning strategy must be created if it doesn't exist. 0: Update only if it exists. 1: Insert if it doesn't exist. Defaults to 0.",
        True
    ),
]


def get_reasoning_strategy(option_list: list):
    reasoning_strategy_id = None
    reasoning_strategy_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "reasoning_strategy_id":
            reasoning_strategy_id = option_arg
        if option_flag.name == "reasoning_strategy_name":
            reasoning_strategy_name = option_arg

    if not (reasoning_strategy_id or reasoning_strategy_name):
        raise MissingRequirementException("Either reasoning strategy ID or name must be specified.")

    client = ReasoningStrategyClient()
    result = client.get_reasoning_strategy(
        reasoning_strategy_id=reasoning_strategy_id,
        reasoning_strategy_name=reasoning_strategy_name
    )
    Console.write_stdout(f"Reasoning strategy detail: \n{result}")


get_reasoning_strategy_options = [
    Option(
        "reasoning_strategy_id",
        ["--reasoning-strategy-id", "--rsid"],
        "ID of the reasoning strategy to retrieve (optional if name is provided)",
        True
    ),
    Option(
        "reasoning_strategy_name",
        ["--reasoning-strategy-name", "--rsn"],
        "Name of the reasoning strategy to retrieve (optional if ID is provided)",
        True
    ),
]

# AGENTIC PROCESS DEFINITION
# PROCESSES


def create_process(option_list: list):
    project_id = None
    key = None
    name = None
    description = None
    kb = None
    agentic_activities = list()
    artifact_signals = list()
    user_signals = list()
    start_event = None
    end_event = None
    sequence_flows = list()
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "key":
            key = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "kb":
            try:
                kb = json.loads(option_arg)
                if not isinstance(kb, dict) or "name" not in kb or "artifactTypeName" not in kb:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "KB must be in JSON format: "
                    "'{\"name\": \"basic-sample\", \"artifactTypeName\": [\"sample-artifact\"]}'"
                )
        if option_flag.name == "agentic_activity":
            try:
                activity_json = json.loads(option_arg)
                if isinstance(activity_json, list) and not activity_json:
                    agentic_activities = []
                elif not isinstance(activity_json, dict) or "key" not in activity_json or "name" not in activity_json:
                    raise ValueError
                agentic_activities.append(activity_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each agentic activity must be in JSON format: "
                    "'{\"key\": \"activityOne\", \"name\": \"First Step\", \"taskName\": \"basic-task\", "
                    "\"agentName\": \"sample-translator\", \"agentRevisionId\": 0}'"
                )
        if option_flag.name == "artifact_signal":
            try:
                signal_json = json.loads(option_arg)
                if not isinstance(signal_json, dict) or "key" not in signal_json or "name" not in signal_json:
                    raise ValueError
                artifact_signals.append(signal_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each artifact signal must be in JSON format: "
                    "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\", \"handlingType\": \"C\", "
                    "\"artifactTypeName\": [\"sample-artifact\"]}'"
                )
        if option_flag.name == "user_signal":
            try:
                signal_json = json.loads(option_arg)
                if not isinstance(signal_json, dict) or "key" not in signal_json or "name" not in signal_json:
                    raise ValueError
                user_signals.append(signal_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each user signal must be in JSON format: "
                    "'{\"key\": \"signal_done\", \"name\": \"process-completed\"}'"
                )
        if option_flag.name == "start_event":
            try:
                start_event = json.loads(option_arg)
                if not isinstance(start_event, dict) or "key" not in start_event or "name" not in start_event:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "Start event must be in JSON format: "
                    "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\"}'"
                )
        if option_flag.name == "end_event":
            try:
                end_event = json.loads(option_arg)
                if not isinstance(end_event, dict) or "key" not in end_event or "name" not in end_event:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "End event must be in JSON format: "
                    "'{\"key\": \"end\", \"name\": \"Done\"}'"
                )
        if option_flag.name == "sequence_flow":
            try:
                flow_json = json.loads(option_arg)
                if not isinstance(flow_json, dict) or "key" not in flow_json or "sourceKey" not in flow_json or "targetKey" not in flow_json:
                    raise ValueError
                sequence_flows.append(flow_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each sequence flow must be in JSON format: "
                    "'{\"key\": \"step1\", \"sourceKey\": \"artifact.upload.1\", \"targetKey\": \"activityOne\"}'"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)

    if not key:
        raise MissingRequirementException("Key must be specified.")
    if not name:
        raise MissingRequirementException("Name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.create_process(
        key=key,
        name=name,
        description=description,
        kb=kb,
        agentic_activities=agentic_activities if agentic_activities else None,
        artifact_signals=artifact_signals if artifact_signals else None,
        user_signals=user_signals if user_signals else None,
        start_event=start_event,
        end_event=end_event,
        sequence_flows=sequence_flows if sequence_flows else None,
        automatic_publish=automatic_publish
    )
    Console.write_stdout(f"Created process detail: \n{result}")


create_process_options = [
    PROJECT_ID_OPTION,
    Option(
        "key",
        ["--key", "-k"],
        "Unique key for the process",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the process",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of the process (optional)",
        True
    ),
    Option(
        "kb",
        ["--kb"],
        "Knowledge base in JSON format: "
        "'{\"name\": \"basic-sample\", \"artifactTypeName\": [\"sample-artifact\"]}' (optional)",
        True
    ),
    Option(
        "agentic_activity",
        ["--agentic-activity", "--aa"],
        "Agentic activity in JSON format: "
        "'{\"key\": \"activityOne\", \"name\": \"First Step\", \"taskName\": \"basic-task\", "
        "\"agentName\": \"sample-translator\", \"agentRevisionId\": 0}' "
        "or '[]' to clear all activities. "
        "Multiple activities can be specified by using this option multiple times.",
        True
    ),
    Option(
        "artifact_signal",
        ["--artifact-signal", "--as"],
        "Artifact signal in JSON format: "
        "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\", \"handlingType\": \"C\", "
        "\"artifactTypeName\": [\"sample-artifact\"]}'. "
        "Multiple signals can be specified by using this option multiple times (optional).",
        True
    ),
    Option(
        "user_signal",
        ["--user-signal", "--us"],
        "User signal in JSON format: "
        "'{\"key\": \"signal_done\", \"name\": \"process-completed\"}'. "
        "Multiple signals can be specified by using this option multiple times (optional).",
        True
    ),
    Option(
        "start_event",
        ["--start-event", "--se"],
        "Start event in JSON format: "
        "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\"}' (optional)",
        True
    ),
    Option(
        "end_event",
        ["--end-event", "--ee"],
        "End event in JSON format: "
        "'{\"key\": \"end\", \"name\": \"Done\"}' (optional)",
        True
    ),
    Option(
        "sequence_flow",
        ["--sequence-flow", "--sf"],
        "Sequence flow in JSON format: "
        "'{\"key\": \"step1\", \"sourceKey\": \"artifact.upload.1\", \"targetKey\": \"activityOne\"}'. "
        "Multiple flows can be specified by using this option multiple times (optional).",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if process must be published after being created. 0: Create as draft. 1: Create and publish. Defaults to 0.",
        True
    ),
]


def update_process(option_list: list):
    project_id = None
    process_id = None
    name = None
    key = None
    description = None
    kb = None
    agentic_activities = list()
    artifact_signals = list()
    user_signals = list()
    start_event = None
    end_event = None
    sequence_flows = list()
    automatic_publish = False
    upsert = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_id":
            process_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "key":
            key = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "kb":
            try:
                kb = json.loads(option_arg)
                if not isinstance(kb, dict) or "name" not in kb or "artifactTypeName" not in kb:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "KB must be in JSON format: "
                    "'{\"name\": \"basic-sample\", \"artifactTypeName\": [\"sample-artifact\"]}'"
                )
        if option_flag.name == "agentic_activity":
            try:
                activity_json = json.loads(option_arg)
                if isinstance(activity_json, list) and not activity_json:
                    agentic_activities = []
                elif not isinstance(activity_json, dict) or "key" not in activity_json or "name" not in activity_json:
                    raise ValueError
                agentic_activities.append(activity_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each agentic activity must be in JSON format: "
                    "'{\"key\": \"activityOne\", \"name\": \"First Step\", \"taskName\": \"basic-task\", "
                    "\"agentName\": \"sample-translator\", \"agentRevisionId\": 0}'"
                )
        if option_flag.name == "artifact_signal":
            try:
                signal_json = json.loads(option_arg)
                if not isinstance(signal_json, dict) or "key" not in signal_json or "name" not in signal_json:
                    raise ValueError
                artifact_signals.append(signal_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each artifact signal must be in JSON format: "
                    "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\", \"handlingType\": \"C\", "
                    "\"artifactTypeName\": [\"sample-artifact\"]}'"
                )
        if option_flag.name == "user_signal":
            try:
                signal_json = json.loads(option_arg)
                if not isinstance(signal_json, dict) or "key" not in signal_json or "name" not in signal_json:
                    raise ValueError
                user_signals.append(signal_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each user signal must be in JSON format: "
                    "'{\"key\": \"signal_done\", \"name\": \"process-completed\"}'"
                )
        if option_flag.name == "start_event":
            try:
                start_event = json.loads(option_arg)
                if not isinstance(start_event, dict) or "key" not in start_event or "name" not in start_event:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "Start event must be in JSON format: "
                    "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\"}'"
                )
        if option_flag.name == "end_event":
            try:
                end_event = json.loads(option_arg)
                if not isinstance(end_event, dict) or "key" not in end_event or "name" not in end_event:
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "End event must be in JSON format: "
                    "'{\"key\": \"end\", \"name\": \"Done\"}'"
                )
        if option_flag.name == "sequence_flow":
            try:
                flow_json = json.loads(option_arg)
                if not isinstance(flow_json, dict) or "key" not in flow_json or "sourceKey" not in flow_json or "targetKey" not in flow_json:
                    raise ValueError
                sequence_flows.append(flow_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each sequence flow must be in JSON format: "
                    "'{\"key\": \"step1\", \"sourceKey\": \"artifact.upload.1\", \"targetKey\": \"activityOne\"}'"
                )
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)
        if option_flag.name == "upsert":
            upsert = get_boolean_value(option_arg)

    if not (process_id or name):
        raise MissingRequirementException("Either process ID or name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.update_process(
        process_id=process_id,
        name=name,
        key=key,
        description=description,
        kb=kb,
        agentic_activities=agentic_activities if agentic_activities else None,
        artifact_signals=artifact_signals if artifact_signals else None,
        user_signals=user_signals if user_signals else None,
        start_event=start_event,
        end_event=end_event,
        sequence_flows=sequence_flows if sequence_flows else None,
        automatic_publish=automatic_publish,
        upsert=upsert
    )
    Console.write_stdout(f"Updated process detail: \n{result}")


update_process_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_id",
        ["--process-id", "--pid"],
        "ID of the process to update (optional if name is provided)",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the process to update (optional if process_id is provided)",
        True
    ),
    Option(
        "key",
        ["--key", "-k"],
        "Unique key for the process (optional for update)",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of the process (optional for update)",
        True
    ),
    Option(
        "kb",
        ["--kb"],
        "Knowledge base in JSON format: "
        "'{\"name\": \"basic-sample\", \"artifactTypeName\": [\"sample-artifact\"]}' (optional for update)",
        True
    ),
    Option(
        "agentic_activity",
        ["--agentic-activity", "--aa"],
        "Agentic activity in JSON format: "
        "'{\"key\": \"activityOne\", \"name\": \"First Step\", \"taskName\": \"basic-task\", "
        "\"agentName\": \"sample-translator\", \"agentRevisionId\": 0}' "
        "or '[]' to clear all activities. "
        "Multiple activities can be specified by using this option multiple times (optional for update).",
        True
    ),
    Option(
        "artifact_signal",
        ["--artifact-signal", "--as"],
        "Artifact signal in JSON format: "
        "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\", \"handlingType\": \"C\", "
        "\"artifactTypeName\": [\"sample-artifact\"]}'. "
        "Multiple signals can be specified by using this option multiple times (optional for update).",
        True
    ),
    Option(
        "user_signal",
        ["--user-signal", "--us"],
        "User signal in JSON format: "
        "'{\"key\": \"signal_done\", \"name\": \"process-completed\"}'. "
        "Multiple signals can be specified by using this option multiple times (optional for update).",
        True
    ),
    Option(
        "start_event",
        ["--start-event", "--se"],
        "Start event in JSON format: "
        "'{\"key\": \"artifact.upload.1\", \"name\": \"artifact.upload\"}' (optional for update)",
        True
    ),
    Option(
        "end_event",
        ["--end-event", "--ee"],
        "End event in JSON format: "
        "'{\"key\": \"end\", \"name\": \"Done\"}' (optional for update)",
        True
    ),
    Option(
        "sequence_flow",
        ["--sequence-flow", "--sf"],
        "Sequence flow in JSON format: "
        "'{\"key\": \"step1\", \"sourceKey\": \"artifact.upload.1\", \"targetKey\": \"activityOne\"}'. "
        "Multiple flows can be specified by using this option multiple times (optional for update).",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if process must be published after being updated. 0: Update as draft. 1: Update and publish. Defaults to 0.",
        True
    ),
    Option(
        "upsert",
        ["--upsert"],
        "Define if process must be created if it doesn't exist. 0: Update only if it exists. 1: Insert if it doesn't exist. Defaults to 0.",
        True
    ),
]


def get_process(option_list: list):
    project_id = None
    process_id = None
    process_name = None
    revision = "0"
    version = 0
    allow_drafts = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_id":
            process_id = option_arg
        if option_flag.name == "process_name":
            process_name = option_arg
        if option_flag.name == "revision":
            revision = option_arg
        if option_flag.name == "version":
            version = int(option_arg)
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)

    if not (process_id or process_name):
        raise MissingRequirementException("Either process ID or process name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_process(
        process_id=process_id,
        process_name=process_name,
        revision=revision,
        version=version,
        allow_drafts=allow_drafts
    )
    Console.write_stdout(f"Process detail: \n{result}")


get_process_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_id",
        ["--process-id", "--pid"],
        "ID of the process to retrieve (optional if process_name is provided)",
        True
    ),
    Option(
        "process_name",
        ["--process-name", "--pn"],
        "Name of the process to retrieve (optional if process_id is provided)",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of the process to retrieve. Defaults to '0' (latest revision).",
        True
    ),
    Option(
        "version",
        ["--version", "-v"],
        "Version of the process to retrieve. Defaults to 0 (latest version).",
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts", "--ad"],
        "Whether to include draft processes in the retrieval. Defaults to 1 (True).",
        True
    ),
]


def list_processes(option_list: list):
    project_id = None
    id = None
    name = None
    status = None
    start = "0"
    count = "100"
    allow_draft = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "id":
            id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "status":
            status = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "allow_draft":
            allow_draft = get_boolean_value(option_arg)

    client = AgenticProcessClient(project_id=project_id)
    result = client.list_processes(
        id=id,
        name=name,
        status=status,
        start=start,
        count=count,
        allow_draft=allow_draft
    )
    Console.write_stdout(f"Process list: \n{result}")


list_processes_options = [
    PROJECT_ID_OPTION,
    Option(
        "id",
        ["--id"],
        "ID of the process to filter by (optional)",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the process to filter by (optional)",
        True
    ),
    Option(
        "status",
        ["--status", "-s"],
        "Status of the processes to filter by (e.g., 'active', 'inactive') (optional)",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of processes to retrieve. Defaults to '100'.",
        True
    ),
    Option(
        "allow_draft",
        ["--allow-draft", "--ad"],
        "Whether to include draft processes in the list. Defaults to 1 (True).",
        True
    ),
]


def list_processes_instances(option_list: list):
    project_id = None
    process_id = None
    is_active = True
    start = "0"
    count = "10"

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_id":
            process_id = option_arg
        if option_flag.name == "is_active":
            is_active = get_boolean_value(option_arg)
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg

    if not process_id:
        raise MissingRequirementException("Process ID must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.list_process_instances(
        process_id=process_id,
        is_active=is_active,
        start=start,
        count=count
    )
    Console.write_stdout(f"Process instances list: \n{result}")


list_processes_instances_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_id",
        ["--process-id", "--pid"],
        "ID of the process to list instances for",
        True
    ),
    Option(
        "is_active",
        ["--is-active", "--ia"],
        "Whether to list only active process instances. Defaults to 1 (True).",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of process instances to retrieve. Defaults to '10'.",
        True
    ),
]


def delete_process(option_list: list):
    project_id = None
    process_id = None
    process_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_id":
            process_id = option_arg
        if option_flag.name == "process_name":
            process_name = option_arg

    if not (process_id or process_name):
        raise MissingRequirementException("Either process ID or process name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.delete_process(
        process_id=process_id,
        process_name=process_name
    )
    Console.write_stdout(f"Delete process result: \n{result}")


delete_process_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_id",
        ["--process-id", "--pid"],
        "ID of the process to delete (optional if process_name is provided)",
        True
    ),
    Option(
        "process_name",
        ["--process-name", "--pn"],
        "Name of the process to delete (optional if process_id is provided)",
        True
    ),
]


def publish_process_revision(option_list: list):
    project_id = None
    process_id = None
    process_name = None
    revision = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_id":
            process_id = option_arg
        if option_flag.name == "process_name":
            process_name = option_arg
        if option_flag.name == "revision":
            revision = option_arg

    if not (process_id or process_name):
        raise MissingRequirementException("Either process ID or process name must be specified.")
    if not revision:
        raise MissingRequirementException("Revision must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.publish_process_revision(
        process_id=process_id,
        process_name=process_name,
        revision=revision
    )
    Console.write_stdout(f"Published process revision detail: \n{result}")


publish_process_revision_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_id",
        ["--process-id", "--pid"],
        "ID of the process to publish (optional if process_name is provided)",
        True
    ),
    Option(
        "process_name",
        ["--process-name", "--pn"],
        "Name of the process to publish (optional if process_id is provided)",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of the process to publish",
        True
    ),
]


# TASKS


def create_task(option_list: list):
    project_id = None
    name = None
    description = None
    title_template = None
    id = None
    prompt_data = None
    artifact_types = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "title_template":
            title_template = option_arg
        if option_flag.name == "id":
            id = option_arg
        if option_flag.name == "prompt_data":
            try:
                prompt_data = json.loads(option_arg)
                if not isinstance(prompt_data, dict):
                    raise ValueError("prompt_data must be a JSON object")
            except json.JSONDecodeError:
                raise ValueError("prompt_data must be a valid JSON string")
        if option_flag.name == "artifact_types":
            try:
                artifact_types = json.loads(option_arg)
                if not isinstance(artifact_types, list):
                    raise ValueError("artifact_types must be a JSON array")
            except json.JSONDecodeError:
                raise ValueError("artifact_types must be a valid JSON string")
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)

    if not name:
        raise MissingRequirementException("Task name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.create_task(
        name=name,
        description=description,
        title_template=title_template,
        id=id,
        prompt_data=prompt_data,
        artifact_types=artifact_types,
        automatic_publish=automatic_publish
    )
    Console.write_stdout(f"Created task detail: \n{result}")


create_task_options = [
    PROJECT_ID_OPTION,
    Option(
        "name",
        ["--name", "-n"],
        "Name of the task (required, must be unique within the project, no ':' or '/')",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of what the task does (optional)",
        True
    ),
    Option(
        "title_template",
        ["--title-template", "--tt"],
        "Title template for task instances (optional, e.g., 'specs for {{issue}}')",
        True
    ),
    Option(
        "id",
        ["--id"],
        "Custom ID for the task (optional, used instead of system-assigned ID)",
        True
    ),
    Option(
        "prompt_data",
        ["--prompt-data", "--pd"],
        "Prompt configuration as JSON (optional, e.g., '{\"instructions\": \"Do this\", \"inputs\": [\"x\"]}')",
        True
    ),
    Option(
        "artifact_types",
        ["--artifact-types", "--at"],
        "Artifact types as JSON array (optional, e.g., '[{\"name\": \"doc\", \"description\": \"Docs\", \"isRequired\": true, \"usageType\": \"output\", \"artifactVariableKey\": \"doc_prefix\"}]')",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if task must be published after creation. 0: Create as draft. 1: Create and publish. Defaults to 0.",
        True
    ),
]


def get_task(option_list: list):
    project_id = None
    task_id = None
    task_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "task_id":
            task_id = option_arg
        if option_flag.name == "task_name":
            task_name = option_arg

    if not (task_id or task_name):
        raise MissingRequirementException("Either task ID or task name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_task(
        task_id=task_id,
        task_name=task_name
    )
    Console.write_stdout(f"Task detail: \n{result}")


get_task_options = [
    PROJECT_ID_OPTION,
    Option(
        "task_id",
        ["--task-id", "--tid"],
        "ID of the task to retrieve",
        True
    ),
    Option(
        "task_name",
        ["--task-name", "--tn"],
        "Name of the task to retrieve (optional if task_id is provided)",
        True
    ),
]


def list_tasks(option_list: list):
    project_id = None
    id = None
    start = "0"
    count = "100"
    allow_drafts = True

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "id":
            id = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "allow_drafts":
            allow_drafts = get_boolean_value(option_arg)

    client = AgenticProcessClient(project_id=project_id)
    result = client.list_tasks(
        id=id,
        start=start,
        count=count,
        allow_drafts=allow_drafts
    )
    Console.write_stdout(f"Task list: \n{result}")


list_tasks_options = [
    PROJECT_ID_OPTION,
    Option(
        "id",
        ["--id"],
        "ID of the task to filter by (optional)",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of tasks to retrieve. Defaults to '100'.",
        True
    ),
    Option(
        "allow_drafts",
        ["--allow-drafts", "--ad"],
        "Whether to include draft tasks in the list. Defaults to 1 (True).",
        True
    ),
]


def update_task(option_list: list):
    project_id = None
    task_id = None
    name = None
    description = None
    title_template = None
    id = None
    prompt_data = None
    artifact_types = None
    automatic_publish = False
    upsert = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "task_id":
            task_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "description":
            description = option_arg
        if option_flag.name == "title_template":
            title_template = option_arg
        if option_flag.name == "id":
            id = option_arg
        if option_flag.name == "prompt_data":
            try:
                prompt_data = json.loads(option_arg)
                if not isinstance(prompt_data, dict):
                    raise ValueError("prompt_data must be a JSON object")
            except json.JSONDecodeError:
                raise ValueError("prompt_data must be a valid JSON string")
        if option_flag.name == "artifact_types":
            try:
                artifact_types = json.loads(option_arg)
                if not isinstance(artifact_types, list):
                    raise ValueError("artifact_types must be a JSON array")
            except json.JSONDecodeError:
                raise ValueError("artifact_types must be a valid JSON string")
        if option_flag.name == "automatic_publish":
            automatic_publish = get_boolean_value(option_arg)
        if option_flag.name == "upsert":
            upsert = get_boolean_value(option_arg)

    if not (task_id or name):
        raise MissingRequirementException("Either task ID or name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.update_task(
        task_id=task_id,
        name=name,
        description=description,
        title_template=title_template,
        id=id,
        prompt_data=prompt_data,
        artifact_types=artifact_types,
        automatic_publish=automatic_publish,
        upsert=upsert
    )
    Console.write_stdout(f"Updated task detail: \n{result}")


update_task_options = [
    PROJECT_ID_OPTION,
    Option(
        "task_id",
        ["--task-id", "--tid"],
        "ID of the task to update",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Updated name of the task (optional, must be unique within the project, no ':' or '/' if provided)",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Updated description of what the task does (optional)",
        True
    ),
    Option(
        "title_template",
        ["--title-template", "--tt"],
        "Updated title template for task instances (optional, e.g., 'specs for {{issue}}')",
        True
    ),
    Option(
        "id",
        ["--id"],
        "Custom ID for the task (optional, used in upsert mode if creating a new task)",
        True
    ),
    Option(
        "prompt_data",
        ["--prompt-data", "--pd"],
        "Updated prompt configuration as JSON (optional, e.g., '{\"instructions\": \"Do this\", \"inputs\": [\"x\"]}')",
        True
    ),
    Option(
        "artifact_types",
        ["--artifact-types", "--at"],
        "Updated artifact types as JSON array (optional, e.g., '[{\"name\": \"doc\", \"description\": \"Docs\", \"isRequired\": true, \"usageType\": \"output\", \"artifactVariableKey\": \"doc_prefix\"}]')",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if task must be published after update. 0: Update as draft. 1: Update and publish. Defaults to 0.",
        True
    ),
    Option(
        "upsert",
        ["--upsert"],
        "Define if task must be created if it doesn't exist. 0: Update only if exists. 1: Insert if doesn't exist. Defaults to 0.",
        True
    ),
]


def delete_task(option_list: list):
    project_id = None
    task_id = None
    task_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "task_id":
            task_id = option_arg
        if option_flag.name == "task_name":
            task_name = option_arg

    if not (task_id or task_name):
        raise MissingRequirementException("Either task ID or task name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.delete_task(
        task_id=task_id,
        task_name = task_name
    )
    Console.write_stdout(f"Delete task result: \n{result}")


delete_task_options = [
    PROJECT_ID_OPTION,
    Option(
        "task_id",
        ["--task-id", "--tid"],
        "ID of the task to delete",
        True
    ),
    Option(
        "task_name",
        ["--task-name", "--tn"],
        "Name of the task to delete (optional if task_id is provided)",
        True
    ),
]


def publish_task_revision(option_list: list):
    project_id = None
    task_id = None
    task_name = None
    revision = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "task_id":
            task_id = option_arg
        if option_flag.name == "task_name":
            task_name = option_arg
        if option_flag.name == "revision":
            revision = option_arg

    if not (task_id or task_name):
        raise MissingRequirementException("Either task ID or task name must be specified.")
    if not revision:
        raise MissingRequirementException("Revision must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.publish_task_revision(
        task_id=task_id,
        task_name=task_name,
        revision=revision
    )
    Console.write_stdout(f"Published task revision detail: \n{result}")


publish_task_revision_options = [
    PROJECT_ID_OPTION,
    Option(
        "task_id",
        ["--task-id", "--tid"],
        "ID of the task to publish",
        True
    ),
    Option(
        "task_name",
        ["--task-name", "--tn"],
        "Name of the task to publish (optional if task_id is provided)",
        True
    ),
    Option(
        "revision",
        ["--revision", "-r"],
        "Revision of the task to publish",
        True
    ),
]


# RUNTIME - Process instances
def start_instance(option_list: list):
    project_id = None
    process_name = None
    subject = None
    variables = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "process_name":
            process_name = option_arg
        if option_flag.name == "subject":
            subject = option_arg
        if option_flag.name == "variables":
            try:
                variables = json.loads(option_arg)
                if not isinstance(variables, list):
                    raise ValueError
            except Exception:
                raise WrongArgumentError(
                    "Variables must be a JSON list: '[{\"key\": \"location\", \"value\": \"Paris\"}]'"
                )

    if not process_name:
        raise MissingRequirementException("Process name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.start_instance(
        process_name=process_name,
        subject=subject,
        variables=variables
    )
    Console.write_stdout(f"Started instance detail: \n{result}")


start_instance_options = [
    PROJECT_ID_OPTION,
    Option(
        "process_name",
        ["--process-name", "--pn"],
        "Name of the process to start an instance for",
        True
    ),
    Option(
        "subject",
        ["--subject", "-s"],
        "Subject of the process instance (optional)",
        True
    ),
    Option(
        "variables",
        ["--variables", "-v"],
        "Variables for the process instance in JSON list format: '[{\"key\": \"location\", \"value\": \"Paris\"}]' (optional)",
        True
    ),
]


def abort_instance(option_list: list):
    project_id = None
    instance_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "instance_id":
            instance_id = option_arg

    if not instance_id:
        raise MissingRequirementException("Instance ID must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.abort_instance(
        instance_id=instance_id
    )
    Console.write_stdout(f"Abort instance result: \n{result}")


abort_instance_options = [
    PROJECT_ID_OPTION,
    Option(
        "instance_id",
        ["--instance-id", "--iid"],
        "ID of the instance to abort",
        True
    ),
]


def get_instance(option_list: list):
    project_id = None
    instance_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "instance_id":
            instance_id = option_arg

    if not instance_id:
        raise MissingRequirementException("Instance ID must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_instance(
        instance_id=instance_id
    )
    Console.write_stdout(f"Instance detail: \n{result}")


get_instance_options = [
    PROJECT_ID_OPTION,
    Option(
        "instance_id",
        ["--instance-id", "--iid"],
        "ID of the instance to retrieve",
        True
    ),
]


def get_instance_history(option_list: list):
    project_id = None
    instance_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "instance_id":
            instance_id = option_arg

    if not instance_id:
        raise MissingRequirementException("Instance ID must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_instance_history(
        instance_id=instance_id
    )
    Console.write_stdout(f"Instance history: \n{result}")


get_instance_history_options = [
    PROJECT_ID_OPTION,
    Option(
        "instance_id",
        ["--instance-id", "--iid"],
        "ID of the instance to retrieve history for",
        True
    ),
]

def get_thread_information(option_list: list):
    project_id = None
    thread_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "thread_id":
            thread_id = option_arg

    if not thread_id:
        raise MissingRequirementException("Thread ID must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_thread_information(
        thread_id=thread_id
    )
    Console.write_stdout(f"Thread information: \n{result}")


get_thread_information_options = [
    PROJECT_ID_OPTION,
    Option(
        "thread_id",
        ["--thread-id", "--tid"],
        "ID of the thread to retrieve information for",
        True
    ),
]


def send_user_signal(option_list: list):
    project_id = None
    instance_id = None
    signal_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "instance_id":
            instance_id = option_arg
        if option_flag.name == "signal_name":
            signal_name = option_arg

    if not instance_id:
        raise MissingRequirementException("Instance ID must be specified.")
    if not signal_name:
        raise MissingRequirementException("Signal name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.send_user_signal(
        instance_id=instance_id,
        signal_name=signal_name
    )
    Console.write_stdout(f"Send user signal result: \n{result}")


send_user_signal_options = [
    PROJECT_ID_OPTION,
    Option(
        "instance_id",
        ["--instance-id", "--iid"],
        "ID of the instance to send the signal to",
        True
    ),
    Option(
        "signal_name",
        ["--signal-name", "--sn"],
        "Name of the user signal to send (e.g., 'approval')",
        True
    ),
]

# KNOWLEDGE BASES


def create_kb(option_list: list):
    project_id = None
    name = None
    artifacts = None
    metadata = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "artifacts":
            try:
                artifacts = json.loads(option_arg)
                if not isinstance(artifacts, list):
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "Artifacts must be a JSON list of strings: '[\"artifact1\", \"artifact2\"]'"
                )
        if option_flag.name == "metadata":
            try:
                metadata = json.loads(option_arg)
                if not isinstance(metadata, list):
                    raise ValueError
            except Exception as e:
                raise WrongArgumentError(
                    "Metadata must be a JSON list of strings: '[\"meta1\", \"meta2\"]'"
                )

    if not name:
        raise MissingRequirementException("Name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.create_kb(
        name=name,
        artifacts=artifacts,
        metadata=metadata
    )
    Console.write_stdout(f"Created knowledge base detail: \n{result}")


create_kb_options = [
    PROJECT_ID_OPTION,
    Option(
        "name",
        ["--name", "-n"],
        "Name of the knowledge base",
        True
    ),
    Option(
        "artifacts",
        ["--artifacts", "-a"],
        "List of artifact names in JSON format: '[\"artifact1\", \"artifact2\"]'. Optional.",
        True
    ),
    Option(
        "metadata",
        ["--metadata", "-m"],
        "List of metadata fields in JSON format: '[\"meta1\", \"meta2\"]'. Optional.",
        True
    ),
]


def get_kb(option_list: list):
    project_id = None
    kb_id = None
    kb_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "kb_id":
            kb_id = option_arg
        if option_flag.name == "kb_name":
            kb_name = option_arg

    if not (kb_id or kb_name):
        raise MissingRequirementException("Either KB ID or KB name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.get_kb(
        kb_id=kb_id,
        kb_name=kb_name
    )
    Console.write_stdout(f"Knowledge base detail: \n{result}")


get_kb_options = [
    PROJECT_ID_OPTION,
    Option(
        "kb_id",
        ["--kb-id", "--kid"],
        "ID of the knowledge base to retrieve (optional if kb_name is provided)",
        True
    ),
    Option(
        "kb_name",
        ["--kb-name", "--kn"],
        "Name of the knowledge base to retrieve (optional if kb_id is provided)",
        True
    ),
]


def list_kbs(option_list: list):
    project_id = None
    name = None
    start = "0"
    count = "100"

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "name":
            name = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg

    client = AgenticProcessClient(project_id=project_id)
    result = client.list_kbs(
        name=name,
        start=start,
        count=count
    )
    Console.write_stdout(f"Knowledge base list: \n{result}")


list_kbs_options = [
    PROJECT_ID_OPTION,
    Option(
        "name",
        ["--name", "-n"],
        "Name of the knowledge base to filter by (optional)",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of knowledge bases to retrieve. Defaults to '100'.",
        True
    ),
]


def delete_kb(option_list: list):
    project_id = None
    kb_id = None
    kb_name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "kb_id":
            kb_id = option_arg
        if option_flag.name == "kb_name":
            kb_name = option_arg

    if not (kb_id or kb_name):
        raise MissingRequirementException("Either KB ID or KB name must be specified.")

    client = AgenticProcessClient(project_id=project_id)
    result = client.delete_kb(
        kb_id=kb_id,
        kb_name=kb_name
    )
    Console.write_stdout(f"Delete knowledge base result: \n{result}")


delete_kb_options = [
    PROJECT_ID_OPTION,
    Option(
        "kb_id",
        ["--kb-id", "--kid"],
        "ID of the knowledge base to delete (optional if kb_name is provided)",
        True
    ),
    Option(
        "kb_name",
        ["--kb-name", "--kn"],
        "Name of the knowledge base to delete (optional if kb_id is provided)",
        True
    ),
]

# JOBS


def list_jobs(option_list: list):
    project_id = None
    start = "0"
    count = "100"
    topic = None
    token = None
    name = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg
        if option_flag.name == "start":
            start = option_arg
        if option_flag.name == "count":
            count = option_arg
        if option_flag.name == "topic":
            topic = option_arg
        if option_flag.name == "token":
            token = option_arg
        if option_flag.name == "name":
            name = option_arg

    client = AgenticProcessClient(project_id=project_id)
    result = client.list_jobs(
        start=start,
        count=count,
        topic=topic,
        token=token,
        name=name
    )
    Console.write_stdout(f"Job list: \n{result}")


list_jobs_options = [
    PROJECT_ID_OPTION,
    Option(
        "start",
        ["--start", "-s"],
        "Starting index for pagination. Defaults to '0'.",
        True
    ),
    Option(
        "count",
        ["--count", "-c"],
        "Number of jobs to retrieve. Defaults to '100'.",
        True
    ),
    Option(
        "topic",
        ["--topic"],
        "Topic of the jobs to filter by (optional).",
        True
    ),
    Option(
        "token",
        ["--token", "-t"],
        "Token of the jobs to filter by (optional).",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "Name of the jobs to filter by (optional).",
        True
    )
]
# COMMANDS


ai_lab_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    # Agents
    Command(
        "list_agents",
        ["list-agents", "la"],
        "List agents",
        list_agents,
        ArgumentsEnum.REQUIRED,
        [],
        list_agents_options
    ),
    Command(
        "create_agent",
        ["create-agent", "ca"],
        "Create agent",
        create_agent,
        ArgumentsEnum.REQUIRED,
        [],
        create_agent_options
    ),
    Command(
        "get_agent",
        ["get-agent", "ga"],
        "Get agent",
        get_agent,
        ArgumentsEnum.REQUIRED,
        [],
        get_agent_options
    ),
    Command(
        "export_agent",
        ["export-agent", "ea"],
        "Export agent",
        export_agent,
        ArgumentsEnum.REQUIRED,
        [],
        export_agent_options
    ),
    Command(
        "import_agent",
        ["import-agent", "ia"],
        "Import agent",
        import_agent,
        ArgumentsEnum.REQUIRED,
        [],
        import_agent_options
    ),
    Command(
        "create_sharing_link",
        ["create-sharing-link", "csl"],
        "Create sharing link",
        create_sharing_link,
        ArgumentsEnum.REQUIRED,
        [],
        create_sharing_link_options
    ),
    Command(
        "publish_agent_revision",
        ["publish-agent-revision", "par"],
        "Publish agent revision",
        publish_agent_revision,
        ArgumentsEnum.REQUIRED,
        [],
        publish_agent_revision_options
    ),
    Command(
        "delete_agent",
        ["delete-agent", "da"],
        "Delete agent",
        delete_agent,
        ArgumentsEnum.REQUIRED,
        [],
        delete_agent_options
    ),
    Command(
        "update_agent",
        ["update-agent", "ua"],
        "Update agent by ID or name",
        update_agent,
        ArgumentsEnum.REQUIRED,
        [],
        update_agent_options
    ),
    # Tools
    Command(
        "create_tool",
        ["create-tool", "ct"],
        "Create tool",
        create_tool,
        ArgumentsEnum.REQUIRED,
        [],
        create_tool_options
    ),
    Command(
        "list_tools",
        ["list-tools", "lt"],
        "List tools",
        list_tools,
        ArgumentsEnum.REQUIRED,
        [],
        list_tools_options
    ),
    Command(
        "get_tool",
        ["get-tool", "gt"],
        "Get tool",
        get_tool,
        ArgumentsEnum.REQUIRED,
        [],
        get_tool_options
    ),
    #Command(
    #    "export_tool",
    #    ["export-tool", "et"],
    #    "Export tool",
    #    export_tool,
    #    ArgumentsEnum.REQUIRED,
    #    [],
    #    export_tool_options
    #),
    Command(
        "delete_tool",
        ["delete-tool", "dt"],
        "Delete tool",
        delete_tool,
        ArgumentsEnum.REQUIRED,
        [],
        delete_tool_options
    ),
    Command(
        "update_tool",
        ["update-tool", "ut"],
        "Update tool",
        update_tool,
        ArgumentsEnum.REQUIRED,
        [],
        update_tool_options
    ),
    Command(
        "publish_tool_revision",
        ["publish-tool-revision", "ptr"],
        "Publish tool revision",
        publish_tool_revision,
        ArgumentsEnum.REQUIRED,
        [],
        publish_tool_revision_options
    ),
    Command(
        "get_parameter",
        ["get-parameter", "gp"],
        "Get tool parameter",
        get_parameter,
        ArgumentsEnum.REQUIRED,
        [],
        get_parameter_options
    ),
    Command(
        "set_parameter",
        ["set-parameter", "sp"],
        "Set tool parameter",
        set_parameter,
        ArgumentsEnum.REQUIRED,
        [],
        set_parameter_options
    ),
    # reasoning-strategies
    Command(
        "list_reasoning_strategies",
        ["list-reasoning-strategies", "lrs"],
        "List reasoning strategies",
        list_reasoning_strategies,
        ArgumentsEnum.REQUIRED,
        [],
        list_reasoning_strategies_options
    ),
    Command(
        "create_reasoning_strategy",
        ["create-reasoning-strategy", "crs"],
        "Create reasoning strategy",
        create_reasoning_strategy,
        ArgumentsEnum.REQUIRED,
        [],
        create_reasoning_strategy_options
    ),
    Command(
        "update_reasoning_strategy",
        ["update-reasoning-strategy", "urs"],
        "Update reasoning strategy",
        update_reasoning_strategy,
        ArgumentsEnum.REQUIRED,
        [],
        update_reasoning_strategy_options
    ),
    Command(
        "get_reasoning_strategy",
        ["get-reasoning-strategy", "grs"],
        "Get reasoning strategy",
        get_reasoning_strategy,
        ArgumentsEnum.REQUIRED,
        [],
        get_reasoning_strategy_options
    ),
    # Agentic process definition
    # processes
    Command(
        "create_process",
        ["create-process", "cp"],
        "Create process",
        create_process,
        ArgumentsEnum.REQUIRED,
        [],
        create_process_options
    ),
    Command(
        "update_process",
        ["update-process", "up"],
        "Update process",
        update_process,
        ArgumentsEnum.REQUIRED,
        [],
        update_process_options
    ),
    Command(
        "get_process",
        ["get-process", "gp"],
        "Get process",
        get_process,
        ArgumentsEnum.REQUIRED,
        [],
        get_process_options
    ),
    Command(
        "list_processes",
        ["list-processes", "lp"],
        "List processes",
        list_processes,
        ArgumentsEnum.REQUIRED,
        [],
        list_processes_options
    ),
    Command(
        "list_processes_instances",
        ["list-processes-instances", "lpi"],
        "List processes instances",
        list_processes_instances,
        ArgumentsEnum.REQUIRED,
        [],
        list_processes_instances_options
    ),
    Command(
        "delete_process",
        ["delete-process", "dp"],
        "Delete process",
        delete_process,
        ArgumentsEnum.REQUIRED,
        [],
        delete_process_options
    ),
    Command(
        "publish_process_revision",
        ["publish-process-revision", "ppr"],
        "Publish process revision",
        publish_process_revision,
        ArgumentsEnum.REQUIRED,
        [],
        publish_process_revision_options
    ),
    # tasks
    Command(
        "create_task",
        ["create-task", "ctsk"],
        "Create task",
        create_task,
        ArgumentsEnum.REQUIRED,
        [],
        create_task_options
    ),
    Command(
        "get_task",
        ["get-task", "gtsk"],
        "Get task",
        get_task,
        ArgumentsEnum.REQUIRED,
        [],
        get_task_options
    ),
    Command(
        "list_tasks",
        ["list-tasks", "ltsk"],
        "List tasks",
        list_tasks,
        ArgumentsEnum.REQUIRED,
        [],
        list_tasks_options
    ),
    Command(
        "update_task",
        ["update-task", "utsk"],
        "Update task",
        update_task,
        ArgumentsEnum.REQUIRED,
        [],
        update_task_options
    ),
    Command(
        "delete_task",
        ["delete-task", "dtsk"],
        "Delete task",
        delete_task,
        ArgumentsEnum.REQUIRED,
        [],
        delete_task_options
    ),
    Command(
        "publish_task_revision",
        ["publish-task-revision", "ptskr"],
        "Publish task revision",
        publish_task_revision,
        ArgumentsEnum.REQUIRED,
        [],
        publish_task_revision_options
    ),
    # process instances
    Command(
        "start_instance",
        ["start-instance", "si"],
        "Start process instance",
        start_instance,
        ArgumentsEnum.REQUIRED,
        [],
        start_instance_options
    ),
    Command(
        "abort_instance",
        ["abort-instance", "ai"],
        "Abort process instance",
        abort_instance,
        ArgumentsEnum.REQUIRED,
        [],
        abort_instance_options
    ),
    Command(
        "get_instance",
        ["get-instance", "gi"],
        "Get process instance",
        get_instance,
        ArgumentsEnum.REQUIRED,
        [],
        get_instance_options
    ),
    Command(
        "get_instance_history",
        ["get-instance-history", "gih"],
        "Get process instance history",
        get_instance_history,
        ArgumentsEnum.REQUIRED,
        [],
        get_instance_history_options
    ),
    Command(
        "get_thread_information",
        ["get-thread-information", "gti"],
        "Get thread information",
        get_thread_information,
        ArgumentsEnum.REQUIRED,
        [],
        get_thread_information_options
    ),
    Command(
        "send_user_signal",
        ["send-user-signal", "sus"],
        "Send user signal to process instance",
        send_user_signal,
        ArgumentsEnum.REQUIRED,
        [],
        send_user_signal_options
    ),
    # knowledge bases
    Command(
        "create_kb",
        ["create-kb", "ckb"],
        "Create knowledge base",
        create_kb,
        ArgumentsEnum.REQUIRED,
        [],
        create_kb_options
    ),
    Command(
        "get_kb",
        ["get-kb", "gkb"],
        "Get knowledge base",
        get_kb,
        ArgumentsEnum.REQUIRED,
        [],
        get_kb_options
    ),
    Command(
        "list_kbs",
        ["list-kbs", "lkb"],
        "List knowledge bases",
        list_kbs,
        ArgumentsEnum.REQUIRED,
        [],
        list_kbs_options
    ),
    Command(
        "delete_kb",
        ["delete-kb", "dkb"],
        "Delete knowledge base",
        delete_kb,
        ArgumentsEnum.REQUIRED,
        [],
        delete_kb_options
    ),
    Command(
        "list_jobs",
        ["list-jobs", "lj"],
        "List runtime jobs",
        list_jobs,
        ArgumentsEnum.REQUIRED,
        [],
        list_jobs_options
    ),
]
