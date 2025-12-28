from pygeai.admin.clients import AdminClient
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import ADMIN_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(admin_commands, ADMIN_HELP_TEXT)
    Console.write_stdout(help_text)


def validate_api_token():
    client = AdminClient()
    result = client.validate_api_token()
    Console.write_stdout(f"API Token access detail: \n{result}")


def get_authorized_organizations():
    client = AdminClient()
    result = client.get_authorized_organizations()
    Console.write_stdout(f"Authorized organizations: \n{result}")


def get_authorized_projects_by_organization(option_list: list):
    organization = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg

    if not organization:
        raise MissingRequirementException("Cannot get authorized projects within organization without organization id")

    client = AdminClient()
    result = client.get_authorized_projects_by_organization(
        organization=organization
    )
    Console.write_stdout(f"Authorized projects detail: \n{result}")


authorized_projects_by_organization_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "ID of the organization.",
        True
    ),
]


def get_project_visibility(option_list: list):
    organization = None
    project = None
    access_token = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "access_token":
            access_token = option_arg

    if not (organization and project and access_token):
        raise MissingRequirementException("Cannot get project visibility for access token without specifying "
                                          "organization, project and access token.")

    client = AdminClient()
    result = client.get_project_visibility(
        organization=organization,
        project=project,
        access_token=access_token
    )
    Console.write_stdout(f"Project visibility detail: \n{result}")


project_visibility_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "ID of the organization.",
        True
    ),
    Option(
        "project",
        ["--project", "-p"],
        "ID of the project.",
        True
    ),
    Option(
        "access_token",
        ["--access-token", "--token", "--at"],
        "GAM access token.",
        True
    ),
]


def get_project_api_token(option_list: list):
    organization = None
    project = None
    access_token = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "access_token":
            access_token = option_arg

    if not (organization and project and access_token):
        raise MissingRequirementException("Cannot get project API Token without specifying "
                                          "organization, project and access token.")

    client = AdminClient()
    result = client.get_project_api_token(
        organization=organization,
        project=project,
        access_token=access_token
    )
    Console.write_stdout(f"Project API Token: \n{result}")


project_api_token_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "ID of the organization.",
        True
    ),
    Option(
        "project",
        ["--project", "-p"],
        "ID of the project.",
        True
    ),
    Option(
        "access_token",
        ["--access-token", "--token", "--at"],
        "GAM access token.",
        True
    ),
]


admin_commands = [
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
        "validate_api_token",
        ["validate-token", "vt"],
        "Validate API Token: Obtains organization and project information related to the provided apitoken.",
        validate_api_token,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "list_authorized_organizations",
        ["list-authorized-organizations", "auth-org"],
        "Obtain the list of organizations that a user is permitted to access.",
        get_authorized_organizations,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "list_authorized_projects",
        ["list-authorized-projects", "auth-proj"],
        "Obtain the list of projects that a user is permitted to access in a particular organization.",
        get_authorized_projects_by_organization,
        ArgumentsEnum.REQUIRED,
        [],
        authorized_projects_by_organization_options
    ),
    Command(
        "get_project_visibility",
        ["project-visibility", "pv"],
        "Determines if a GAM user has visibility of a project",
        get_project_visibility,
        ArgumentsEnum.REQUIRED,
        [],
        project_visibility_options
    ),
    Command(
        "get_project_api_token",
        ["project-token", "pt"],
        "Returns Project's API Token",
        get_project_api_token,
        ArgumentsEnum.REQUIRED,
        [],
        project_api_token_options
    ),
]
