import json
import platform
import os
import subprocess
import sys
from importlib import resources
from pathlib import Path

from pygeai import logger
from pygeai.chat.clients import ChatClient
from pygeai.chat.iris import Iris
from pygeai.chat.session import AgentChatSession
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.common import get_messages, get_boolean_value, get_penalty_float_value
from pygeai.cli.commands.lab.utils import get_project_id
from pygeai.cli.texts.help import CHAT_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError, InvalidAgentException
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from pygeai.core.utils.console import Console
from pygeai.lab.agents.clients import AgentClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(chat_commands, CHAT_HELP_TEXT)
    Console.write_stdout(help_text)


def get_chat_completion(option_list: list):
    model = None
    message_list = []
    stream = False
    temperature = None
    max_tokens = None
    thread_id = None
    frequency_penalty = None
    presence_penalty = None
    top_p = None
    stop = None
    response_format = None
    tools = None
    tool_choice = None
    logprobs = None
    top_logprobs = None
    seed = None
    stream_options = None
    store = None
    metadata = None
    user = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "model":
            model = option_arg
        if option_flag.name == "messages":
            try:
                message_json = json.loads(option_arg)
                if isinstance(message_json, list):
                    message_list = message_json
                elif isinstance(message_json, dict):
                    message_list.append(message_json)
            except Exception as e:
                raise WrongArgumentError(
                    "Each message must be in json format: '{\"role\": \"user\", \"content\": \"message content\"}' "
                    "It can be a dictionary or a list of dictionaries. Each dictionary must contain role and content")
        if option_flag.name == "stream":
            if option_arg:
                stream = get_boolean_value(option_arg)
        if option_flag.name == "temperature":
            temperature = float(option_arg) if option_arg is not None else None
        if option_flag.name == "max_tokens":
            max_tokens = int(option_arg) if option_arg is not None else None
        if option_flag.name == "thread_id":
            thread_id = option_arg
        if option_flag.name == "frequency_penalty":
            if option_arg:
                frequency_penalty = get_penalty_float_value(option_arg)
        if option_flag.name == "presence_penalty":
            if option_arg:
                presence_penalty = get_penalty_float_value(option_arg)
        if option_flag.name == "top_p":
            top_p = float(option_arg) if option_arg else None
        if option_flag.name == "stop":
            try:
                stop = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                stop = option_arg
        if option_flag.name == "response_format":
            try:
                response_format = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                raise WrongArgumentError("response_format must be a valid JSON object")
        if option_flag.name == "tools":
            try:
                tools = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                raise WrongArgumentError("tools must be a valid JSON array")
        if option_flag.name == "tool_choice":
            try:
                tool_choice = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                tool_choice = option_arg
        if option_flag.name == "logprobs":
            logprobs = get_boolean_value(option_arg) if option_arg else None
        if option_flag.name == "top_logprobs":
            top_logprobs = int(option_arg) if option_arg else None
        if option_flag.name == "seed":
            seed = int(option_arg) if option_arg else None
        if option_flag.name == "stream_options":
            try:
                stream_options = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                raise WrongArgumentError("stream_options must be a valid JSON object")
        if option_flag.name == "store":
            store = get_boolean_value(option_arg) if option_arg else None
        if option_flag.name == "metadata":
            try:
                metadata = json.loads(option_arg) if option_arg else None
            except json.JSONDecodeError:
                raise WrongArgumentError("metadata must be a valid JSON object")
        if option_flag.name == "user":
            user = option_arg

    messages = get_messages(message_list)

    if not (model and messages):
        raise MissingRequirementException("Cannot perform chat completion without specifying model and messages")

    client = ChatClient()
    result = client.chat_completion(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        thread_id=thread_id,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        top_p=top_p,
        stop=stop,
        response_format=response_format,
        tools=tools,
        tool_choice=tool_choice,
        logprobs=logprobs,
        top_logprobs=top_logprobs,
        seed=seed,
        stream_options=stream_options,
        store=store,
        metadata=metadata,
        user=user
    )
    if stream:
        Console.write_stdout("Streaming chat completion:")
        for chunk in result:
            Console.write_stdout(f"{chunk}", end="")
            sys.stdout.flush()
        Console.write_stdout()
    else:
        Console.write_stdout(f"Chat completion detail: \n{result}\n")


