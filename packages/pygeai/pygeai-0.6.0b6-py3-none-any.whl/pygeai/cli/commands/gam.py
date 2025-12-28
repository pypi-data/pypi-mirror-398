from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import GAM_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console
from pygeai.gam.clients import GAMClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(gam_commands, GAM_HELP_TEXT)
    Console.write_stdout(help_text)


def generate_signin_url(option_list: list):
    client_id = None
    redirect_uri = None
    scope = "gam_user_data"
    state = None
    response_type = "code"

    for option_flag, option_arg in option_list:
        if option_flag.name == "client_id":
            client_id = option_arg
        if option_flag.name == "redirect_uri":
            redirect_uri = option_arg
        if option_flag.name == "scope":
            scope = option_arg
        if option_flag.name == "state":
            state = option_arg
        if option_flag.name == "response_type":
            response_type = option_arg

    if not all([client_id, redirect_uri, state]):
        raise MissingRequirementException("client_id, redirect_uri, and state are required for generating signin URL")

    client = GAMClient()
    result = client.generate_signing_url(
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        response_type=response_type
    )
    Console.write_stdout(f"GAM Signin URL: \n{result}")


generate_signin_url_options = [
    Option(
        "client_id",
        ["--client-id", "--cid"],
        "Application Client ID.",
        True
    ),
    Option(
        "redirect_uri",
        ["--redirect-uri", "--ru"],
        "Callback URL configured in the application (must match the one in GAM).",
        True
    ),
    Option(
        "scope",
        ["--scope", "-s"],
        'Scope of the user account to access. Default: "gam_user_data"',
        True
    ),
    Option(
        "state",
        ["--state", "--st"],
        "Random string to store the status before the request.",
        True
    ),
    Option(
        "response_type",
        ["--response-type", "--rt"],
        'Response type for the signin request. Default: "code"',
        True
    )
]


def get_access_token(option_list: list):
    client_id = None
    client_secret = None
    grant_type = "password"
    authentication_type_name = "local"
    scope = "gam_user_data"
    username = None
    password = None
    initial_properties = None
    repository = None
    request_token_type = "OAuth"

    for option_flag, option_arg in option_list:
        if option_flag.name == "client_id":
            client_id = option_arg
        if option_flag.name == "client_secret":
            client_secret = option_arg
        if option_flag.name == "grant_type":
            grant_type = option_arg
        if option_flag.name == "authentication_type_name":
            authentication_type_name = option_arg
        if option_flag.name == "scope":
            scope = option_arg
        if option_flag.name == "username":
            username = option_arg
        if option_flag.name == "password":
            password = option_arg
        if option_flag.name == "initial_properties":
            initial_properties = option_arg
        if option_flag.name == "repository":
            repository = option_arg
        if option_flag.name == "request_token_type":
            request_token_type = option_arg

    if not ((client_id and client_secret) or (username and password)):
        raise MissingRequirementException("Cannot get access token without specifying valid credentials")

    client = GAMClient()
    result = client.get_access_token(
        client_id=client_id,
        client_secret=client_secret,
        grant_type=grant_type,
        authentication_type_name=authentication_type_name,
        scope=scope,
        username=username,
        password=password,
        initial_properties=initial_properties,
        repository=repository,
        request_token_type=request_token_type,
    )
    Console.write_stdout(f"GAM Access Token: \n{result}")


