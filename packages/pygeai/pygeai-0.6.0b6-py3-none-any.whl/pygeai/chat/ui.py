import logging

import streamlit as st
import argparse
import json
import os
from datetime import datetime
from pygeai.chat.session import AgentChatSession
from pygeai.core.utils.console import Console
from pygeai.core.common.config import get_settings
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, AgentList
import sys

logger = logging.getLogger(__name__)


global SESSION_FILE_PATH


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Streamlit chat interface for pygeai agent")
    parser.add_argument("--agent-name", "-n", required=True, help="Name of the agent to interact with")
    args, unknown = parser.parse_known_args()  # Ignore Streamlit's args
    return args


def save_session_to_file(messages, file_path):
    """Helper function to save session to a server-side file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(messages, f, indent=2)
        logger.info(f"Session automatically saved to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving session to {file_path}: {e}")
        st.error(f"Failed to auto-save session: {e}")
        return False


def get_unique_file_path(base_path):
    """Generate a unique file path by appending a numeric suffix if the file exists."""
    if not os.path.exists(base_path):
        return base_path

    directory, filename = os.path.split(base_path)
    name, ext = os.path.splitext(filename)
    counter = 1

    new_path = base_path
    while os.path.exists(new_path):
        new_filename = f"{name}_{counter}{ext}"
        new_path = os.path.join(directory, new_filename)
        counter += 1

    return new_path


def get_session_file_path(agent_name, custom_filename=None):
    """Generate the session file path with date and agent name, or use a custom filename."""
    if custom_filename:
        if not custom_filename.endswith('.json'):
            custom_filename += '.json'
        return os.path.join("chats", custom_filename)
    current_date = datetime.now().strftime("%Y-%m-%d")
    return os.path.join("chats", f"chat_session_{agent_name}_{current_date}.json")


def list_session_files():
    """List all JSON files in the 'chats' directory."""
    chats_dir = "chats"
    if not os.path.exists(chats_dir):
        return []
    try:
        return [f for f in os.listdir(chats_dir) if f.endswith('.json')]
    except Exception as e:
        logger.error(f"Error listing session files in {chats_dir}: {e}")
        return []


def load_session_from_file(file_path):
    """Load session data from a specified file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data, True
            else:
                return None, False
    except Exception as e:
        logger.error(f"Error loading session from {file_path}: {e}")
        return None, False


