from pygeai.cli.commands import Command, ArgumentsEnum, Option
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import LLM_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.llm.clients import LlmClient
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(llm_commands, LLM_HELP_TEXT)
    Console.write_stdout(help_text)


def get_provider_list():
    client = LlmClient()
    result = client.get_provider_list()
    Console.write_stdout(f"Provider list: \n{result}")


def get_provider_data(option_list: list):
    provider_name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "provider_name":
            provider_name = option_arg

    if not provider_name:
        raise MissingRequirementException("Cannot retrieve provider data without name")

    client = LlmClient()
    result = client.get_provider_data(provider_name=provider_name)
    Console.write_stdout(f"Provider detail: \n{result}")


get_provider_data_options = [
    Option(
        "provider_name",
        ["--provider-name", "--pn"],
        "LLM Provider name (required)",
        True
    ),
]


def get_provider_models(option_list: list):
    provider_name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "provider_name":
            provider_name = option_arg

    if not provider_name:
        raise MissingRequirementException("Cannot retrieve provider models without name")

    client = LlmClient()
    result = client.get_provider_models(provider_name=provider_name)
    Console.write_stdout(f"Provider models: \n{result}")


get_provider_models_options = [
    Option(
        "provider_name",
        ["--provider-name", "--pn"],
        "LLM Provider name (required)",
        True
    ),
]


def get_model_data(option_list: list):
    provider_name = None
    model_name = None
    model_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "provider_name":
            provider_name = option_arg
        if option_flag.name == "model_name":
            model_name = option_arg
        if option_flag.name == "model_id":
            model_id = option_arg

    if not (provider_name and (model_name or model_id)):
        raise MissingRequirementException("Cannot retrieve model data without provider name and model id or name.")

    client = LlmClient()
    result = client.get_model_data(
        provider_name=provider_name,
        model_name=model_name or model_id
    )
    Console.write_stdout(f"Model details: \n{result}")


get_model_data_options = [
    Option(
        "provider_name",
        ["--provider-name", "--pn"],
        "LLM Provider name (required)",
        True
    ),
    Option(
        "model_name",
        ["--model-name", "--mn"],
        "LLM Model name",
        True
    ),
    Option(
        "model_id",
        ["--model-id", "--mid"],
        "LLM Model ID",
        True
    ),

]


llm_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "list_providers",
        ["list-providers", "lp"],
        "Retrieve providers list",
        get_provider_list,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "get_provider",
        ["get-provider", "gp"],
        "Retrieve provider data",
        get_provider_data,
        ArgumentsEnum.REQUIRED,
        [],
        get_provider_data_options
    ),
    Command(
        "list_models",
        ["list-models", "lm"],
        "Retrieve provider models",
        get_provider_models,
        ArgumentsEnum.REQUIRED,
        [],
        get_provider_models_options
    ),
    Command(
        "get_model",
        ["get-model", "gm"],
        "Retrieve model data",
        get_model_data,
        ArgumentsEnum.REQUIRED,
        [],
        get_model_data_options
    ),

]
