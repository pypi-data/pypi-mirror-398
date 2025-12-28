from pygeai.cli.commands import Command, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.options import ORGANIZATION_OPTION, SUBSCRIPTION_TYPE_OPTION, USAGE_LIMIT_USAGE_UNIT_OPTION, \
    USAGE_LIMIT_SOFT_LIMIT_OPTION, USAGE_LIMIT_HARD_LIMIT_OPTION, USAGE_LIMIT_RENEWAL_STATUS_OPTION, \
    USAGE_LIMIT_ID_OPTION, PROJECT_OPTION
from pygeai.cli.texts.help import USAGE_LIMIT_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.utils.console import Console
from pygeai.organization.limits.clients import UsageLimitClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(usage_limit_commands, USAGE_LIMIT_HELP_TEXT)
    Console.write_stdout(help_text)


def set_organization_usage_limit(option_list: list):
    organization = None
    subscription_type = None
    usage_unit = None
    soft_limit = None
    hard_limit = None
    renewal_status = None
    usage_limit = {}

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
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

    if not organization:
        raise MissingRequirementException("Cannot set usage limit for organization without organization ID")

    client = UsageLimitClient()
    result = client.set_organization_usage_limit(
        organization=organization,
        usage_limit=usage_limit
    )
    Console.write_stdout(f"Organization usage limit: \n{result}")


set_organization_usage_limit_options = [
    ORGANIZATION_OPTION,
    SUBSCRIPTION_TYPE_OPTION,
    USAGE_LIMIT_USAGE_UNIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def get_organization_latest_usage_limit(option_list: list):
    organization = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg

    if not organization:
        raise MissingRequirementException("Cannot get latest usage limit for organization without organization ID")

    client = UsageLimitClient()
    result = client.get_organization_latest_usage_limit(
        organization=organization,
    )
    Console.write_stdout(f"Organization usage limit: \n{result}")


get_organization_latest_usage_limit_options = [
    ORGANIZATION_OPTION,
]


def get_all_usage_limits_from_organization(option_list: list):
    organization = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg

    if not organization:
        raise MissingRequirementException("Cannot get all usage limits for organization without organization ID")

    client = UsageLimitClient()
    result = client.get_all_usage_limits_from_organization(
        organization=organization,
    )
    Console.write_stdout(f"Organization usage limits: \n{result}")


get_all_usage_limits_from_organization_options = [
    ORGANIZATION_OPTION,
]


def delete_usage_limit_from_organization(option_list: list):
    organization = None
    limit_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "limit_id":
            limit_id = option_arg

    if not (organization and limit_id):
        raise MissingRequirementException("Cannot delete usage limit for organization without organization ID and limit ID")

    client = UsageLimitClient()
    result = client.delete_usage_limit_from_organization(
        organization=organization,
        limit_id=limit_id
    )
    Console.write_stdout(f"Deleted usage limit: \n{result}")


delete_usage_limit_from_organization_options = [
    ORGANIZATION_OPTION,
    USAGE_LIMIT_ID_OPTION
]


def update_organization_usage_limit(option_list: list):
    organization = None
    limit_id = None
    hard_limit = None
    soft_limit = None
    renewal_status = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "limit_id":
            limit_id = option_arg
        if option_flag.name == "hard_limit":
            hard_limit = option_arg
        if option_flag.name == "soft_limit":
            soft_limit = option_arg
        if option_flag.name == "renewal_status":
            renewal_status = option_arg

    if not (organization and limit_id):
        raise MissingRequirementException("Cannot update usage limit for organization without organization ID and limit ID")

    if not (hard_limit or soft_limit or renewal_status):
        raise MissingRequirementException("At least one of the following parameters must be define to update usage limit: "
                                          "--soft-limit, --hard-limit or --renewal-status")

    if soft_limit:
        set_organization_soft_limit(organization, limit_id, soft_limit)

    if hard_limit:
        set_organization_hard_limit(organization, limit_id, hard_limit)

    if renewal_status:
        set_organization_renewal_status(organization, limit_id, renewal_status)


update_organization_usage_limit_options = [
    ORGANIZATION_OPTION,
    USAGE_LIMIT_ID_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def set_organization_hard_limit(organization, limit_id, hard_limit):
    client = UsageLimitClient()
    result = client.set_organization_hard_limit(
        organization=organization,
        limit_id=limit_id,
        hard_limit=hard_limit
    )
    Console.write_stdout(f"Organization hard limit: \n{result}")


def set_organization_soft_limit(organization, limit_id, soft_limit):
    client = UsageLimitClient()
    result = client.set_organization_soft_limit(
        organization=organization,
        limit_id=limit_id,
        soft_limit=soft_limit
    )
    Console.write_stdout(f"Organization soft limit: \n{result}")


def set_organization_renewal_status(organization, limit_id, renewal_status):
    client = UsageLimitClient()
    result = client.set_organization_renewal_status(
        organization=organization,
        limit_id=limit_id,
        renewal_status=renewal_status
    )
    Console.write_stdout(f"Organization renewal status: \n{result}")


def set_project_usage_limit(option_list: list):
    organization = None
    project = None
    subscription_type = None
    usage_unit = None
    soft_limit = None
    hard_limit = None
    renewal_status = None
    usage_limit = {}

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg

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

    if not (organization and project):
        raise MissingRequirementException("Cannot set usage limit for project without organization and project ID")

    client = UsageLimitClient()
    result = client.set_project_usage_limit(
        organization=organization,
        project=project,
        usage_limit=usage_limit
    )
    Console.write_stdout(f"Project usage limit: \n{result}")


set_project_usage_limit_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION,
    SUBSCRIPTION_TYPE_OPTION,
    USAGE_LIMIT_USAGE_UNIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def get_all_usage_limits_from_project(option_list: list):
    organization = None
    project = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg

    if not (organization and project):
        raise MissingRequirementException("Cannot get usage limits for project without organization and project ID")

    client = UsageLimitClient()
    result = client.get_all_usage_limits_from_project(
        organization=organization,
        project=project
    )
    Console.write_stdout(f"Project usage limits: \n{result}")


get_all_usage_limits_from_project_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION
]


def get_latest_usage_limit_from_project(option_list: list):
    organization = None
    project = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg

    if not (organization and project):
        raise MissingRequirementException("Cannot get latest usage limit for project without organization and project ID")

    client = UsageLimitClient()
    result = client.get_latest_usage_limit_from_project(
        organization=organization,
        project=project
    )
    Console.write_stdout(f"Project's latest usage limit: \n{result}")


get_latest_usage_limit_from_project_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION
]