def delete_session_file(file_path):
    """Helper function to delete a session file from the file system."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Session file deleted: {file_path}")
            return True, f"Session file {os.path.basename(file_path)} deleted successfully."
        else:
            logger.warning(f"Session file not found: {file_path}")
            return False, f"Session file {os.path.basename(file_path)} not found."
    except Exception as e:
        logger.error(f"Error deleting session file {file_path}: {e}")
        return False, f"Error deleting session file {os.path.basename(file_path)}: {str(e)}"


def get_alias_list():
    """Get list of available aliases from settings."""
    try:
        settings = get_settings()
        aliases = list(settings.list_aliases().keys())
        return ["-"] + aliases  # Add "-" as default no-selection option
    except Exception as e:
        logger.error(f"Error fetching alias list: {e}")
        st.error(f"Failed to fetch alias list: {e}")
        return ["-"]


def get_agent_list(alias, project_id):
    """Get list of agents for a given alias and project ID."""
    try:
        if alias == "-" or not project_id:
            return ["-"]
        ai_lab_manager = AILabManager(alias=alias)
        filter_settings = FilterSettings(
            allow_external=False,
            allow_drafts=True,
            access_scope="private"
        )
        result = ai_lab_manager.get_agent_list(
            project_id=project_id,
            filter_settings=filter_settings
        )
        if isinstance(result, AgentList) and result.agents:
            # Store full agent data for preview
            st.session_state.agent_data = {f"{agent.name} (ID: {agent.id})": agent for agent in result.agents}
            return ["-"] + [f"{agent.name} (ID: {agent.id})" for agent in result.agents]
        else:
            st.error(f"No agents found for project ID {project_id} or errors occurred: {result.errors if hasattr(result, 'errors') else 'Unknown error'}")
            return ["-"]
    except Exception as e:
        logger.error(f"Error fetching agents for project ID {project_id} with alias {alias}: {e}")
        st.error(f"Failed to fetch agents for project: {e}")
        return ["-"]


def save_recent_agents(agent_name):
    """Save a recently used agent to session state or file."""
    if "recent_agents" not in st.session_state:
        st.session_state.recent_agents = []
    if agent_name and agent_name not in st.session_state.recent_agents:
        st.session_state.recent_agents = [agent_name] + st.session_state.recent_agents[:4]  # Keep top 5 recent
        # Optionally save to a file for persistence
        try:
            with open("recent_agents.json", "w") as f:
                json.dump(st.session_state.recent_agents, f)
        except Exception as e:
            logger.error(f"Error saving recent agents: {e}")


def load_recent_agents():
    """Load recent agents from session state or file."""
    if "recent_agents" not in st.session_state:
        try:
            with open("recent_agents.json", "r") as f:
                st.session_state.recent_agents = json.load(f)
        except Exception:
            st.session_state.recent_agents = []
    return st.session_state.recent_agents


def run_streamlit_chat():
    """Run a Streamlit chat interface for the specified agent."""
    args = parse_args()
    initial_agent_name = args.agent_name
    try:
        # Initialize session state for multiple tabs and current agent
        if "sessions" not in st.session_state:
            st.session_state.sessions = {
                initial_agent_name: {
                    "messages": [],
                    "chat_session": AgentChatSession(initial_agent_name),
                    "custom_filename": "",
                    "active": True
                }
            }
        if "active_tab" not in st.session_state:
            st.session_state.active_tab = initial_agent_name
        if "agent_data" not in st.session_state:
            st.session_state.agent_data = {}
        if "search_term" not in st.session_state:
            st.session_state.search_term = ""
        # if "editing_message" not in st.session_state:
        #    st.session_state.editing_message = None
        # if "edit_content" not in st.session_state:
        #    st.session_state.edit_content = ""
        # if "regenerate_response" not in st.session_state:
        #    st.session_state.regenerate_response = False

        # Load recent agents
        load_recent_agents()

        # Load global vars
        global current_session
        global SESSION_FILE_PATH

        # Get current session for active tab
        current_session = st.session_state.sessions[st.session_state.active_tab]
        if "editing_message" not in current_session:
            current_session["editing_message"] = None
        if "edit_content" not in current_session:
            current_session["edit_content"] = ""
        if "regenerate_response" not in current_session:
            current_session["regenerate_response"] = False
        SESSION_FILE_PATH = get_session_file_path(st.session_state.active_tab, current_session.get("custom_filename", ""))

        # Initialize messages for new session if not already set
        if not current_session["messages"]:
            if os.path.exists(SESSION_FILE_PATH):
                try:
                    with open(SESSION_FILE_PATH, 'r') as f:
                        restored_data = json.load(f)
                        if isinstance(restored_data, list):
                            current_session["messages"] = restored_data
                            st.success(f"Session automatically restored from {SESSION_FILE_PATH}")
                        else:
                            logger.warning(f"Invalid session data in {SESSION_FILE_PATH}. Starting fresh.")
                            intro = current_session["chat_session"].get_answer(
                                ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                                 "stating who you are and what you do. Nothing else."]
                            )
                            if "Agent not found" in str(intro):
                                st.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                                logger.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                                return
                            current_session["messages"] = [{"role": "assistant", "content": intro}]
                except Exception as e:
                    logger.error(f"Error auto-restoring session from {SESSION_FILE_PATH}: {e}")
                    intro = current_session["chat_session"].get_answer(
                        ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                         "stating who you are and what you do. Nothing else."]
                    )
                    if "Agent not found" in str(intro):
                        st.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                        logger.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                        return
                    current_session["messages"] = [{"role": "assistant", "content": intro}]
            else:
                intro = current_session["chat_session"].get_answer(
                    ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                     "stating who you are and what you do. Nothing else."]
                )
                if "Agent not found" in str(intro):
                    st.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                    logger.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                    return
                current_session["messages"] = [{"role": "assistant", "content": intro}]
                save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                st.rerun()

        # Set page title
        st.title(f"Chat with {st.session_state.active_tab}")

        # Display the session save path in the main area for better readability
        st.info(f"Session will be saved as: {SESSION_FILE_PATH}", icon="ℹ️")

        # Chat History Search
        search_term = st.text_input("Search Chat History", value=st.session_state.search_term, placeholder="Enter keyword to filter messages")
        if search_term != st.session_state.search_term:
            st.session_state.search_term = search_term
            st.rerun()

        # Single Session Chat
        current_session = st.session_state.sessions[st.session_state.active_tab]
        if "editing_message" not in current_session:
            current_session["editing_message"] = None
        if "edit_content" not in current_session:
            current_session["edit_content"] = ""
        render_chat_history(
            current_session["messages"],
            search_term,
            tab_key_prefix=st.session_state.active_tab,
            session=current_session
        )

        # Sidebar for session management and agent selection
        with st.sidebar:
            st.header("Session Management")

            with st.expander("Help: Session Saving & Restoring", expanded=False):
                st.markdown("""
                **Session Saving & Restoring Explained:**
                - **Auto-Save Session**: When toggled on, your chat history is automatically saved to a server-side file in the 'chats' directory after each message or action.
                - **Custom Session Filename**: Enter a custom name for the session file to save it with a specific identifier.
                - **Save Session (JSON)**: Download a local copy of your chat history.
                - **Restore Session (JSON)**: Upload a previously saved JSON file to load a specific chat history.
                - **Available Sessions**: List of saved session files with previews. Click to load into the current tab.
                - **Reset Chat**: Clears the current session and starts fresh with the agent's introduction.
                """)

            # Custom filename input for the current session
            custom_filename = st.text_input("Custom Session Filename (optional)", value=current_session.get("custom_filename", ""), placeholder="e.g., my_custom_session")
            if custom_filename != current_session.get("custom_filename", ""):
                current_session["custom_filename"] = custom_filename
                SESSION_FILE_PATH = get_session_file_path(st.session_state.active_tab, custom_filename)
                if current_session["messages"]:
                    save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                    st.rerun()

            uploaded_file = st.file_uploader("Restore Session (JSON)", type=["json"])
            if uploaded_file is not None and "session_restored" not in st.session_state:
                try:
                    restored_data = json.load(uploaded_file)
                    if isinstance(restored_data, list):
                        current_session["messages"] = restored_data
                        st.session_state.session_restored = True
                        save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                        st.success(f"Session restored from {uploaded_file.name}")
                        st.rerun()
                    else:
                        st.error("Invalid session file: Must contain a list of messages in JSON format.")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in uploaded file.")
                except Exception as e:
                    st.error(f"Error restoring session: {e}")
                    logger.error(f"Error restoring session: {e}")

            if current_session["messages"]:
                session_json = json.dumps(current_session["messages"], indent=2)
                current_date = datetime.now().strftime("%Y-%m-%d")
                st.download_button(
                    label="Save Session (JSON)",
                    data=session_json,
                    file_name=f"chat_session_{st.session_state.active_tab}_{current_date}.json",
                    mime="application/json"
                )

            auto_save = st.toggle("Auto-Save Session", value=st.session_state.get("auto_save", True))
            st.session_state.auto_save = auto_save

            # Available Sessions with Preview
            st.subheader("Available Sessions")
            session_files = list_session_files()
            session_feedback_placeholder = st.empty()
            if session_files:
                st.markdown("Click a file to load the session, or use the trash icon to delete:")
                for file in session_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button(file, key=f"load_{file}", use_container_width=True):
                            file_path = os.path.join("chats", file)
                            loaded_data, success = load_session_from_file(file_path)
                            if success:
                                current_session["messages"] = loaded_data
                                st.success(f"Session loaded from {file}")
                                if st.session_state.auto_save:
                                    save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                                st.rerun()
                            else:
                                st.error(f"Failed to load session from {file}")
                    with col2:
                        if st.button("🗑️", key=f"delete_{file}", help=f"Delete {file}"):
                            file_path = os.path.join("chats", file)
                            if os.path.abspath(file_path) == os.path.abspath(SESSION_FILE_PATH):
                                with session_feedback_placeholder.container():
                                    st.markdown("---")
                                    st.error(
                                        "Cannot delete the currently active session file. Please switch to another session or reset the chat first.",
                                        icon="🚫")
                                    st.markdown("---")
                            else:
                                try:
                                    os.remove(file_path)
                                    logger.info(f"Deleted session file: {file_path}")
                                    with session_feedback_placeholder.container():
                                        st.markdown("---")
                                        st.success(f"Deleted {file}", icon="✅")
                                        st.markdown("---")
                                    st.rerun()
                                except Exception as e:
                                    logger.error(f"Error deleting session file {file_path}: {e}")
                                    with session_feedback_placeholder.container():
                                        st.markdown("---")
                                        st.error(f"Failed to delete {file}: {e}", icon="❌")
                                        st.markdown("---")
            else:
                st.markdown("No saved sessions found in 'chats' directory.")

            # New Feature: Agent Selection
            st.header("Switch Agent")
            with st.expander("Help: Switching Agents", expanded=False):
                st.markdown("""
                **Switching Agents Explained:**
                - **Select Alias**: Choose a profile (alias) to access specific API configurations.
                - **Enter Project ID**: Provide the ID of the project to list available agents.
                - **Select Agent**: Pick an agent to chat with. You'll be prompted to confirm before switching.
                - Switching to a new agent starts a fresh session in a new tab.
                """)

            # Initialize session state for alias, project ID, and agent selection
            if "selected_alias" not in st.session_state:
                st.session_state.selected_alias = "-"
            if "project_id_input" not in st.session_state:
                st.session_state.project_id_input = ""
            if "selected_agent" not in st.session_state:
                st.session_state.selected_agent = "-"
            if "confirm_switch" not in st.session_state:
                st.session_state.confirm_switch = False

            # Alias Selection
            alias_list = get_alias_list()
            selected_alias = st.selectbox("Select Alias (Profile)", alias_list, index=alias_list.index(st.session_state.selected_alias))
            if selected_alias != st.session_state.selected_alias:
                st.session_state.selected_alias = selected_alias
                st.session_state.selected_agent = "-"
                st.rerun()

            # Project ID Input
            project_id_input = st.text_input("Enter Project ID", value=st.session_state.project_id_input, placeholder="e.g., 2ca6883f-6778-40bb-bcc1-85451fb11107")
            if project_id_input != st.session_state.project_id_input:
                st.session_state.project_id_input = project_id_input
                st.session_state.selected_agent = "-"
                st.rerun()

            # Agent Selection
            agent_list = get_agent_list(st.session_state.selected_alias, st.session_state.project_id_input) if st.session_state.selected_alias != "-" and st.session_state.project_id_input else ["-"]
            selected_agent = st.selectbox("Select Agent", agent_list, index=agent_list.index(st.session_state.selected_agent) if st.session_state.selected_agent in agent_list else 0)
            if selected_agent != st.session_state.selected_agent:
                st.session_state.selected_agent = selected_agent
                st.session_state.confirm_switch = False

            # Agent Info Preview
            if st.session_state.selected_agent != "-" and st.session_state.selected_agent in st.session_state.agent_data:
                agent_obj = st.session_state.agent_data.get(st.session_state.selected_agent)
                if agent_obj and getattr(agent_obj, 'description', None):
                    st.markdown("**Agent Description:**")
                    st.markdown(f"{agent_obj.description[:200]}{'...' if len(agent_obj.description) > 200 else ''}")

            # Favorite/Recent Agents List
            st.subheader("Recent Agents")
            recent_agents = load_recent_agents()
            if recent_agents:
                for agent in recent_agents:
                    if st.button(f"Switch to {agent}", key=f"recent_{agent}"):
                        if agent != st.session_state.active_tab:
                            if agent not in st.session_state.sessions:
                                st.session_state.sessions[agent] = {
                                    "messages": [],
                                    "chat_session": AgentChatSession(agent),
                                    "custom_filename": "",
                                    "active": True
                                }
                            st.session_state.active_tab = agent
                            save_recent_agents(agent)
                            st.rerun()
            else:
                st.markdown("No recent agents found.")

            # Confirmation for switching agent
            if st.session_state.selected_agent != "-" and st.session_state.selected_agent.split(" (ID: ")[0] != st.session_state.active_tab:
                if not st.session_state.confirm_switch:
                    st.warning(f"Do you wish to chat with {st.session_state.selected_agent.split(' (ID: ')[0]}? This will start a new session in a new tab.", icon="⚠️")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Confirm Switch"):
                            st.session_state.confirm_switch = True
                            new_agent_name = st.session_state.selected_agent.split(" (ID: ")[0]
                            if new_agent_name not in st.session_state.sessions:
                                st.session_state.sessions[new_agent_name] = {
                                    "messages": [],
                                    "chat_session": AgentChatSession(new_agent_name),
                                    "custom_filename": "",
                                    "active": True
                                }
                            st.session_state.active_tab = new_agent_name
                            save_recent_agents(new_agent_name)
                            current_session = st.session_state.sessions[new_agent_name]
                            if not current_session["messages"]:
                                intro = current_session["chat_session"].get_answer(
                                    ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                                     "stating who you are and what you do. Nothing else."]
                                )
                                if "Agent not found" in str(intro):
                                    st.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                                    logger.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                                    return
                                current_session["messages"] = [{"role": "assistant", "content": intro}]
                            SESSION_FILE_PATH = get_session_file_path(new_agent_name, current_session.get("custom_filename", ""))
                            if st.session_state.auto_save:
                                save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                            st.rerun()
                    with col2:
                        if st.button("Cancel"):
                            st.session_state.selected_agent = "-"
                            st.session_state.confirm_switch = False
                            st.rerun()
                else:
                    st.success(f"Switched to agent {st.session_state.selected_agent.split(' (ID: ')[0]}!", icon="✅")

        # Reset chat button for current tab
        if st.button("Reset Chat"):
            current_session["messages"] = []
            intro = current_session["chat_session"].get_answer(
                ["You're about to speak to a user. Introduce yourself in a clear and concise manner, "
                 "stating who you are and what you do. Nothing else."]
            )
            if "Agent not found" in str(intro):
                st.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                logger.error("The specified agent doesn't seem to exist. Please review the name and try again.")
                return
            current_session["messages"] = [{"role": "assistant", "content": intro}]
            if st.session_state.auto_save:
                save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
            st.rerun()

        error_container = st.empty()

        # "Complete Answer" button logic
        if (current_session["messages"] and
            current_session["messages"][-1]["role"] == "assistant" and
            "complete_answer_triggered" not in st.session_state):
            if st.button("Complete Answer"):
                st.session_state.complete_answer_triggered = True
                last_assistant_message = current_session["messages"][-1]["content"]
                continuation_prompt = (
                    f"The previous answer was: '{last_assistant_message}'. "
                    "It seems incomplete. Please continue and complete the answer."
                )
                current_session["messages"].append({"role": "user", "content": continuation_prompt})
                with st.chat_message("user"):
                    st.markdown(continuation_prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Continuing answer..."):
                        response_placeholder = st.empty()
                        continued_answer = ""
                        result = current_session["chat_session"].stream_answer(current_session["messages"])
                        for chunk in result:
                            continued_answer += chunk
                            sanitized_answer = continued_answer
                            response_placeholder.markdown(f'{sanitized_answer}')
                        current_session["messages"].append({"role": "assistant", "content": continued_answer})
                if st.session_state.auto_save:
                    save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                del st.session_state.complete_answer_triggered
                st.rerun()

        # Chat input for current tab
        if user_input := st.chat_input(f"Ask {st.session_state.active_tab}"):
            if not user_input.strip():
                logger.warning(f"Empty input submitted for agent {st.session_state.active_tab}")
                with error_container.container():
                    st.error(f"Unable to communicate with the agent {st.session_state.active_tab}")
                return
            error_container.empty()

            # Append user message to session
            with st.chat_message("user"):
                st.markdown(f"{user_input}")
            current_session["messages"].append({"role": "user", "content": user_input})

            # Save session if auto_save is enabled
            if st.session_state.auto_save:
                save_session_to_file(current_session["messages"], SESSION_FILE_PATH)

            # Stream assistant response
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    response_placeholder = st.empty()
                    answer = ""
                    result = current_session["chat_session"].stream_answer(current_session["messages"])
                    for chunk in result:
                        answer += chunk
                        sanitized_answer = answer
                        response_placeholder.markdown(f'{sanitized_answer}')

                    # Append the complete response to session
                    current_session["messages"].append({"role": "assistant", "content": answer})

            # Save session again after assistant response
            if st.session_state.auto_save:
                save_session_to_file(current_session["messages"], SESSION_FILE_PATH)
                st.rerun()
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        logger.error(f"An unexpected error occurred: {e}")
        Console.write_stderr("An unexpected error has occurred. Please contact the developers.")
        sys.exit(1)


def render_chat_history(messages, search_term="", tab_key_prefix="", session=None):
    """Render chat history with search filter, copy, and edit buttons."""

    global auto_save

    filtered_messages = []
    if search_term:
        search_term = search_term.lower()
        filtered_messages = [msg for msg in messages if search_term in msg["content"].lower()]
    else:
        filtered_messages = messages

    if search_term and not filtered_messages:
        st.info("No messages match your search term.", icon="ℹ️")
    elif search_term:
        st.info(f"Showing {len(filtered_messages)} messages matching '{search_term}'", icon="🔍")

    # Find the index of the last user message in the filtered list for edit button display
    last_user_msg_index = None
    for i, msg in enumerate(filtered_messages):
        if msg["role"] == "user":
            last_user_msg_index = i

    for i, message in enumerate(filtered_messages):
        with st.chat_message(message["role"]):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(message["content"])
            with col2:
                # Edit Button - Only for the last user message
                if message["role"] == "user" and i == last_user_msg_index:
                    if st.button("✏️", key=f"{tab_key_prefix}_edit_{i}", help="Edit this message"):
                        session["editing_message"] = i
                        session["edit_content"] = message["content"]
                        st.rerun()

    # Handle Message Editing
    if session and session.get("editing_message") is not None:
        with st.container():
            st.markdown("**Editing Message:**")
            new_content = st.text_area(
                "Edit your message:",
                value=session.get("edit_content", ""),
                key=f"{tab_key_prefix}_edit_area"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Edit", key=f"{tab_key_prefix}_save_edit"):
                    # Update the message content
                    messages[session["editing_message"]]["content"] = new_content
                    # Check if there's a subsequent agent response to remove
                    if session["editing_message"] + 1 < len(messages) and messages[session["editing_message"] + 1]["role"] == "assistant":
                        messages.pop(session["editing_message"] + 1)  # Remove the old response
                        session["regenerate_response"] = True  # Flag to regenerate response
                    session["editing_message"] = None
                    session["edit_content"] = ""
                    st.rerun()
            with col2:
                if st.button("Cancel Edit", key=f"{tab_key_prefix}_cancel_edit"):
                    session["editing_message"] = None
                    session["edit_content"] = ""
                    session["regenerate_response"] = False
                    st.rerun()

    # Regenerate agent response if needed after edit
    if session and session.get("regenerate_response"):
        with st.chat_message("assistant"):
            with st.spinner("Regenerating response..."):
                response_placeholder = st.empty()
                answer = ""
                result = current_session["chat_session"].stream_answer(messages)
                for chunk in result:
                    answer += chunk
                    sanitized_answer = answer
                    response_placeholder.markdown(f'{sanitized_answer}')
                messages.append({"role": "assistant", "content": answer})
        if st.session_state.auto_save:
            save_session_to_file(messages, SESSION_FILE_PATH)
        session["regenerate_response"] = False
        st.rerun()


if __name__ == "__main__":
    run_streamlit_chat()