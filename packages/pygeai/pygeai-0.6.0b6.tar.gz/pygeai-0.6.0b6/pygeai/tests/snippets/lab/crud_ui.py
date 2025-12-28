import json
import streamlit as st
from typing import Optional, List, Dict, Any
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList,
    Tool, ToolParameter, ResourcePool, ResourcePoolTool, ResourcePoolList,
    Task, AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow,
    Variable, VariableList, FilterSettings
)

# Initialize the manager
manager = AILabManager()

# Streamlit App
st.title("AI Lab Manager Interface")
st.write("Manage Agents, Tools, Tasks, and Agentic Processes for your AI Lab project.")

# Project ID Input at the top of the app
project_id = st.text_input("Project ID (Required)", value="2ca6883f-6778-40bb-bcc1-85451fb11107", key="project_id")
if not project_id:
    st.error("Please enter a valid Project ID to proceed.")
    st.stop()

# Helper function to display results or errors with detailed feedback
def display_result(result: Any, operation: str, entity_type: str, entity_name: str):
    """
    Displays success or error messages based on the result of an operation.

    Args:
        result: The response object from the AILabManager operation.
        operation: The type of operation ('create', 'update', 'delete').
        entity_type: The type of entity ('Agent', 'Tool', 'Task', 'Process').
        entity_name: The name or ID of the entity for personalized feedback.
    """
    success_msg = {
        'create': f"{entity_type} '{entity_name}' created successfully!",
        'update': f"{entity_type} '{entity_name}' updated successfully!",
        'delete': f"{entity_type} '{entity_name}' deleted successfully!"
    }
    error_msg = {
        'create': f"Failed to create {entity_type.lower()} '{entity_name}'",
        'update': f"Failed to update {entity_type.lower()} '{entity_name}'",
        'delete': f"Failed to delete {entity_type.lower()} '{entity_name}'"
    }

    if hasattr(result, 'errors') and result.errors:
        st.error(f"{error_msg[operation]}: {result.errors}")
    elif isinstance(result, dict) and 'errors' in result:
        st.error(f"{error_msg[operation]}: {result['errors']}")
    elif hasattr(result, '__dict__') and 'errors' in result.__dict__ and result.__dict__['errors']:
        st.error(f"{error_msg[operation]}: {result.__dict__['errors']}")
    else:
        st.success(success_msg[operation])

# Create tabs for different components
agent_tab, tool_tab, task_tab, process_tab = st.tabs(["Agents", "Tools", "Tasks", "Agentic Processes"])