def get_active_usage_limit_from_project(option_list: list):
    organization = None
    project = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg

    if not (organization and project):
        raise MissingRequirementException("Cannot get active usage limit for project without organization and project ID")

    client = UsageLimitClient()
    result = client.get_active_usage_limit_from_project(
        organization=organization,
        project=project
    )
    Console.write_stdout(f"Project's latest usage limit: \n{result}")


get_active_usage_limit_from_project_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION
]


def delete_usage_limit_from_project(option_list: list):
    organization = None
    project = None
    limit_id = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "limit_id":
            limit_id = option_arg

    if not (organization and project and limit_id):
        raise MissingRequirementException("Cannot delete usage limit for project without organization, project and limit ID")

    client = UsageLimitClient()
    result = client.delete_usage_limit_from_project(
        organization=organization,
        project=project,
        limit_id=limit_id
    )
    Console.write_stdout(f"Deleted usage limit: \n{result}")


delete_usage_limit_from_project_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION,
    USAGE_LIMIT_ID_OPTION
]


def update_project_usage_limit(option_list: list):
    organization = None
    project = None
    limit_id = None
    hard_limit = None
    soft_limit = None
    renewal_status = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "limit_id":
            limit_id = option_arg
        if option_flag.name == "hard_limit":
            hard_limit = option_arg
        if option_flag.name == "soft_limit":
            soft_limit = option_arg
        if option_flag.name == "renewal_status":
            renewal_status = option_arg

    if not (organization and project and limit_id):
        raise MissingRequirementException("Cannot update usage limit for project without organization ID, project ID and limit ID")

    if not (hard_limit or soft_limit or renewal_status):
        raise MissingRequirementException("At least one of the following parameters must be define to update usage limit: "
                                          "--soft-limit, --hard-limit or --renewal-status")

    if hard_limit:
        set_project_hard_limit(organization, project, limit_id, hard_limit)

    if soft_limit:
        set_project_soft_limit(organization, project, limit_id, soft_limit)

    if renewal_status:
        set_project_renewal_status(organization, project, limit_id, renewal_status)


