from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList,
    Tool, ToolParameter, ToolMessage,
    Task,
    AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow,
    Variable, ProcessInstance, VariableList
)

manager = AILabManager()
project_id = "2ca6883f-6778-40bb-bcc1-85451fb11107"

created_entities = {
    "agent_id": None,
    "tool_id": None,
    "task_id": None,
    "process_id": None,
    "instance_id": None
}


def rollback():
    print("\n=== Initiating Rollback ===")
    if created_entities["instance_id"]:
        print(f"Deleting instance {created_entities['instance_id']}...")
        result = manager.abort_instance(project_id=project_id, instance_id=created_entities["instance_id"])
        print(f"Rollback: {result}")
    if created_entities["process_id"]:
        print(f"Deleting process {created_entities['process_id']}...")
        result = manager.delete_process(project_id=project_id, process_id=created_entities["process_id"])
        print(f"Rollback: {result}")
    if created_entities["task_id"]:
        print(f"Deleting task {created_entities['task_id']}...")
        result = manager.delete_task(project_id=project_id, task_id=created_entities["task_id"])
        print(f"Rollback: {result}")
    if created_entities["tool_id"]:
        print(f"Deleting tool {created_entities['tool_id']}...")
        result = manager.delete_tool(project_id=project_id, tool_id=created_entities["tool_id"])
        print(f"Rollback: {result}")
    if created_entities["agent_id"]:
        print(f"Deleting agent {created_entities['agent_id']}...")
        result = manager.delete_agent(project_id=project_id, agent_id=created_entities["agent_id"])
        print(f"Rollback: {result}")
    print("Rollback complete.")