chat_completion_options = [
    Option(
        "model",
        ["--model", "-m"],
        "The model needs to address the assistant type and name or bot_id, depending on the Type. Then, the parameters"
        " will vary depending on the type. Its format is as follows: \n"
        "\t\"model\": \"saia:<assistant_type>:<assistant_name>|<bot_id>\"",
        True
    ),
    Option(
        "messages",
        ["--messages", "--msg"],
        "The messages element defines the desired messages to be added. The minimal value needs to be the following, "
        "where the content details the user input.\n"
        "\t{ \n"
        "\t\t\"role\": \"string\", /* user, system and may support others depending on the selected model */ \n"
        "\t\t\"content\": \"string\" \n"
        "\t}\n",
        True
    ),
    Option(
        "stream",
        ["--stream"],
        "If response should be streamed. Possible values: 0: OFF; 1: ON",
        True
    ),
    Option(
        "temperature",
        ["--temperature", "--temp"],
        "Float value to set volatility of the assistant's answers (between 0 and 2)",
        True
    ),
    Option(
        "max_tokens",
        ["--max-tokens"],
        "Integer value to set max tokens to use",
        True
    ),
    Option(
        "thread_id",
        ["--thread-id"],
        "Optional UUID for conversation identifier",
        True
    ),
    Option(
        "frequency_penalty",
        ["--frequency-penalty"],
        "Optional number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency "
        "in the text so far, decreasing the model's likelihood to repeat the same line verbatim.",
        True
    ),
    Option(
        "presence_penalty",
        ["--presence-penalty"],
        "Optional number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in "
        "the text so far, increasing the model's likelihood to talk about new topics.",
        True
    ),
    Option(
        "top_p",
        ["--top-p"],
        "Optional float value for nucleus sampling, where the model considers tokens with top_p probability mass "
        "(between 0 and 1). An alternative to temperature.",
        True
    ),
    Option(
        "stop",
        ["--stop"],
        "Optional string or JSON array of up to 4 sequences where the API will stop generating further tokens.",
        True
    ),
    Option(
        "response_format",
        ["--response-format"],
        "Optional JSON object specifying the output format, e.g., {\"type\": \"json_schema\", \"json_schema\": {...}} "
        "for structured outputs.",
        True
    ),
    Option(
        "tools",
        ["--tools"],
        "Optional JSON array of tools (e.g., functions) the model may call.",
        True
    ),
    Option(
        "tool_choice",
        ["--tool-choice"],
        "Optional string (e.g., \"none\", \"auto\") or JSON object to control which tool is called.",
        True
    ),
    Option(
        "logprobs",
        ["--logprobs"],
        "Optional boolean to return log probabilities of output tokens. Possible values: 0: OFF; 1: ON",
        True
    ),
    Option(
        "top_logprobs",
        ["--top-logprobs"],
        "Optional integer (0-20) specifying the number of most likely tokens to return with log probabilities.",
        True
    ),
    Option(
        "seed",
        ["--seed"],
        "Optional integer for deterministic sampling (in Beta).",
        True
    ),
    Option(
        "stream_options",
        ["--stream-options"],
        "Optional JSON object for streaming options, e.g., {\"include_usage\": true}.",
        True
    ),
    Option(
        "store",
        ["--store"],
        "Optional boolean to store the output for model distillation or evals. Possible values: 0: OFF; 1: ON",
        True
    ),
    Option(
        "metadata",
        ["--metadata"],
        "Optional JSON object with up to 16 key-value pairs to attach to the object.",
        True
    ),
    Option(
        "user",
        ["--user"],
        "Optional string identifier for the end-user to monitor abuse.",
        True
    ),
]