update_project_usage_limit_options = [
    ORGANIZATION_OPTION,
    PROJECT_OPTION,
    USAGE_LIMIT_ID_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def set_project_hard_limit(organization, project, limit_id, hard_limit):
    client = UsageLimitClient()
    result = client.set_hard_limit_for_active_usage_limit_from_project(
        organization=organization,
        project=project,
        limit_id=limit_id,
        hard_limit=hard_limit
    )
    Console.write_stdout(f"Project hard limit: \n{result}")


def set_project_soft_limit(organization, project, limit_id, soft_limit):
    client = UsageLimitClient()
    result = client.set_soft_limit_for_active_usage_limit_from_project(
        organization=organization,
        project=project,
        limit_id=limit_id,
        soft_limit=soft_limit
    )
    Console.write_stdout(f"Project soft limit: \n{result}")


def set_project_renewal_status(organization, project, limit_id, renewal_status):
    client = UsageLimitClient()
    result = client.set_project_renewal_status(
        organization=organization,
        project=project,
        limit_id=limit_id,
        renewal_status=renewal_status
    )
    Console.write_stdout(f"Project renewal status: \n{result}")


usage_limit_commands = [
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
        "set_organization_limit",
        ["set-organization-limit", "set-org-lim"],
        "Set organization usage limit",
        set_organization_usage_limit,
        ArgumentsEnum.REQUIRED,
        [],
        set_organization_usage_limit_options
    ),
    Command(
        "get_organization_limit",
        ["get-latest-organization-limit", "get-latest-org-lim"],
        "Get latest organization usage limit",
        get_organization_latest_usage_limit,
        ArgumentsEnum.REQUIRED,
        [],
        get_organization_latest_usage_limit_options
    ),
    Command(
        "get_all_organization_limits",
        ["get-all-organization-limit", "get-all-org-lim"],
        "Get all organization usage limit",
        get_all_usage_limits_from_organization,
        ArgumentsEnum.REQUIRED,
        [],
        get_all_usage_limits_from_organization_options
    ),
    Command(
        "delete_organization_usage_limit",
        ["delete-organization-limit", "del-org-lim"],
        "Delete organization usage limit",
        delete_usage_limit_from_organization,
        ArgumentsEnum.REQUIRED,
        [],
        delete_usage_limit_from_organization_options
    ),
    Command(
        "update_organization_usage_limit",
        ["update-organization-limit", "up-org-lim"],
        "Update organization usage limit",
        update_organization_usage_limit,
        ArgumentsEnum.REQUIRED,
        [],
        update_organization_usage_limit_options
    ),
    Command(
        "set_project_usage_limit",
        ["set-project-limit", "set-proj-lim"],
        "Set project usage limit",
        set_project_usage_limit,
        ArgumentsEnum.REQUIRED,
        [],
        set_project_usage_limit_options
    ),
    Command(
        "get_all_project_usage_limit",
        ["get-all-project-limit", "get-all-proj-lim"],
        "Get all usage limits for project",
        get_all_usage_limits_from_project,
        ArgumentsEnum.REQUIRED,
        [],
        get_all_usage_limits_from_project_options
    ),
    Command(
        "get_latest_usage_limit_from_project",
        ["get-latest-project-limit", "get-latest-proj-lim"],
        "Get latest usage limit for project",
        get_latest_usage_limit_from_project,
        ArgumentsEnum.REQUIRED,
        [],
        get_latest_usage_limit_from_project_options
    ),
    Command(
        "get_active_usage_limit_from_project",
        ["get-active-project-limit", "get-active-proj-lim"],
        "Get active usage limit for project",
        get_active_usage_limit_from_project,
        ArgumentsEnum.REQUIRED,
        [],
        get_active_usage_limit_from_project_options
    ),
    Command(
        "delete_usage_limit_from_project",
        ["delete-project-limit", "del-proj-lim"],
        "Get active usage limit for project",
        delete_usage_limit_from_project,
        ArgumentsEnum.REQUIRED,
        [],
        delete_usage_limit_from_project_options
    ),
    Command(
        "update_project_usage_limit",
        ["update-project-limit", "up-proj-lim"],
        "Update project usage limit",
        update_project_usage_limit,
        ArgumentsEnum.REQUIRED,
        [],
        update_project_usage_limit_options
    )

]