# --- Agents Tab ---
with agent_tab:
    st.header("Manage Agents")

    # JSON Upload Section
    st.subheader("Upload Agent JSON")
    uploaded_agent_file = st.file_uploader("Upload Agent JSON File", type=["json"], key="agent_json_upload")
    if uploaded_agent_file is not None:
        try:
            agent_json = json.load(uploaded_agent_file)
            st.json(agent_json)  # Display the JSON for user verification

            # Parse JSON to Agent object
            agent_data_json = agent_json.get("agentData", {})
            prompt_json = agent_data_json.get("prompt", {})
            llm_config_json = agent_data_json.get("llmConfig", {})
            sampling_json = llm_config_json.get("sampling", {})
            models_json = agent_data_json.get("models", [])

            agent = Agent(
                id=agent_json.get("id"),
                name=agent_json.get("name", ""),
                access_scope=agent_json.get("accessScope", "private"),
                description=agent_json.get("description"),
                job_description=agent_json.get("jobDescription"),
                is_draft=agent_json.get("isDraft", True),
                agent_data=AgentData(
                    prompt=Prompt(
                        context=prompt_json.get("context", ""),
                        instructions=prompt_json.get("instructions", "")
                    ),
                    llm_config=LlmConfig(
                        max_tokens=llm_config_json.get("maxTokens", 1500),
                        sampling=Sampling(
                            temperature=sampling_json.get("temperature", 0.7),
                            top_k=sampling_json.get("topK", 50),
                            top_p=sampling_json.get("topP", 1.0)
                        ),
                        timeout=llm_config_json.get("timeout", 60)
                    ),
                    models=ModelList(models=[
                        Model(
                            name=model.get("name", ""),
                            llm_config=LlmConfig(
                                max_tokens=model.get("llmConfig", {}).get("maxTokens", 0),
                                sampling=Sampling(
                                    temperature=model.get("llmConfig", {}).get("sampling", {}).get("temperature", 0.7)
                                )
                            )
                        ) for model in models_json
                    ]),
                    resource_pools=None  # Simplified; can be extended if needed
                )
            )

            st.success("Agent JSON parsed successfully!")
            if st.button("Create/Update Agent from JSON", key="agent_json_submit"):
                if agent.id:
                    result = manager.update_agent(project_id=project_id, agent=agent, automatic_publish=False)
                    display_result(result, 'update', 'Agent', agent.name)
                else:
                    result = manager.create_agent(project_id=project_id, agent=agent, automatic_publish=False)
                    display_result(result, 'create', 'Agent', agent.name)
        except json.JSONDecodeError:
            st.error("Invalid JSON format in uploaded file.")
        except Exception as e:
            st.error(f"Error parsing Agent JSON: {str(e)}")

    with st.form("agent_form"):
        st.subheader("Create or Update Agent")
        agent_name = st.text_input("Name (Required)", key="agent_name")
        agent_access_scope = st.selectbox("Access Scope (Required)", ["private", "public"], key="agent_access_scope")
        agent_public_name = st.text_input("Public Name (Required if Public)", key="agent_public_name")
        agent_description = st.text_area("Description (Optional)", key="agent_description")
        agent_job_description = st.text_area("Job Description (Optional)", key="agent_job_description")
        agent_avatar_image = st.text_input("Avatar Image URL (Optional)", key="agent_avatar_image")
        agent_is_draft = st.checkbox("Is Draft (Optional)", value=True, key="agent_is_draft")
        # Simplified Agent Data (focus on key fields, default nested structures)
        prompt_instructions = st.text_area("Prompt Instructions (Required for Agent Data)", key="agent_prompt_instructions")
        llm_max_tokens = st.number_input("LLM Max Tokens (Required for Agent Data)", min_value=1, value=1500, key="agent_max_tokens")
        # For update/delete
        agent_id = st.text_input("Agent ID (Required for Update/Delete)", key="agent_id")

        col1, col2, col3 = st.columns(3)
        with col1:
            create_agent_btn = st.form_submit_button("Create Agent")
        with col2:
            update_agent_btn = st.form_submit_button("Update Agent")
        with col3:
            delete_agent_btn = st.form_submit_button("Delete Agent")

        if create_agent_btn:
            if not agent_name or not prompt_instructions:
                st.error("Name and Prompt Instructions are required.")
            else:
                agent = Agent(
                    name=agent_name,
                    access_scope=agent_access_scope,
                    public_name=agent_public_name if agent_public_name else None,
                    description=agent_description if agent_description else None,
                    job_description=agent_job_description if agent_job_description else None,
                    avatar_image=agent_avatar_image if agent_avatar_image else None,
                    is_draft=agent_is_draft,
                    agent_data=AgentData(
                        prompt=Prompt(instructions=prompt_instructions),
                        llm_config=LlmConfig(max_tokens=llm_max_tokens),
                        models=ModelList(models=[Model(name="gpt-3.5-turbo")]),
                        resource_pools=None
                    )
                )
                result = manager.create_agent(project_id=project_id, agent=agent, automatic_publish=False)
                display_result(result, 'create', 'Agent', agent_name)

        if update_agent_btn:
            if not agent_id or not agent_name or not prompt_instructions:
                st.error("Agent ID, Name, and Prompt Instructions are required for update.")
            else:
                agent = Agent(
                    id=agent_id,
                    name=agent_name,
                    access_scope=agent_access_scope,
                    public_name=agent_public_name if agent_public_name else None,
                    description=agent_description if agent_description else None,
                    job_description=agent_job_description if agent_job_description else None,
                    avatar_image=agent_avatar_image if agent_avatar_image else None,
                    is_draft=agent_is_draft,
                    agent_data=AgentData(
                        prompt=Prompt(instructions=prompt_instructions),
                        llm_config=LlmConfig(max_tokens=llm_max_tokens),
                        models=ModelList(models=[Model(name="gpt-3.5-turbo")]),
                        resource_pools=None
                    )
                )
                result = manager.update_agent(project_id=project_id, agent=agent, automatic_publish=False)
                display_result(result, 'update', 'Agent', agent_name)

        if delete_agent_btn:
            if not agent_id:
                st.error("Agent ID is required for deletion.")
            else:
                result = manager.delete_agent(project_id=project_id, agent_id=agent_id)
                display_result(result, 'delete', 'Agent', f"ID: {agent_id}")

