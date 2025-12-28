from pygeai.cli.commands import Option


DETAIL_OPTION = Option(
    "detail",
    ["--detail", "-d"],
    "Defines the level of detail required. The available options are summary (default) or full (optional).",
    True
)

PROJECT_NAME_OPTION = Option(
    "name",
    ["--name", "-n"],
    "Name of the project",
    True
)

PROJECT_DESCRIPTION_OPTION = Option(
    "description",
    ["--description", "-d"],
    "Description of the new project",
    True
)

PROJECT_ID_OPTION = Option(
    "project_id",
    ["--project-id", "--pid"],
    "GUID of the project (required)",
    True
)

ORGANIZATION_OPTION = Option(
    "organization",
    ["--organization", "--org", "-o"],
    "Organization ID (Required)",
    True
)

PROJECT_OPTION = Option(
    "project",
    ["--project", "--proj", "-p"],
    "Project ID (Required)",
    True
)

SUBSCRIPTION_TYPE_OPTION = Option(
    "subscription_type",
    ["--subscription-type"],
    "string: Options: Freemium, Daily, Weekly, Monthly)",
    True
)

USAGE_LIMIT_USAGE_UNIT_OPTION = Option(
    "usage_unit",
    ["--usage-unit"],
    "string: Options: Requests, Cost)",
    True
)

USAGE_LIMIT_SOFT_LIMIT_OPTION = Option(
    "soft_limit",
    ["--soft-limit"],
    "number: Soft limit for usage (lower threshold))",
    True
)

USAGE_LIMIT_HARD_LIMIT_OPTION = Option(
    "hard_limit",
    ["--hard-limit"],
    "number: Hard limit for usage (upper threshold)). Must be greater or equal to --soft-limit.",
    True
)

USAGE_LIMIT_RENEWAL_STATUS_OPTION = Option(
    "renewal_status",
    ["--renewal-status"],
    "string: Options: Renewable, NonRenewable). If --subscription-type is Freemium, this must be NonRenewable",
    True
)

USAGE_LIMIT_ID_OPTION = Option(
    "limit_id",
    ["--limit-id", "--lid"],
    "Usage limit ID (Required)",
    True
)