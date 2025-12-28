from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.options import DETAIL_OPTION, PROJECT_NAME_OPTION, PROJECT_ID_OPTION, SUBSCRIPTION_TYPE_OPTION, \
    USAGE_LIMIT_USAGE_UNIT_OPTION, USAGE_LIMIT_SOFT_LIMIT_OPTION, USAGE_LIMIT_HARD_LIMIT_OPTION, \
    USAGE_LIMIT_RENEWAL_STATUS_OPTION, PROJECT_DESCRIPTION_OPTION
from pygeai.cli.texts.help import ORGANIZATION_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.plugins.clients import PluginClient
from pygeai.core.utils.console import Console
from pygeai.organization.clients import OrganizationClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(organization_commands, ORGANIZATION_HELP_TEXT)
    Console.write_stdout(help_text)


def list_assistants(option_list: list):
    organization_id = None
    project_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization_id":
            organization_id = option_arg
        if option_flag.name == "project_id":
            project_id = option_arg

        if not organization_id and project_id:
            raise MissingRequirementException("Organization ID and Project ID are required.")

    client = PluginClient()
    result = client.list_assistants(organization_id=organization_id, project_id=project_id)

    Console.write_stdout(f"Assistant list: \n{result}")


assistants_list_options = [
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "UUID of the organization",
        True
    ),
    Option(
        "project_id",
        ["--project-id", "--pid"],
        "UUID of the project",
        True
    ),
]


def get_project_list(option_list: list):
    detail = "summary"
    name = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "detail":
            detail = option_arg
        if option_flag.name == "name":
            name = option_arg

    client = OrganizationClient()
    result = client.get_project_list(detail, name)
    Console.write_stdout(f"Project list: \n{result}")


project_list_options = [
    DETAIL_OPTION,
    PROJECT_NAME_OPTION,
]


def get_project_detail(option_list: list):
    project_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project detail without project-id")

    client = OrganizationClient()
    result = client.get_project_data(project_id=project_id)
    Console.write_stdout(f"Project detail: \n{result}")


project_detail_options = [
    PROJECT_ID_OPTION,
]


def create_project(option_list: list):
    name = None
    email = None
    description = None
    subscription_type = None
    usage_unit = None
    soft_limit = None
    hard_limit = None
    renewal_status = None
    usage_limit = {}

    for option_flag, option_arg in option_list:
        if option_flag.name == "name":
            name = option_arg

        if option_flag.name == "description":
            description = option_arg

        if option_flag.name == "admin_email":
            email = option_arg

        if option_flag.name == "subscription_type":
            subscription_type = option_arg

        if option_flag.name == "usage_unit":
            usage_unit = option_arg

        if option_flag.name == "soft_limit":
            soft_limit = option_arg

        if option_flag.name == "hard_limit":
            hard_limit = option_arg

        if option_flag.name == "renewal_status":
            renewal_status = option_arg

    if subscription_type or usage_unit or soft_limit or hard_limit or renewal_status:
        usage_limit.update({
            "subscriptionType": subscription_type,
            "usageUnit": usage_unit,
            "softLimit": soft_limit,
            "hardLimit": hard_limit,
            "renewalStatus": renewal_status
        })

    if not (name and email):
        raise MissingRequirementException("Cannot create project without name and administrator's email")

    client = OrganizationClient()
    result = client.create_project(name, email, description)
    Console.write_stdout(f"New project: \n{result}")


create_project_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Name of the new project",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of the new project",
        True
    ),
    Option(
        "admin_email",
        ["--email", "-e"],
        "Project administrator's email",
        True
    ),
    SUBSCRIPTION_TYPE_OPTION,
    USAGE_LIMIT_USAGE_UNIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def update_project(option_list: list):
    project_id = None
    name = None
    description = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg

        if option_flag.name == "name":
            name = option_arg

        if option_flag.name == "description":
            description = option_arg

    if not (project_id and name):
        raise MissingRequirementException("Cannot update project without project-id and/or name")

    client = OrganizationClient()
    result = client.update_project(project_id, name, description)
    Console.write_stdout(f"Updated project: \n{result}")


update_project_options = [
    PROJECT_ID_OPTION,
    PROJECT_NAME_OPTION,
    PROJECT_DESCRIPTION_OPTION,
]


def delete_project(option_list: list):
    project_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg

    if not project_id:
        raise MissingRequirementException("Cannot delete project without project-id")

    client = OrganizationClient()
    result = client.delete_project(project_id)
    Console.write_stdout(f"Deleted project: \n{result}")


delete_project_options = [
    PROJECT_ID_OPTION,
]


def get_project_tokens(option_list: list):
    project_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "project_id":
            project_id = option_arg

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project tokens without project-id")

    client = OrganizationClient()
    result = client.get_project_tokens(project_id)
    Console.write_stdout(f"Project tokens: \n{result}")


get_project_tokens_options = [
    PROJECT_ID_OPTION,
]


def export_request_data(option_list: list):
    assistant_name = None
    status = None
    skip = 0
    count = 0
    for option_flag, option_arg in option_list:
        if option_flag.name == "assistant_name":
            assistant_name = option_arg

        if option_flag.name == "status":
            status = option_arg

        if option_flag.name == "skip":
            skip = option_arg

        if option_flag.name == "count":
            count = option_arg

    client = OrganizationClient()
    result = client.export_request_data(assistant_name, status, skip, count)
    Console.write_stdout(f"Request data: \n{result}")


export_request_data_options = [
    Option(
        "assistant_name",
        ["--assistant-name"],
        "string: Assistant name (optional)",
        True
    ),
    Option(
        "status",
        ["--status"],
        "string: Status (optional)",
        True
    ),
    Option(
        "skip",
        ["--skip"],
        "integer: Number of entries to skip",
        True
    ),
    Option(
        "count",
        ["--count"],
        "integer: Number of entries to retrieve",
        True
    )
]

organization_commands = [
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
        "assistants_list",
        ["list-assistants"],
        "List assistant information",
        list_assistants,
        ArgumentsEnum.OPTIONAL,
        [],
        assistants_list_options
    ),
    Command(
        "project_list",
        ["list-projects"],
        "List project information",
        get_project_list,
        ArgumentsEnum.OPTIONAL,
        [],
        project_list_options
    ),
    Command(
        "project_detail",
        ["get-project"],
        "Get project information",
        get_project_detail,
        ArgumentsEnum.REQUIRED,
        [],
        project_detail_options
    ),
    Command(
        "create_project",
        ["create-project"],
        "Create new project",
        create_project,
        ArgumentsEnum.REQUIRED,
        [],
        create_project_options
    ),
    Command(
        "update_project",
        ["update-project"],
        "Update existing project",
        update_project,
        ArgumentsEnum.REQUIRED,
        [],
        update_project_options
    ),
    Command(
        "delete_project",
        ["delete-project"],
        "Delete existing project",
        delete_project,
        ArgumentsEnum.REQUIRED,
        [],
        delete_project_options
    ),
    Command(
        "get_project_tokens",
        ["get-tokens"],
        "Get project tokens",
        get_project_tokens,
        ArgumentsEnum.REQUIRED,
        [],
        get_project_tokens_options
    ),
    Command(
        "export_request_data",
        ["export-request"],
        "Export request data",
        export_request_data,
        ArgumentsEnum.OPTIONAL,
        [],
        export_request_data_options
    ),
]