# --- Tools Tab ---
with tool_tab:
    st.header("Manage Tools")

    # JSON Upload Section
    st.subheader("Upload Tool JSON")
    uploaded_tool_file = st.file_uploader("Upload Tool JSON File", type=["json"], key="tool_json_upload")
    if uploaded_tool_file is not None:
        try:
            tool_json = json.load(uploaded_tool_file)
            st.json(tool_json)  # Display the JSON for user verification

            # Parse JSON to Tool object
            parameters_json = tool_json.get("parameters", [])
            parameters = [
                ToolParameter(
                    key=param.get("key", ""),
                    data_type=param.get("dataType", ""),
                    description=param.get("description", ""),
                    is_required=param.get("isRequired", False),
                    type=param.get("type"),
                    value=param.get("value"),
                    from_secret=param.get("fromSecret", False)
                ) for param in parameters_json
            ]

            tool = Tool(
                id=tool_json.get("id"),
                name=tool_json.get("name", ""),
                description=tool_json.get("description", ""),
                scope=tool_json.get("scope", "builtin"),
                access_scope=tool_json.get("accessScope"),
                public_name=None,  # Optional field, not in JSON example
                icon=None,  # Optional field, not in JSON example
                open_api=None,  # Optional field, not in JSON example
                report_events="None",  # Default value
                is_draft=False,  # Default value
                parameters=parameters if parameters else None
            )

            st.success("Tool JSON parsed successfully!")
            if st.button("Create/Update Tool from JSON", key="tool_json_submit"):
                if tool.id:
                    result = manager.update_tool(project_id=project_id, tool=tool, automatic_publish=False)
                    display_result(result, 'update', 'Tool', tool.name)
                else:
                    result = manager.create_tool(project_id=project_id, tool=tool, automatic_publish=False)
                    display_result(result, 'create', 'Tool', tool.name)
        except json.JSONDecodeError:
            st.error("Invalid JSON format in uploaded file.")
        except Exception as e:
            st.error(f"Error parsing Tool JSON: {str(e)}")

    with st.form("tool_form"):
        st.subheader("Create or Update Tool")
        tool_name = st.text_input("Name (Required)", key="tool_name")
        tool_description = st.text_area("Description (Required)", key="tool_description")
        tool_scope = st.selectbox("Scope (Required)", ["builtin", "external", "api"], key="tool_scope")
        tool_access_scope = st.selectbox("Access Scope (Optional)", ["", "private", "public"], key="tool_access_scope")
        tool_public_name = st.text_input("Public Name (Required if Public)", key="tool_public_name")
        tool_icon = st.text_input("Icon URL (Optional)", key="tool_icon")
        tool_open_api = st.text_input("OpenAPI URL (Required if Scope is API)", key="tool_open_api")
        tool_report_events = st.selectbox("Report Events (Optional)", ["None", "All", "Start", "Finish", "Progress"], key="tool_report_events")
        tool_is_draft = st.checkbox("Is Draft (Optional)", value=True, key="tool_is_draft")
        # Simplified Parameters Input
        param_key = st.text_input("Parameter Key (Optional)", key="tool_param_key")
        param_data_type = st.text_input("Parameter Data Type (Optional)", key="tool_param_data_type")
        param_desc = st.text_area("Parameter Description (Optional)", key="tool_param_desc")
        param_is_required = st.checkbox("Parameter Is Required (Optional)", value=False, key="tool_param_is_required")
        # For update/delete
        tool_id = st.text_input("Tool ID (Required for Update/Delete)", key="tool_id")

        col1, col2, col3 = st.columns(3)
        with col1:
            create_tool_btn = st.form_submit_button("Create Tool")
        with col2:
            update_tool_btn = st.form_submit_button("Update Tool")
        with col3:
            delete_tool_btn = st.form_submit_button("Delete Tool")

        if create_tool_btn:
            if not tool_name or not tool_description:
                st.error("Name and Description are required.")
            elif tool_scope == "api" and not tool_open_api:
                st.error("OpenAPI URL is required for API scope.")
            else:
                parameters = []
                if param_key and param_data_type:
                    parameters.append(ToolParameter(
                        key=param_key,
                        data_type=param_data_type,
                        description=param_desc if param_desc else "",
                        is_required=param_is_required
                    ))
                tool = Tool(
                    name=tool_name,
                    description=tool_description,
                    scope=tool_scope,
                    access_scope=tool_access_scope if tool_access_scope else None,
                    public_name=tool_public_name if tool_public_name else None,
                    icon=tool_icon if tool_icon else None,
                    open_api=tool_open_api if tool_open_api else None,
                    report_events=tool_report_events,
                    is_draft=tool_is_draft,
                    parameters=parameters if parameters else None
                )
                result = manager.create_tool(project_id=project_id, tool=tool, automatic_publish=False)
                display_result(result, 'create', 'Tool', tool_name)

        if update_tool_btn:
            if not tool_id or not tool_name or not tool_description:
                st.error("Tool ID, Name, and Description are required for update.")
            elif tool_scope == "api" and not tool_open_api:
                st.error("OpenAPI URL is required for API scope.")
            else:
                parameters = []
                if param_key and param_data_type:
                    parameters.append(ToolParameter(
                        key=param_key,
                        data_type=param_data_type,
                        description=param_desc if param_desc else "",
                        is_required=param_is_required
                    ))
                tool = Tool(
                    id=tool_id,
                    name=tool_name,
                    description=tool_description,
                    scope=tool_scope,
                    access_scope=tool_access_scope if tool_access_scope else None,
                    public_name=tool_public_name if tool_public_name else None,
                    icon=tool_icon if tool_icon else None,
                    open_api=tool_open_api if tool_open_api else None,
                    report_events=tool_report_events,
                    is_draft=tool_is_draft,
                    parameters=parameters if parameters else None
                )
                result = manager.update_tool(project_id=project_id, tool=tool, automatic_publish=False)
                display_result(result, 'update', 'Tool', tool_name)

        if delete_tool_btn:
            if not tool_id:
                st.error("Tool ID is required for deletion.")
            else:
                result = manager.delete_tool(project_id=project_id, tool_id=tool_id)
                display_result(result, 'delete', 'Tool', f"ID: {tool_id}")

