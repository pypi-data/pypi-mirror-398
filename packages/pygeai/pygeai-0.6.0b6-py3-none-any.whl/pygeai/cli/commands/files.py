from pygeai.cli.commands import Command, ArgumentsEnum, Option
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import FILES_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.files.clients import FileClient
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(files_commands, FILES_HELP_TEXT)
    Console.write_stdout(help_text)


def upload_file(option_list: list):
    organization = None
    project = None
    file_name = None
    file_path = None
    folder = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "file_name":
            file_name = option_arg
        if option_flag.name == "file_path":
            file_path = option_arg
        if option_flag.name == "folder":
            folder = option_arg

    if not (organization and project and file_path):
        raise MissingRequirementException("Organization ID, Project ID and File path are mandatory parameters in order "
                                          "to upload a file.")

    client = FileClient()
    result = client.upload_file(
        organization_id=organization,
        project_id=project,
        file_path=file_path,
        file_name=file_name,
        folder=folder
    )
    Console.write_stdout(f"Uploaded file: \n{result}")


upload_file_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "Organization ID (required)",
        True
    ),
    Option(
        "project",
        ["--project", "--proj", "-p"],
        "Project ID (required)",
        True
    ),
    Option(
        "file_name",
        ["--file-name", "--fn"],
        "File name (optional). If not provided, the name of the uploaded file will be used.",
        True
    ),
    Option(
        "file_path",
        ["--file-path", "--fp"],
        "File path to the file you want to upload (required)",
        True
    ),
    Option(
        "folder",
        ["--folder", "-f"],
        "Destination folder (optional). If not provided, the file will be temporarily saved.",
        True
    ),
]


def get_file(option_list: list):
    organization = None
    project = None
    file_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "file_id":
            file_id = option_arg

    if not (organization and project and file_id):
        raise MissingRequirementException("Cannot get file without organization, project and file_id.")

    client = FileClient()
    result = client.get_file(
        organization=organization,
        project=project,
        file_id=file_id,
    )
    Console.write_stdout(f"File: \n{result}")


get_file_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "Organization ID (required)",
        True
    ),
    Option(
        "project",
        ["--project", "--proj", "-p"],
        "Project ID (required)",
        True
    ),
    Option(
        "file_id",
        ["--file-id", "--fid"],
        "File ID (required)",
        True
    ),
]


def delete_file(option_list: list):
    organization = None
    project = None
    file_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "file_id":
            file_id = option_arg

    if not (organization and project and file_id):
        raise MissingRequirementException("Cannot delete file without organization, project and file_id.")

    client = FileClient()
    result = client.delete_file(
        file_id=file_id,
        organization=organization,
        project=project
    )
    Console.write_stdout(f"Deleted file: \n{result}")


delete_file_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "Organization ID (required)",
        True
    ),
    Option(
        "project",
        ["--project", "--proj", "-p"],
        "Project ID (required)",
        True
    ),
    Option(
        "file_id",
        ["--file-id", "--fid"],
        "File ID (required)",
        True
    ),
]


def get_file_content(option_list: list):
    organization = None
    project = None
    file_id = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg
        if option_flag.name == "file_id":
            file_id = option_arg

    if not (organization and project and file_id):
        raise MissingRequirementException("Cannot get file content without organization, project and file_id.")

    client = FileClient()
    result = client.get_file_content(
        file_id=file_id,
        organization=organization,
        project=project
    )
    Console.write_stdout(f"File content: \n{result}")


get_file_content_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "Organization ID (required)",
        True
    ),
    Option(
        "project",
        ["--project", "--proj", "-p"],
        "Project ID (required)",
        True
    ),
    Option(
        "file_id",
        ["--file-id", "--fid"],
        "File ID (required)",
        True
    ),
]


def get_file_list(option_list: list):
    organization = None
    project = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "organization":
            organization = option_arg
        if option_flag.name == "project":
            project = option_arg

    if not (organization and project):
        raise MissingRequirementException("Cannot file list without organization and project id.")

    client = FileClient()
    result = client.get_file_list(
        organization=organization,
        project=project
    )
    Console.write_stdout(f"Files list: \n{result}")


get_file_list_options = [
    Option(
        "organization",
        ["--organization", "--org", "-o"],
        "Organization ID (required)",
        True
    ),
    Option(
        "project",
        ["--project", "--proj", "-p"],
        "Project ID (required)",
        True
    ),
]

files_commands = [
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
        "upload_file",
        ["upload-file", "uf"],
        "Upload file",
        upload_file,
        ArgumentsEnum.REQUIRED,
        [],
        upload_file_options
    ),
    Command(
        "get_file",
        ["get-file", "gf"],
        "Get file data",
        get_file,
        ArgumentsEnum.REQUIRED,
        [],
        get_file_options
    ),
    Command(
        "delete_file",
        ["delete-file", "df"],
        "Delete file data",
        delete_file,
        ArgumentsEnum.REQUIRED,
        [],
        delete_file_options
    ),
    Command(
        "get_file_content",
        ["get-file-content", "gfc"],
        "Get file content",
        get_file_content,
        ArgumentsEnum.REQUIRED,
        [],
        get_file_content_options
    ),
    Command(
        "list_files",
        ["list-files", "lf"],
        "Retrieve file list",
        get_file_list,
        ArgumentsEnum.REQUIRED,
        [],
        get_file_list_options
    )
]