def chat_with_iris():
    iris = Iris()
    messages = list()

    history = InMemoryHistory()
    session = PromptSession(">> Ask Iris: ", history=history)

    Console.write_stdout(f"#=================================================#")
    Console.write_stdout(f"#--------------------- IRIS ----------------------#")
    Console.write_stdout(f"#=================================================#")
    Console.write_stdout(f"# This is the start of your conversation with Iris. Type 'exit' or press Ctrl+C to close the chat.\n")
    Console.write_stdout("""- Iris: Hello! I'm Iris. I'll guide you step by step to create your agent.
First, we need to define some key details for your agent. You can specify its role and purpose or give it a name, and I'll help you set up the rest. Once we have that, we'll refine its knowledge and behavior.""")
    try:
        while (user_input := session.prompt()) != "exit":
            Console.write_stdout(f"- User: {user_input}")
            new_message = {
                "role": "user",
                "content": user_input
            }
            messages.append(new_message)

            result = iris.stream_answer(messages)
            answer = ""
            Console.write_stdout("- Iris: ")
            for chunk in result:
                answer += chunk
                Console.write_stdout(f"{chunk}", end="")
                sys.stdout.flush()
            Console.write_stdout()

            new_answer = {
                "role": "assistant",
                "content": answer
            }
            messages.append(new_answer)
    except KeyboardInterrupt:
        print("\nExiting chat...")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Error chatting with Iris: {e}")
        Console.write_stderr("An unexpected error has occurred. Please contact the developers.")