# --- Tasks Tab ---
with task_tab:
    st.header("Manage Tasks")

    with st.form("task_form"):
        st.subheader("Create or Update Task")
        task_name = st.text_input("Name (Required)", key="task_name")
        task_description = st.text_area("Description (Optional)", key="task_description")
        task_title_template = st.text_input("Title Template (Optional)", key="task_title_template")
        task_is_draft = st.checkbox("Is Draft (Optional)", value=True, key="task_is_draft")
        prompt_instructions = st.text_area("Prompt Instructions (Optional)", key="task_prompt_instructions")
        # For update/delete
        task_id = st.text_input("Task ID (Required for Update/Delete)", key="task_id")

        col1, col2, col3 = st.columns(3)
        with col1:
            create_task_btn = st.form_submit_button("Create Task")
        with col2:
            update_task_btn = st.form_submit_button("Update Task")
        with col3:
            delete_task_btn = st.form_submit_button("Delete Task")

        if create_task_btn:
            if not task_name:
                st.error("Name is required.")
            else:
                task = Task(
                    name=task_name,
                    description=task_description if task_description else None,
                    title_template=task_title_template if task_title_template else None,
                    is_draft=task_is_draft,
                    prompt_data=Prompt(instructions=prompt_instructions) if prompt_instructions else None
                )
                result = manager.create_task(project_id=project_id, task=task, automatic_publish=False)
                display_result(result, 'create', 'Task', task_name)

        if update_task_btn:
            if not task_id or not task_name:
                st.error("Task ID and Name are required for update.")
            else:
                task = Task(
                    id=task_id,
                    name=task_name,
                    description=task_description if task_description else None,
                    title_template=task_title_template if task_title_template else None,
                    is_draft=task_is_draft,
                    prompt_data=Prompt(instructions=prompt_instructions) if prompt_instructions else None
                )
                result = manager.update_task(project_id=project_id, task=task, automatic_publish=False)
                display_result(result, 'update', 'Task', task_name)

        if delete_task_btn:
            if not task_id:
                st.error("Task ID is required for deletion.")
            else:
                result = manager.delete_task(project_id=project_id, task_id=task_id)
                display_result(result, 'delete', 'Task', f"ID: {task_id}")

