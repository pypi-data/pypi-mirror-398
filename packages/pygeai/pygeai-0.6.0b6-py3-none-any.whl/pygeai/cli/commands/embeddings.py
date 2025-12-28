from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import EMBEDDINGS_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.embeddings.clients import EmbeddingsClient
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(embeddings_commands, EMBEDDINGS_HELP_TEXT)
    Console.write_stdout(help_text)


def generate_embeddings(option_list: list):
    model = None
    encoding_format = None
    dimensions = None
    user = None
    input_type = None
    timeout = None
    cache = None
    input_list = list()

    for option_flag, option_arg in option_list:
        if option_flag.name == "model":
            model = option_arg
        if option_flag.name == "input":
            input_list.append(option_arg)
        if option_flag.name == "encoding_format":
            encoding_format = option_arg
        if option_flag.name == "dimensions":
            dimensions = option_arg
        if option_flag.name == "user":
            user = option_arg
        if option_flag.name == "input_type":
            input_type = option_arg
        if option_flag.name == "timeout":
            timeout = option_arg
        if option_flag.name == "cache":
            if not str(option_arg).isdigit() or int(option_arg) not in [0, 1]:
                raise WrongArgumentError("If specified, cache must be 0 or 1")

            cache = bool(int(option_arg))

    if not (model and any(input_list)):
        raise MissingRequirementException("Cannot generate embeddings without specifying model and at least one input")

    client = EmbeddingsClient()
    result = client.generate_embeddings(
        input_list=input_list,
        model=model,
        encoding_format=encoding_format,
        dimensions=dimensions,
        user=user,
        input_type=input_type,
        timeout=timeout,
        cache=cache
    )
    Console.write_stdout(f"Embeddings detail: \n{result}")


generate_embeddings_options = [
    Option(
        "input",
        ["--input", "-i"],
        "string: Input to embed, encoded as a string. To embed multiple inputs in a single request, pass the string inputs "
        "multiple times using -i. The input must not exceed the max input tokens for the model and cannot be an empty string",
        True
    ),
    Option(
        "model",
        ["--model", "-m"],
        "string: provider/modelId to use",
        True
    ),
    Option(
        "encoding_format",
        ["--encoding-format", "--enc-for"],
        "string: The format to return the embeddings. It can be either float (default) or base64 (optional)",
        True
    ),
    Option(
        "dimensions",
        ["--dimensions", "--dim"],
        "integer: The number of dimensions the resulting output embeddings should have. Only supported in text-embedding-3* and later models (optional)",
        True
    ),
    Option(
        "user",
        ["--user", "-u"],
        "string: A unique identifier representing your end-user",
        True
    ),
    Option(
        "input_type",
        ["--input-type", "--it"],
        "string: Defines how the input data will be used when generating embeddings (optional)",
        True
    ),
    Option(
        "timeout",
        ["--timeout", "-t"],
        "integer: The maximum time, in seconds, to wait for the API to respond. Defaults to 600 seconds",
        True
    ),
    Option(
        "cache",
        ["--cache"],
        "Enable X-Saia-Cache-Enabled to cache the embeddings for the model; it applies by Organization/Project."
        "1 to set to True and 0 to false. 0 is default",
        True
    ),

]


embeddings_commands = [
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
        "generate_embeddings",
        ["generate", "gen"],
        "Get embeddings",
        generate_embeddings,
        ArgumentsEnum.REQUIRED,
        [],
        generate_embeddings_options
    ),
]
