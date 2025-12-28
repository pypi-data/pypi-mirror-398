from pygeai.auth.clients import AuthClient
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import AUTH_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(auth_commands, AUTH_HELP_TEXT)
    Console.write_stdout(help_text)


def get_oauth2_access_token(option_list: list):
    client_id = None
    username = None
    password = None
    scope = "gam_user_data gam_user_roles"
    for option_flag, option_arg in option_list:
        if option_flag.name == "client_id":
            client_id = option_arg
        if option_flag.name == "username":
            username = option_arg
        if option_flag.name == "password":
            password = option_arg
        if option_flag.name == "scope":
            scope = option_arg

    if not (client_id and username and password):
        raise MissingRequirementException("Cannot obtain Oauth2 access token without client_id, username and password")

    client = AuthClient()
    result = client.get_oauth2_access_token(
        client_id=client_id,
        username=username,
        password=password,
        scope=scope
    )
    Console.write_stdout(f"Authorized projects detail: \n{result}")


get_oauth2_access_token_options = [
    Option(
        "client_id",
        ["--client-id", "--cid"],
        "The client identifier provided by Globant.",
        True
    ),
    Option(
        "username",
        ["--username", "-u"],
        "Username for authentication.",
        True
    ),
    Option(
        "password",
        ["--password", "-p"],
        "Password for authentication.",
        True
    ),
    Option(
        "scope",
        ["--scope", "-s"],
        "Space-separated list of requested scopes. (Optional)",
        True
    ),

]


def get_user_profile_information(option_list: list):
    access_token = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "access_token":
            access_token = option_arg

    client = AuthClient()
    result = client.get_user_profile_information(access_token=access_token)
    Console.write_stdout(f"User profile information: \n{result}")


get_user_profile_information_options = [
    Option(
        "access_token",
        ["--access-token", "--token"],
        "Token obtained with the --get-access-token option",
        True
    ),
]


auth_commands = [
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
        "get_oauth2_access_token",
        ["get-access-token", "gat"],
        "Get Oauth acess token for Globant Enterprise AI instance",
        get_oauth2_access_token,
        ArgumentsEnum.REQUIRED,
        [],
        get_oauth2_access_token_options
    ),
    Command(
        "get_user_profile_information_options",
        ["get-user-information", "get-user-info", "gui"],
        "Retrieve user profile information",
        get_user_profile_information_options,
        ArgumentsEnum.REQUIRED,
        [],
        get_user_profile_information_options
    ),
]