def chat_with_agent(option_list: list):
    agent_name = None
    use_gui = False
    save_session_file = None
    restore_session_file = None
    for option_flag, option_arg in option_list:
        if option_flag.name == "agent_name":
            agent_name = option_arg
        if option_flag.name == "gui":
            use_gui = True
        if option_flag.name == "save_session":
            save_session_file = option_arg
        if option_flag.name == "restore_session":
            restore_session_file = option_arg

    if not agent_name:
        raise MissingRequirementException(f"Agent name must be specified.")

    project_id = get_project_id()
    agent_data = AgentClient(project_id=project_id).get_agent(agent_id=agent_name)
    if 'errors' in agent_data:
        raise InvalidAgentException(f"There is no agent with that name: {agent_data.get('errors')}")

    if use_gui:
        try:
            import streamlit
        except ImportError:
            logger.error("Streamlit not installed")
            Console.write_stderr("Streamlit is required for GUI mode. Install it with 'pip install streamlit'.")
            sys.exit(1)

        try:
            ui_path = resources.files("pygeai.chat").joinpath("ui.py")
            ui_file_path = str(ui_path)

            # Add the top-level project root to PYTHONPATH
            package_root = str(Path(ui_file_path).resolve().parents[2])
            env = os.environ.copy()
            env["PYTHONPATH"] = package_root + os.pathsep + env.get("PYTHONPATH", "")

            streamlit_cmd = [
                sys.executable, "-m", "streamlit", "run", ui_file_path,
                "--server.address", "127.0.0.1",
                "--", "--agent-name", agent_name
            ]

            if platform.system() == "Linux":
                streamlit_cmd.insert(5, "--server.headless=true")

            process = subprocess.Popen(
                streamlit_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            url = "http://localhost:8501"
            if platform.system() == "Linux":
                Console.write_stdout(f"Open Streamlit app at {url} (or next port like 8502 if 8501 is taken)")

            try:
                stdout, stderr = process.communicate()
                if stderr:
                    logger.error(f"Streamlit stderr:\n{stderr}")
                    Console.write_stderr(f"Streamlit error:\n{stderr}")
            except KeyboardInterrupt:
                process.terminate()
                Console.write_stdout("Streamlit stopped.")
                sys.exit(0)

        except FileNotFoundError:
            logger.error("Could not locate pygeai/chat/ui.py")
            Console.write_stderr("Streamlit UI file not found. Ensure pygeai is installed correctly.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Streamlit error: {e}")
            Console.write_stderr(
                f"Failed to launch Streamlit. Check port with 'lsof -i :8501' and kill any process, or try {url}.")
            sys.exit(1)
    else:
        chat_session = AgentChatSession(agent_name)
        messages = list()

        # Restore session if specified
        if restore_session_file:
            try:
                with open(restore_session_file, 'r') as f:
                    restored_data = json.load(f)
                    if isinstance(restored_data, list):
                        messages = restored_data
                        Console.write_stdout(f"Restored conversation from {restore_session_file}")
                        # Display restored conversation history
                        Console.write_stdout(f"#=================================================#")
                        Console.write_stdout(f"#    CHAT SESSION WITH {agent_name}               ")
                        Console.write_stdout(f"#=================================================#")
                        for msg in messages:
                            role = msg.get("role", "unknown")
                            content = msg.get("content", "")
                            if role == "assistant":
                                Console.write_stdout(f"- Agent: {content}")
                            elif role == "user":
                                Console.write_stdout(f"- User: {content}")
                    else:
                        raise WrongArgumentError("Session file must contain a list of messages in JSON format.")
            except FileNotFoundError:
                logger.error(f"Session file {restore_session_file} not found.")
                Console.write_stderr(f"Session file {restore_session_file} not found. Starting a new conversation.")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON format in {restore_session_file}.")
                Console.write_stderr(f"Invalid JSON format in {restore_session_file}. Starting a new conversation.")
            except Exception as e:
                logger.error(f"Error restoring session: {e}")
                Console.write_stderr(f"Error restoring session from {restore_session_file}. Starting a new conversation.")

        # If no session was restored or messages are empty, get the agent's introduction
        if not messages:
            introduction_message = chat_session.get_answer(
                ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                 "stating who you are and what you do. Nothing else."]
            )

            if "Agent not found" in str(introduction_message):
                raise WrongArgumentError(
                    "The specified agent doesn't seem to exist. Please review the name and try again.")

            Console.write_stdout(f"#=================================================#")
            Console.write_stdout(f"#    CHAT SESSION WITH {agent_name}               ")
            Console.write_stdout(f"#=================================================#")
            Console.write_stdout(introduction_message)
            messages.append({"role": "assistant", "content": introduction_message})

        history = InMemoryHistory()
        session = PromptSession(f">> Ask {agent_name}: ", history=history)

        # Save session function
        def save_session(messages, file_path):
            try:
                with open(file_path, 'w') as f:
                    json.dump(messages, f, indent=2)
                logger.info(f"Session saved to {file_path}")
            except Exception as e:
                logger.error(f"Error saving session to {file_path}: {e}")
                Console.write_stderr(f"Failed to save session to {file_path}: {e}")

        try:
            while (user_input := session.prompt()) != "exit":
                Console.write_stdout(f"- User: {user_input}")
                new_message = {
                    "role": "user",
                    "content": user_input
                }
                messages.append(new_message)

                # Save session after user input if specified
                if save_session_file:
                    save_session(messages, save_session_file)

                result = chat_session.stream_answer(messages)
                answer = ""
                Console.write_stdout("- Agent: ")
                for chunk in result:
                    answer += chunk
                    Console.write_stdout(f"{chunk}", end="")
                    sys.stdout.flush()
                Console.write_stdout()

                new_answer = {
                    "role": "assistant",
                    "content": answer
                }
                messages.append(new_answer)

                # Save session after agent response if specified
                if save_session_file:
                    save_session(messages, save_session_file)

        except KeyboardInterrupt:
            print("\nExiting chat...")
            # Final save before exit if specified
            if save_session_file:
                save_session(messages, save_session_file)
            sys.exit(0)
        except WrongArgumentError as e:
            Console.write_stderr(f"There was an error: {e}")
        except Exception as e:
            logger.error(f"Error chatting with Agent: {e}")
            Console.write_stderr("An unexpected error has occurred. Please contact the developers.")
            # Save session on error if specified
            if save_session_file:
                save_session(messages, save_session_file)