get_access_token_options = [
    Option(
        "client_id",
        ["--client-id", "--cid"],
        "Application Client ID.",
        True
    ),
    Option(
        "client_secret",
        ["--client-secret", "--cs"],
        "Application Client Secret.",
        True
    ),
    Option(
        "grant_type",
        ["--grant-type", "--gt"],
        'Grant type for authentication. Default: "password"',
        True
    ),
    Option(
        "authentication_type_name",
        ["--authentication-type-name", "--atn"],
        'Authentication type name. Default: "local"',
        True
    ),
    Option(
        "scope",
        ["--scope", "-s"],
        'Scope of the user account you want to access. gam_user_data+gam_user_roles. '
        'Valid scopes: gam_user_data, gam_user_additional_data, gam_user_roles, session_initial_prop, '
        'session_application_data, fullcontrol. Default: "gam_user_data"',
        True
    ),
    Option(
        "username",
        ["--username", "-u"],
        "Username of the user to be authenticated.",
        True
    ),
    Option(
        "password",
        ["--password", "-p"],
        "Password of the user to be authenticated.",
        True
    ),
    Option(
        "initial_properties",
        ["--initial-properties", "--ip"],
        "User custom properties array.",
        False
    ),
    Option(
        "repository",
        ["--repository", "-r"],
        "Only use if the IDP is multitenant.",
        False
    ),
    Option(
        "request_token_type",
        ["--request-token-type", "--rtt"],
        'Determines the token type to return and, based on that, the Security Policy to be applied. Default: "OAuth"',
        False
    )
]


def get_user_info(option_list: list):
    access_token = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "access_token":
            access_token = option_arg

    if not access_token:
        raise MissingRequirementException("Cannot get user info without the access token")

    client = GAMClient()
    result = client.get_user_info(
        access_token=access_token,
    )
    Console.write_stdout(f"GAM User info: \n{result}")


get_user_info_options = [
    Option(
        "access_token",
        ["--access-token", "--at"],
        "The access_token obtained in the previous request.",
        True
    ),
]


def refresh_access_token(option_list: list):
    client_id = None
    client_secret = None
    grant_type = "refresh_token"
    refresh_token = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "client_id":
            client_id = option_arg
        if option_flag.name == "client_secret":
            client_secret = option_arg
        if option_flag.name == "grant_type":
            grant_type = option_arg
        if option_flag.name == "refresh_token":
            refresh_token = option_arg

    if not ((client_id and client_secret) or refresh_token):
        raise MissingRequirementException("Cannot refresh access token without specifying valid credentials")

    client = GAMClient()
    result = client.refresh_access_token(
        client_id=client_id,
        client_secret=client_secret,
        grant_type=grant_type,
        refresh_token=refresh_token,
    )
    Console.write_stdout(f"GAM Access Token: \n{result}")


refresh_access_token_options = [
    Option(
        "client_id",
        ["--client-id", "--cid"],
        "Application Client ID.",
        True
    ),
    Option(
        "client_secret",
        ["--client-secret", "--cs"],
        "Application Client Secret.",
        True
    ),
    Option(
        "grant_type",
        ["--grant-type", "--gt"],
        'Grant type for authentication. Must be: "refresh_token"',
        True
    ),
    Option(
        "refresh_token",
        ["--refresh-token", "--rt"],
        'Refresh token.',
        True
    ),
]


def get_authentication_types():
    client = GAMClient()
    result = client.get_authentication_types()
    Console.write_stdout(f"GAM Authentication Types: \n{result}")


gam_commands = [
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
        "get_access_token",
        ["get-access-token", "gat"],
        "Get access token",
        get_access_token,
        ArgumentsEnum.REQUIRED,
        [],
        get_access_token_options
    ),
    Command(
        "get_user_info",
        ["get-user-info", "gui"],
        "Get user info",
        get_user_info,
        ArgumentsEnum.REQUIRED,
        [],
        get_user_info_options
    ),
    Command(
        "refresh_access_token",
        ["refresh-access-token", "rat"],
        "Refresh access token",
        refresh_access_token,
        ArgumentsEnum.REQUIRED,
        [],
        refresh_access_token_options
    ),
    Command(
        "generate_signin_url",
        ["generate-signin-url", "gsu"],
        "Generate signin URL for browser-based OAuth flow",
        generate_signin_url,
        ArgumentsEnum.REQUIRED,
        [],
        generate_signin_url_options
    )
    # Command(
    #     "get_authentication_types",
    #     ["get-authentication-types", "get-auth-types"],
    #     "Get authentication types",
    #     get_authentication_types,
    #     ArgumentsEnum.NOT_AVAILABLE,
    #     [],
    #     []
    # ),

]
