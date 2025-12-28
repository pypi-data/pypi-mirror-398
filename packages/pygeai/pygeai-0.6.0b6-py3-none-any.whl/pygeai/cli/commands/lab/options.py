from pygeai.cli.commands import Option

PROJECT_ID_OPTION = Option(
    "project_id",
    ["--project-id", "--pid"],
    "GUID of the project (optional)",
    True
)