# --- Agentic Processes Tab ---
with process_tab:
    st.header("Manage Agentic Processes")

    with st.form("process_form"):
        st.subheader("Create or Update Agentic Process")
        process_name = st.text_input("Name (Required)", key="process_name")
        process_key = st.text_input("Key (Optional)", key="process_key")
        process_description = st.text_area("Description (Optional)", key="process_description")
        process_is_draft = st.checkbox("Is Draft (Optional)", value=True, key="process_is_draft")
        kb_name = st.text_input("Knowledge Base Name (Optional)", key="process_kb_name")
        # For update/delete
        process_id = st.text_input("Process ID (Required for Update/Delete)", key="process_id")

        col1, col2, col3 = st.columns(3)
        with col1:
            create_process_btn = st.form_submit_button("Create Process")
        with col2:
            update_process_btn = st.form_submit_button("Update Process")
        with col3:
            delete_process_btn = st.form_submit_button("Delete Process")

        if create_process_btn:
            if not process_name:
                st.error("Name is required.")
            else:
                process = AgenticProcess(
                    name=process_name,
                    key=process_key if process_key else None,
                    description=process_description if process_description else None,
                    is_draft=process_is_draft,
                    kb=KnowledgeBase(name=kb_name) if kb_name else None
                )
                result = manager.create_process(project_id=project_id, process=process, automatic_publish=False)
                display_result(result, 'create', 'Process', process_name)

        if update_process_btn:
            if not process_id or not process_name:
                st.error("Process ID and Name are required for update.")
            else:
                process = AgenticProcess(
                    id=process_id,
                    name=process_name,
                    key=process_key if process_key else None,
                    description=process_description if process_description else None,
                    is_draft=process_is_draft,
                    kb=KnowledgeBase(name=kb_name) if kb_name else None
                )
                result = manager.update_process(project_id=project_id, process=process, automatic_publish=False)
                display_result(result, 'update', 'Process', process_name)

        if delete_process_btn:
            if not process_id:
                st.error("Process ID is required for deletion.")
            else:
                result = manager.delete_process(project_id=project_id, process_id=process_id)
                display_result(result, 'delete', 'Process', f"ID: {process_id}")