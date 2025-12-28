from pygeai import logger
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import SPEC_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException

from pygeai.core.utils.console import Console
from pygeai.lab.managers import AILabManager
from pygeai.lab.spec.loader import JSONLoader
from pygeai.lab.spec.parsers import AgentParser, ToolParser, TaskParser, AgenticProcessParser


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(spec_commands, SPEC_HELP_TEXT)
    Console.write_stdout(help_text)


def load_agent(option_list: list):
    file = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "file":
            file = option_arg
        if option_flag.name == "automatic_publish":
            automatic_publish = option_arg

    if not file:
        raise MissingRequirementException("Cannot load agent definition without specifying path to JSON file.")

    agent_data = JSONLoader.load_data(file_path=file)
    if isinstance(agent_data, dict):
        agent = AgentParser.get_agent(agent_data)
        create_agent(agent, automatic_publish)
    elif isinstance(agent_data, list):
        for agent_spec in agent_data:
            agent = AgentParser.get_agent(agent_spec)
            create_agent(agent, automatic_publish)


def create_agent(agent, automatic_publish):
    try:
        created_agent = AILabManager().create_agent(
            agent=agent,
            automatic_publish=automatic_publish
        )

        Console.write_stdout(f"Created agent detail: \n{created_agent}")
    except Exception as e:
        logger.error(f"Error creating agent: {e}\nAgent data: {agent}")
        Console.write_stderr(f"Error creating agent: \n{agent}")


load_agent_options = [
    Option(
        "file",
        ["--file", "-f"],
        "Path to the file containing agent definition in JSON format.",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if reasoning strategy must be published besides being created. 0: Create as draft. 1: Create and publish.",
        True
    ),
]


def load_tool(option_list: list):
    file = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "file":
            file = option_arg
        if option_flag.name == "automatic_publish":
            automatic_publish = option_arg

    if not file:
        raise MissingRequirementException("Cannot load tool definition without specifying path to JSON file.")

    tool_data = JSONLoader.load_data(file_path=file)
    if isinstance(tool_data, dict):
        tool = ToolParser.get_tool(tool_data)
        create_tool(tool, automatic_publish)
    elif isinstance(tool_data, list):
        for tool_spec in tool_data:
            tool = ToolParser.get_tool(tool_spec)
            create_tool(tool, automatic_publish)


def create_tool(tool, automatic_publish):
    try:
        created_tool = AILabManager().create_tool(
            tool=tool,
            automatic_publish=automatic_publish
        )
        Console.write_stdout(f"Created tool detail: \n{created_tool}")
    except Exception as e:
        logger.error(f"Error creating tool: {e}\nTool data: {tool}")
        Console.write_stderr(f"Error creating tool: \n{tool}")


load_tool_options = [
    Option(
        "file",
        ["--file", "-f"],
        "Path to the file containing tool definition in JSON format.",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if tool must be published besides being created. 0: Create as draft. 1: Create and publish.",
        True
    ),
]


def load_task(option_list: list):
    file = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "file":
            file = option_arg
        if option_flag.name == "automatic_publish":
            automatic_publish = option_arg

    if not file:
        raise MissingRequirementException("Cannot load task definition without specifying path to JSON file.")

    task_data = JSONLoader.load_data(file_path=file)
    if isinstance(task_data, dict):
        task = TaskParser.get_task(task_data)
        create_task(task, automatic_publish)
    elif isinstance(task_data, list):
        for task_spec in task_data:
            task = TaskParser.get_task(task_spec)
            create_task(task, automatic_publish)


def create_task(task, automatic_publish):
    try:
        created_task = AILabManager().create_task(
            task=task,
            automatic_publish=automatic_publish
        )
        Console.write_stdout(f"Created task detail: \n{created_task}")
    except Exception as e:
        logger.error(f"Error creating task: {e}\nTask data: {task}")
        Console.write_stderr(f"Error creating task: \n{task}")


load_task_options = [
    Option(
        "file",
        ["--file", "-f"],
        "Path to the file containing task definition in JSON format.",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if task must be published besides being created. 0: Create as draft. 1: Create and publish.",
        True
    ),
]


def load_agentic_process(option_list: list):
    file = None
    automatic_publish = False

    for option_flag, option_arg in option_list:
        if option_flag.name == "file":
            file = option_arg
        if option_flag.name == "automatic_publish":
            automatic_publish = option_arg


    if not file:
        raise MissingRequirementException("Cannot load agentic process definition without specifying path to JSON file.")

    process_data = JSONLoader.load_data(file_path=file)
    if isinstance(process_data, dict):
        process = AgenticProcessParser.get_agentic_process(process_data)
        create_agentic_process(process, automatic_publish)
    elif isinstance(process_data, list):
        for process_spec in process_data:
            process = AgenticProcessParser.get_agentic_process(process_spec)
            create_agentic_process(process, automatic_publish)


def create_agentic_process(process, automatic_publish):
    try:
        created_process = AILabManager().create_process(
            process=process,
            automatic_publish=automatic_publish
        )
        Console.write_stdout(f"Created agentic process detail: \n{created_process}")
    except Exception as e:
        logger.error(f"Error creating agentic process: {e}\nProcess data: {process}")
        Console.write_stderr(f"Error creating agentic process: \n{process}")


load_agentic_process_options = [
    Option(
        "file",
        ["--file", "-f"],
        "Path to the file containing agentic process definition in JSON format.",
        True
    ),
    Option(
        "automatic_publish",
        ["--automatic-publish", "--ap"],
        "Define if agentic process must be published besides being created. 0: Create as draft. 1: Create and publish.",
        True
    ),
]


spec_commands = [
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
        "load_agent",
        ["load-agent", "la"],
        "Load agent from JSON specification",
        load_agent,
        ArgumentsEnum.REQUIRED,
        [],
        load_agent_options
    ),
    Command(
        "load_tool",
        ["load-tool", "lt"],
        "Load tool from JSON specification",
        load_tool,
        ArgumentsEnum.REQUIRED,
        [],
        load_tool_options
    ),
    Command(
        "load_task",
        ["load-task"],
        "Load task from JSON specification",
        load_task,
        ArgumentsEnum.REQUIRED,
        [],
        load_task_options
    ),
    Command(
        "load_agentic_process",
        ["load-agentic-process", "lap"],
        "Load agentic process from JSON specification",
        load_agentic_process,
        ArgumentsEnum.REQUIRED,
        [],
        load_agentic_process_options
    ),
]
