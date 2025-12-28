GEAI Chat GUI Documentation
===========================

Overview
--------

The GEAI Chat GUI is a Streamlit-based graphical user interface (GUI) for interacting with AI agents provided by the Globant Enterprise AI (GEAI) platform. This interface is launched via the `geai chat agent` command with the `--gui` or `-g` flag. It allows users to chat with specified agents, manage chat sessions, switch between agents, and customize session storage settings.

This documentation provides an overview of the GUI's features, usage instructions, and command-line invocation.

Command-Line Invocation
-----------------------

The Streamlit GUI is not run as a standalone Streamlit app but is invoked through the GEAI CLI. The relevant command and options are as follows:

.. code-block:: bash

    geai chat agent --agent-name <agent_name> --gui

**Options:**

- ``--agent-name`` or ``-n``: Specifies the name or ID of the agent to interact with. This is a required argument.
- ``--gui`` or ``-g``: Launches the Streamlit GUI for an interactive chat experience. No additional argument is needed for this flag.

**Example:**

.. code-block:: bash

    geai chat agent --agent-name "MyAgent" --gui

This command launches the Streamlit GUI for chatting with the agent named "MyAgent".

Features of the Streamlit GUI
-----------------------------

The GEAI Chat GUI provides a user-friendly interface for interacting with AI agents. Below are the key features, organized by their location in the interface (main area and sidebar).

Main Interface
~~~~~~~~~~~~~~

1. **Chat Window:**
   - Displays the conversation history with the selected agent.
   - Supports real-time message streaming for agent responses.
   - Allows searching through chat history using a keyword filter.
   - Provides options to edit the last user message and regenerate the agent's response if needed.
   - Includes a "Complete Answer" button to prompt the agent to continue an incomplete response.

2. **Chat Input:**
   - Located at the bottom of the main window, allowing users to type and send messages to the agent.

3. **Session Information:**
   - Displays the path where the current session will be saved (e.g., ``chats/chat_session_<agent_name>_<date>.json``).

4. **Reset Chat:**
   - A button to clear the current chat history and start a fresh session with the agent's introductory message.

Sidebar Features
~~~~~~~~~~~~~~~~

The sidebar contains controls for session management and agent switching.

1. **Session Management:**
   - **Auto-Save Session:** A toggle to enable or disable automatic saving of chat history to a server-side file after each message or action.
   - **Custom Session Filename:** An input field to specify a custom filename for saving the session (stored in the ``chats`` directory).
   - **Save Session (JSON):** A download button to save the current chat history as a JSON file locally.
   - **Restore Session (JSON):** A file uploader to load a previously saved JSON session file into the current chat.
   - **Available Sessions:** A list of saved session files in the ``chats`` directory, with options to load or delete them. Note: The active session file cannot be deleted.
   - **Help Section:** An expandable section explaining session saving and restoring functionalities.

2. **Agent Switching:**
   - **Select Alias:** A dropdown to choose a profile (alias) for accessing specific API configurations.
   - **Enter Project ID:** An input field for specifying the project ID to list available agents.
   - **Select Agent:** A dropdown to pick an agent from the list retrieved based on the alias and project ID.
   - **Agent Description Preview:** Displays a brief description of the selected agent (if available).
   - **Recent Agents:** A list of recently used agents for quick switching.
   - **Confirmation for Switching:** Prompts the user to confirm before switching to a new agent, which starts a fresh session in a new tab.
   - **Help Section:** An expandable section explaining the agent switching process.

Usage Instructions
------------------

1. **Launching the GUI:**
   - Run the command ``geai chat agent --agent-name <agent_name> --gui`` to start the Streamlit interface for the specified agent.
   - The browser will open automatically (if configured) or provide a URL to access the interface.

2. **Chatting with an Agent:**
   - Type your message in the chat input field at the bottom of the main window and press Enter.
   - The agent's response will stream in real-time in the chat window.
   - Use the "Complete Answer" button if the agent's response seems incomplete.
   - Search through the chat history using the search bar above the chat window.
   - Edit your last message by clicking the edit button (✏️) next to it, modify the content, and save to regenerate the agent's response.

3. **Managing Sessions:**
   - Enable "Auto-Save Session" in the sidebar to automatically save chat history to a server-side file.
   - Specify a custom filename for the session if desired.
   - Download the current session as a JSON file using the "Save Session (JSON)" button.
   - Upload a previously saved JSON file to restore a session using the file uploader.
   - View and manage saved sessions under "Available Sessions" (load or delete files as needed).

4. **Switching Agents:**
   - In the sidebar under "Switch Agent", select an alias and enter a project ID to list available agents.
   - Choose an agent from the dropdown and review its description (if available).
   - Confirm the switch to start a new session with the selected agent in a new tab.
   - Alternatively, switch to a recently used agent directly from the "Recent Agents" list.

5. **Resetting the Chat:**
   - Click the "Reset Chat" button in the main interface to clear the current session and start fresh with the agent's introduction.

File Storage
------------

- **Default Session Files:** Chat sessions are saved by default in the ``chats`` directory with filenames in the format ``chat_session_<agent_name>_<YYYY-MM-DD>.json``.
- **Custom Filenames:** Users can specify custom filenames via the sidebar, which are also stored in the ``chats`` directory.
- **Recent Agents:** A list of recently used agents is saved in ``recent_agents.json`` for quick access across sessions.

Troubleshooting
---------------

- **Agent Not Found:** If the specified agent does not exist, an error message will be displayed. Verify the agent name or ID and try again.
- **Session File Errors:** Errors during saving or loading session files are logged and displayed as Streamlit error messages. Ensure the ``chats`` directory has appropriate read/write permissions.
- **Unexpected Errors:** Any unhandled exceptions are logged and displayed in the GUI. Contact support at ``geai-sdk@globant.com`` for assistance.