def main():
    # Agent Flow
    print("=== Agent Flow ===")
    print("Creating agent 'AgenticAnalyzer' as draft...")
    agent = Agent(
        name="AgenticAnalyzer",
        access_scope="private",
        public_name="analyzer_public",
        job_description="Performs detailed data analysis",
        avatar_image="https://example.com/avatar.png",
        description="A comprehensive agent for data analysis workflows",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Analyze the input data and generate a detailed report.",
                inputs=["data", "format"],
                outputs=[
                    PromptOutput(key="report", description="Detailed analysis report"),
                    PromptOutput(key="summary", description="Concise summary of findings")
                ],
                examples=[
                    PromptExample(
                        input_data="Raw data: 1,2,3; Format: CSV",
                        output='{"report": "Mean: 2, Median: 2", "summary": "Average value is 2"}'
                    )
                ]
            ),
            llm_config=LlmConfig(
                max_tokens=2000,
                timeout=60,
                sampling=Sampling(temperature=0.8, top_k=50, top_p=0.95)
            ),
            models=ModelList(models=[
                Model(name="gpt-4-turbo"),
                Model(name="claude-3-opus")
            ])
        ),
        # id="custom-agent-id-123", # Cannot be manually defined in creation
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_agent_result = manager.create_agent(project_id=project_id, agent=agent, automatic_publish=False)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created Agent: {create_agent_result.name}, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print("Error: Agent creation failed:", create_agent_result)
        rollback()
        exit()

    # Replace agent with created agent
    agent = create_agent_result

    print("Updating agent with additional details...")
    agent.description = "Enhanced agent for multi-format data analysis"
    agent.job_description = "Analyzes data across multiple formats and provides insights"

    update_agent_result = manager.update_agent(project_id=project_id, agent=agent, automatic_publish=False)
    if isinstance(update_agent_result, Agent):
        print(f"Success: Updated Agent: {update_agent_result.description}")
    else:
        print("Error: Agent update failed:", update_agent_result)
        rollback()
        exit()

    print("Publishing agent revision '1'...")
    publish_agent_result = manager.publish_agent_revision(project_id=project_id, agent_id=created_entities["agent_id"], revision="1")
    if isinstance(publish_agent_result, Agent):
        print(f"Success: Published Agent Revision: {publish_agent_result.name}")
    else:
        print("Error: Agent publish failed:", publish_agent_result)
        rollback()
        exit()

    print("Retrieving latest agent version...")
    latest_agent = manager.get_agent(project_id=project_id, agent_id=created_entities["agent_id"])
    if isinstance(latest_agent, Agent):
        print(f"Success: Latest Agent: {latest_agent.name}, Description: {latest_agent.description}")
    else:
        print("Error: Agent retrieval failed:", latest_agent.errors)
        rollback()
        exit()

    # Tool Flow
    print("\n=== Tool Flow ===")
    print("Creating tool 'DataProcessor' as draft...")
    tool = Tool(
        name="DataProcessor",
        description="Processes input data for analysis",
        scope="api",
        parameters=[
            ToolParameter(
                key="input_data",
                data_type="String",
                description="Raw data to process",
                is_required=True,
                type="config",
                from_secret=False,
                value=None
            ),
            ToolParameter(
                key="output_format",
                data_type="String",
                description="Desired output format",
                is_required=False,
                type="context",
                from_secret=False,
                value="json"
            )
        ],
        access_scope="public",
        public_name="data_processor",
        icon="https://example.com/icon.png",
        open_api="https://api.example.com/openapi.yaml",
        open_api_json={"openapi": "3.0.0", "info": {"title": "Data Processor API"}},
        report_events="All",
        id="custom-tool-id-456",
        is_draft=True,
        messages=[ToolMessage(description="Processing completed", type="success")],
        revision=1,
        status="pending"
    )
    create_tool_result = manager.create_tool(project_id=project_id, tool=tool, automatic_publish=False)
    if isinstance(create_tool_result, Tool):
        print(f"Success: Created Tool: {create_tool_result.name}, ID: {create_tool_result.id}")
        created_entities["tool_id"] = create_tool_result.id
    else:
        print("Error: Tool creation failed:", create_tool_result)
        rollback()
        exit()

    # Replace tool with created_tool
    tool = create_tool_result

    print("Updating tool with enhanced features...")
    tool.description = "Advanced tool for multi-format data processing"
    tool.parameters.append(
        ToolParameter(
            key="secret_key",
            data_type="String",
            description="API key for external service",
            is_required=False,
            type="config",
            from_secret=True,
            value="xyz789"
        )
    )
    update_tool_result = manager.update_tool(project_id=project_id, tool=tool, automatic_publish=False)
    if isinstance(update_tool_result, Tool):
        print(f"Success: Updated Tool: {update_tool_result.description}")
    else:
        print("Error: Tool update failed:", update_tool_result)
        rollback()
        exit()

    print("Publishing tool revision '1'...")
    publish_tool_result = manager.publish_tool_revision(project_id=project_id, tool_id=created_entities["tool_id"], revision="1")
    if isinstance(publish_tool_result, Tool):
        print(f"Success: Published Tool Revision: {publish_tool_result.name}")
    else:
        print("Error: Tool publish failed:", publish_tool_result)
        rollback()
        exit()

    print("Retrieving latest tool version...")
    latest_tool = manager.get_tool(project_id=project_id, tool_id=created_entities["tool_id"])
    if isinstance(latest_tool, Tool):
        print(f"Success: Latest Tool: {latest_tool.name}, Description: {latest_tool.description}")
    else:
        print("Error: Tool retrieval failed:", latest_tool.errors)
        rollback()
        exit()

    # Task Flow
    print("\n=== Task Flow ===")
    print("Creating task 'DataAnalysisTask' as draft...")
    task = Task(
        name="DataAnalysisTask",
        description="Analyzes data using specified tools and agents",
        title_template="Analysis Task #{{instance_id}}",
        id="d9e5b1c3-7f2a-4a6d-8b9c-a3d5f1e7c2b6",
        prompt_data={
           "instructions": "Process the input data and generate a report.",
           "inputs": ["data"],
           "outputs": [{"key": "report", "description": "Analysis report"}],
           "examples": [{"inputData": "data: 1,2,3", "output": '{"report": "Mean: 2"}'}]
        },
        artifact_types=[
           {
               "name": "input_data",
               "description": "Raw data file",
               "isRequired": False,
               "usageType": "input",
               "artifactVariableKey": "input_raw"
           },
           {
               "name": "report",
               "description": "Generated analysis report",
               "isRequired": False,
               "usageType": "output",
               "artifactVariableKey": "report_out"
           }
        ],
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_task_result = manager.create_task(project_id=project_id, task=task, automatic_publish=False)
    if isinstance(create_task_result, Task):
        print(f"Success: Created Task: {create_task_result.name}, ID: {create_task_result.id}")
        created_entities["task_id"] = create_task_result.id
    else:
        print("Error: Task creation failed:", create_task_result)
        rollback()
        exit()

    # Assign created task to task for updates
    task = create_task_result

    print("Updating task with additional details...")
    task.description = "Enhanced task for comprehensive data analysis"
    task.prompt_data.instructions = "Process data and include statistical summary."
    # task.artifact_types.append(
    #    {
    #        "name": "summary",
    #        "description": "Summary statistics UPDATED",
    #        "isRequired": False,
    #        "usageType": "output",
    #        "artifactVariableKey": "summary_stats"
    #    }
    # )

    update_task_result = manager.update_task(project_id=project_id, task=task, automatic_publish=False)
    if isinstance(update_task_result, Task):
        print(f"Success: Updated Task: {update_task_result.description}")
    else:
        print("Error: Task update failed:", update_task_result)
        rollback()
        exit()

    print("Publishing task revision '1'...")
    publish_task_result = manager.publish_task_revision(project_id=project_id, task_id=created_entities["task_id"], revision="1")
    if isinstance(publish_task_result, Task):
        print(f"Success: Published Task Revision: {publish_task_result.name}")
    else:
        print("Error: Task publish failed:", publish_task_result)
        rollback()
        exit()

    print("Retrieving latest task version...")
    latest_task = manager.get_task(project_id=project_id, task_id=created_entities["task_id"])
    if isinstance(latest_task, Task):
        print(f"Success: Latest Task: {latest_task.name}, Description: {latest_task.description}")
    else:
        print("Error: Task retrieval failed:", latest_task.errors)
        rollback()
        exit()

    # Process Flow
    print("\n=== Process Flow ===")
    print("Creating process 'DataAnalysisTestProcess' as draft...")
    variables = VariableList(variables=[
        Variable(
            key="input_data",
            value="1,2,3,4,5",
            id="c5a1e9d3-7f2b-4e8d-6b9c-f3d5e1a2c7b4",
            is_draft=True,
            revision=1,
            status="pending"
        ),
        Variable(
            key="format",
            value="json",
            id="7e3d9f2b-1c5a-4e6d-8b9c-a2f5e1d7c3a6",
            is_draft=True,
            revision=1,
            status="pending"
        )
    ])
    process = AgenticProcess(
        key="data_analysis_process",
        name="DataAnalysisTestProcess",
        description="A process for end-to-end data analysis",
        kb=KnowledgeBase(
            name="analysis-kb-3",
            artifact_type_name=["input_data", "report"],
            id="3f8e9d2a-5b7c-4e1a-9c3d-6f2b8e4a1d9c",
            is_draft=True,
            revision=1,
            status="pending"
        ),
        agentic_activities=[
            AgenticActivity(
                key="act1",
                name="Data Processing",
                task_name="DataAnalysisTask",
                agent_name="AgenticAnalyzer",
                agent_revision_id=1,
                id="a7b4c9e1-2d5f-4b8e-9a3c-1e6d7f5b2c8a",
                is_draft=True,
                revision=1,
                status="pending"
            )
        ],
        artifact_signals=[
            ArtifactSignal(
                key="data_input",
                name="Data Input",
                handling_type="C",
                artifact_type_name=["input_data"],
                id="e2d9f6b3-8c1a-4e7d-9b5f-3a2c6e8d1f4b",
                is_draft=True,
                revision=1,
                status="pending"
            )
        ],
        user_signals=[
            UserSignal(
                key="review_complete",
                name="Review Complete",
                id="5c1a7e9d-3f2b-4d6e-8b9c-a4e5d1f7c2b3",
                is_draft=True,
                revision=1,
                status="pending"
            )
        ],
        start_event=Event(
            key="start_event",
            name="Process Start",
            id="9b3e2d6f-1a5c-4e8b-7c9d-f2a3e6b5d1c8",
            is_draft=True,
            revision=1,
            status="pending"
        ),
        end_event=Event(
            key="end_event",
            name="Process End",
            id="d4f7c1e9-6b2a-4e5d-8a3c-b9e1f5d2c7a3",
            is_draft=True,
            revision=1,
            status="pending"
        ),
        sequence_flows=[
            SequenceFlow(key="flow1", source_key="start_event", target_key="data_input", id="2a9c5e1d-7f3b-4d6e-8b2c-e5a1d9f7c3b6"),
            SequenceFlow(key="flow2", source_key="data_input", target_key="act1", id="6e3d9f2b-1c5a-4e7d-8a9c-b2f5e1d6c3a7"),
            SequenceFlow(key="flow3", source_key="act1", target_key="review_complete", id="b5a2c7e9-3d1f-4e6b-9c8d-a7f2e5d1c3b9"),
            SequenceFlow(key="flow4", source_key="review_complete", target_key="end_event", id="f1c6e9d3-5b2a-4e7d-8a3c-d9e5f2b1c6a7")
        ],
        id="8c4f2e9d-1b7a-4d5e-9a3c-6f2e8d1b5c7a",
        is_draft=True,
        revision=1,
        status="pending",
        # variables=variables
    )
    create_process_result = manager.create_process(project_id=project_id, process=process, automatic_publish=False)
    if isinstance(create_process_result, AgenticProcess):
        print(f"Success: Created Process: {create_process_result.name}, ID: {create_process_result.id}")
        created_entities["process_id"] = create_process_result.id
    else:
        print("Error: Process creation failed:", create_process_result)
        rollback()
        exit()

    process = create_process_result

    print("Updating process with refined description...")
    process.description = "Optimized process for scalable data analysis"
    process.agentic_activities[0].name = "Enhanced Data Processing"
    update_process_result = manager.update_process(project_id=project_id, process=process, automatic_publish=False)
    if isinstance(update_process_result, AgenticProcess):
        print(f"Success: Updated Process: {update_process_result.description}")
    else:
        print("Error: Process update failed:", update_process_result)
        rollback()
        exit()

    print("Publishing process revision '1'...")
    publish_process_result = manager.publish_process_revision(project_id=project_id, process_id=created_entities["process_id"], revision="1")
    if isinstance(publish_process_result, AgenticProcess):
        print(f"Success: Published Process Revision: {publish_process_result.name}")
    else:
        print("Error: Process publish failed:", publish_process_result)
        rollback()
        exit()

    print("Retrieving latest process version...")
    latest_process = manager.get_process(project_id=project_id, process_id=created_entities["process_id"])
    if isinstance(latest_process, AgenticProcess):
        print(f"Success: Latest Process: {latest_process.name}, Description: {latest_process.description}")
    else:
        print("Error: Process retrieval failed:", latest_process.errors)
        rollback()
        exit()

    # Process Instance Flow
    print("\n=== Process Instance Flow ===")
    print("Starting process instance for 'DataAnalysisTestProcess'...")
    instance_result = manager.start_instance(
        project_id=project_id,
        process_name="DataAnalysisTestProcess",
        subject="Comprehensive Data Analysis",
        # variables=variables
    )
    if isinstance(instance_result, ProcessInstance):
        print(f"Success: Started Instance: Process: {instance_result.process.name}, ID: {instance_result.id}")
        created_entities["instance_id"] = instance_result.id
    else:
        print("Error: Instance start failed:", instance_result)
        rollback()
        exit()

    print("Retrieving instance information...")
    instance_info = manager.get_instance(project_id=project_id, instance_id=created_entities["instance_id"])
    if isinstance(instance_info, ProcessInstance):
        print(f"Success: Instance Info: Process: {instance_info.process.name}, Subject: {instance_info.subject}")
    else:
        print("Error: Instance retrieval failed:", instance_info.errors)
        rollback()
        exit()

    print("Retrieving instance history...")
    history = manager.get_instance_history(project_id=project_id, instance_id=created_entities["instance_id"])
    if isinstance(history, dict):
        print(f"Success: Instance History: {history}")
    else:
        print("Error: History retrieval failed:", history.errors)
        rollback()
        exit()

    print("\n=== Process Completed Successfully ===")


if __name__ == "__main__":
    try:
        main()

        rollback()  # Delete everything to run again
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")