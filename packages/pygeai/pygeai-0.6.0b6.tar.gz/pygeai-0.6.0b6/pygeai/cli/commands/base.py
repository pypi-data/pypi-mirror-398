from pygeai.cli.commands import ArgumentsEnum, Command, Option
from pygeai.cli.commands.admin import admin_commands
from pygeai.cli.commands.assistant import assistant_commands
from pygeai.cli.commands.auth import auth_commands
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.chat import chat_commands
from pygeai.cli.commands.configuration import configure, configuration_options
from pygeai.cli.commands.docs import docs_commands
from pygeai.cli.commands.embeddings import embeddings_commands
from pygeai.cli.commands.evaluation import evaluation_commands
from pygeai.cli.commands.feedback import feedback_commands
from pygeai.cli.commands.files import files_commands
from pygeai.cli.commands.gam import gam_commands
from pygeai.cli.commands.lab.spec import spec_commands
from pygeai.cli.commands.llm import llm_commands
from pygeai.cli.commands.migrate import migrate_commands
from pygeai.cli.commands.organization import organization_commands
from pygeai.cli.commands.rag import rag_commands
from pygeai.cli.commands.rerank import rerank_commands
from pygeai.cli.commands.lab.ai_lab import ai_lab_commands
from pygeai.cli.commands.secrets import secrets_commands
from pygeai.cli.commands.usage_limits import usage_limit_commands
from pygeai.cli.commands.version import check_new_version
from pygeai.cli.texts.help import HELP_TEXT
from pygeai import __version__ as cli_version
from pygeai.core.utils.console import Console
from pygeai.health.clients import HealthClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(base_commands, HELP_TEXT)
    Console.write_stdout(help_text)


def show_version():
    """
    Displays version in stdout
    """
    Console.write_stdout(
        f" - Globant Enterprise AI: GEAI cli utility. Version: {cli_version}"
    )


def check_for_updates():
    """
    Checks if there are updates available
    """
    package_name = 'pygeai'
    version_status = check_new_version(package_name)
    Console.write_stdout(f"{version_status}")


def check_api_status():
    """
    Checks API status
    """
    api_status = HealthClient().check_api_status()
    Console.write_stdout(f"API Status: {api_status}")


"""
Commands that have available subcommands should have action None, so the parser knows that it shouldn't
run any action but instead send it to process again to identify subcommand.
"""

base_commands = [
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
        "version",
        ["version", "v"],
        "Display version text",
        show_version,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "check_updates",
        ["check-updates", "cu"],
        "Search for available updates",
        check_for_updates,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "check_status",
        ["status", "s"],
        "Check API status for Globant Enterprise AI instance",
        check_api_status,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "configure",
        ["configure", "config", "c"],
        "Setup the environment variables required to interact with GEAI",
        configure,
        ArgumentsEnum.OPTIONAL,
        [],
        configuration_options
    ),
    Command(
        "organization",
        ["organization", "org"],
        "Invoke organization endpoints to handle project parameters",
        None,
        ArgumentsEnum.REQUIRED,
        organization_commands,
        [],
    ),
    Command(
        "assistant",
        ["assistant", "ast"],
        "Invoke assistant endpoints to handle assistant parameters",
        None,
        ArgumentsEnum.REQUIRED,
        assistant_commands,
        [],
    ),
    Command(
        "rag_assistant",
        ["rag"],
        "Invoke rag assistant endpoints to handle RAG assistant parameters",
        None,
        ArgumentsEnum.REQUIRED,
        rag_commands,
        [],
    ),
    Command(
        "chat",
        ["chat"],
        "Invoke chat endpoints to handle chat with assistants parameters",
        None,
        ArgumentsEnum.REQUIRED,
        chat_commands,
        [],
    ),
    Command(
        "admin",
        ["admin", "adm"],
        "Invoke admin endpoints designed for internal use",
        None,
        ArgumentsEnum.REQUIRED,
        admin_commands,
        []
    ),
    Command(
        "auth",
        ["auth"],
        "Invoke auth endpoints for token generation",
        None,
        ArgumentsEnum.REQUIRED,
        auth_commands,
        []
    ),

    Command(
        "llm",
        ["llm"],
        "Invoke llm endpoints for provider's and model retrieval",
        None,
        ArgumentsEnum.REQUIRED,
        llm_commands,
        []
    ),
    Command(
        "files",
        ["files"],
        "Invoke files endpoints for file handling",
        None,
        ArgumentsEnum.REQUIRED,
        files_commands,
        []
    ),
    Command(
        "usage_limit",
        ["usage-limit", "ulim"],
        "Invoke usage limit endpoints for organization and project",
        None,
        ArgumentsEnum.REQUIRED,
        usage_limit_commands,
        []
    ),
    Command(
        "embeddings",
        ["embeddings", "emb"],
        "Invoke embeddings endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        embeddings_commands,
        []
    ),
    Command(
        "feedback",
        ["feedback", "fbk"],
        "Invoke feedback endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        feedback_commands,
        []
    ),
    Command(
        "rerank",
        ["rerank", "rr"],
        "Invoke rerank endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        rerank_commands,
        []
    ),
    Command(
        "evaluation",
        ["evaluation", "eval"],
        "Invoke evaluation endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        evaluation_commands,
        []
    ),
    Command(
        "gam",
        ["gam"],
        "Invoke GAM authentication endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        gam_commands,
        []
    ),
    Command(
        "secrets",
        ["secrets", "sec"],
        "Handle Globant Enterprise AI secrets",
        None,
        ArgumentsEnum.REQUIRED,
        secrets_commands,
        []
    ),
    Command(
        "ai_lab",
        ["ai-lab", "ail"],
        "Invoke AI Lab endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        ai_lab_commands,
        []
    ),
    Command(
        "ai_lab_spec",
        ["ai-lab-spec", "spec"],
        "Invoke AI Lab endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        spec_commands,
        []
    ),
    Command(
        "migrate",
        ["migrate", "mig"],
        "Invoke migrate procedures",
        None,
        ArgumentsEnum.REQUIRED,
        migrate_commands,
        []
    ),
    #Command(
    #    "docs",
    #    ["docs"],
    #    "View PyGEAI SDK documentation",
    #    None,
    #    ArgumentsEnum.NOT_AVAILABLE,
    #    docs_commands,
    #    []
    #),

]


base_options = (
    Option(
        "output",
        ["--output", "-o"],
        "Set output file to save the command result",
        True
    ),
)