chat_with_agent_options = [
    Option(
        "agent_name",
        ["--agent-name", "--name", "-n"],
        "You can use the internal name, public name and agent id in order to chat interactively with any agent",
        True
    ),
    Option(
        "gui",
        ["--gui", "-g"],
        "Launch a Streamlit GUI chat interface. No need to specify argument next to the option",
        False
    ),
    Option(
        "save_session",
        ["--save-session", "--ss"],
        "Save the conversation to a JSON file. Provide the file path as the argument.",
        True
    ),
    Option(
        "restore_session",
        ["--restore-session", "--rs"],
        "Restore a conversation from a JSON file. Provide the file path as the argument.",
        True
    ),
]


def get_generate_image(option_list: list):
    model = None
    prompt = None
    n = None
    quality = None
    size = None
    aspect_ratio = None

    for option_flag, option_arg in option_list:
        if option_flag.name == "model":
            model = option_arg
        if option_flag.name == "prompt":
            prompt = option_arg
        if option_flag.name == "n":
            try:
                n = int(option_arg)
                if n < 1 or n > 10:
                    raise WrongArgumentError("n must be an integer between 1 and 10.")
            except ValueError:
                raise WrongArgumentError("n must be a valid integer.")
        if option_flag.name == "quality":
            quality = option_arg
        if option_flag.name == "size":
            size = option_arg
        if option_flag.name == "aspect_ratio":
            aspect_ratio = option_arg

    if not (model and prompt and n is not None and quality and size):
        raise MissingRequirementException("Cannot generate image without specifying model, prompt, n, quality, and size.")

    client = ChatClient()
    try:
        result = client.generate_image(
            model=model,
            prompt=prompt,
            n=n,
            quality=quality,
            size=size,
            aspect_ratio=aspect_ratio
        )
        Console.write_stdout(f"Image generation result: \n{result}\n")
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        Console.write_stderr(f"Failed to generate image: {e}")


generate_image_options = [
    Option(
        "model",
        ["--model", "-m"],
        "The model specification for image generation, e.g., 'openai/gpt-image-1'.",
        True
    ),
    Option(
        "prompt",
        ["--prompt", "-p"],
        "Description of the desired image.",
        True
    ),
    Option(
        "n",
        ["--n"],
        "Number of images to generate (1-10, depending on the model).",
        True
    ),
    Option(
        "quality",
        ["--quality", "-q"],
        "Rendering quality, e.g., 'high'.",
        True
    ),
    Option(
        "size",
        ["--size", "-s"],
        "Image dimensions, e.g., '1024x1024'.",
        True
    ),
    Option(
        "aspect_ratio",
        ["--aspect-ratio", "-ar"],
        "Relationship between image’s width and height, e.g., '1:1', '9:16', '16:9', '3:4', '4:3'.",
        True
    ),
]


chat_commands = [
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
        "completion",
        ["completion", "comp"],
        "Get chat completion",
        get_chat_completion,
        ArgumentsEnum.REQUIRED,
        [],
        chat_completion_options
    ),
    Command(
        "iris",
        ["iris"],
        "Interactive chat with Iris",
        chat_with_iris,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "agent",
        ["agent"],
        "Interactive chat with Agent",
        chat_with_agent,
        ArgumentsEnum.REQUIRED,
        [],
        chat_with_agent_options
    ),
    Command(
        "generate_image",
        ["generate-image", "gen-img"],
        "Generate an image using the specified model and parameters",
        get_generate_image,
        ArgumentsEnum.REQUIRED,
        [],
        generate_image_options
    ),

]
