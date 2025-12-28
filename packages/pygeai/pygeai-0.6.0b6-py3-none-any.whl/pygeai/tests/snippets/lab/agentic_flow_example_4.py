from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList,
    Tool, ToolParameter, ToolMessage, ResourcePool, ResourcePoolTool, ResourcePoolList,
    Task, AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow,
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
        result = manager.abort_instance(instance_id=created_entities["instance_id"])
        print(f"Rollback: {result}")
    if created_entities["process_id"]:
        print(f"Deleting process {created_entities['process_id']}...")
        result = manager.delete_process(process_id=created_entities["process_id"])
        print(f"Rollback: {result}")
    if created_entities["task_id"]:
        print(f"Deleting task {created_entities['task_id']}...")
        result = manager.delete_task(task_id=created_entities["task_id"])
        print(f"Rollback: {result}")
    if created_entities["tool_id"]:
        print(f"Deleting tool {created_entities['tool_id']}...")
        result = manager.delete_tool(tool_id=created_entities["tool_id"])
        print(f"Rollback: {result}")
    if created_entities["agent_id"]:
        print(f"Deleting agent {created_entities['agent_id']}...")
        result = manager.delete_agent(agent_id=created_entities["agent_id"])
        print(f"Rollback: {result}")
    print("Rollback complete.")


def main():
    # Tool Flow
    print("\n=== Tool Flow ===")
    print("Creating tool 'TextSummarizer' as draft...")
    tool = Tool(
        name="TextSummarizer",
        description="Summarizes text input into concise outputs",
        scope="api",
        parameters=[
            ToolParameter(
                key="text_input",
                data_type="String",
                description="Text to summarize",
                is_required=True,
                type="app",
                from_secret=False,
                value=None
            ),
            ToolParameter(
                key="summary_length",
                data_type="Integer",
                description="Desired length of summary in words",
                is_required=False,
                type="config",
                from_secret=False,
                value="50"
            )
        ],
        access_scope="public",
        public_name="text_summarizer",
        icon="https://example.com/summarizer_icon.png",
        open_api="https://api.example.com/summarizer/openapi.yaml",
        open_api_json={"openapi": "3.0.0", "info": {"title": "Text Summarizer API"}},
        report_events="Progress",
        is_draft=True,
        messages=[ToolMessage(description="Summary generated successfully", type="success")],
        revision=1,
        status="pending"
    )
    create_tool_result = manager.create_tool(tool=tool, automatic_publish=False)
    if isinstance(create_tool_result, Tool):
        print(f"Success: Created Tool: {create_tool_result.name}, ID: {create_tool_result.id}")
        created_entities["tool_id"] = create_tool_result.id
    else:
        print("Error: Tool creation failed:", create_tool_result)
        rollback()
        exit()

    # Replace tool with created tool
    tool = create_tool_result

    print("Updating tool with enhanced features...")
    tool.description = "Advanced tool for text summarization with customization"
    tool.parameters.append(
        ToolParameter(
            key="language",
            data_type="String",
            description="Language for summarization",
            is_required=False,
            type="context",
            from_secret=False,
            value="English"
        )
    )
    update_tool_result = manager.update_tool(tool=tool, automatic_publish=False)
    if isinstance(update_tool_result, Tool):
        print(f"Success: Updated Tool: {update_tool_result.description}")
    else:
        print("Error: Tool update failed:", update_tool_result)
        rollback()
        exit()

    print("Publishing tool revision '1'...")
    publish_tool_result = manager.publish_tool_revision(tool_id=created_entities["tool_id"], revision="1")
    if isinstance(publish_tool_result, Tool):
        print(f"Success: Published Tool Revision: {publish_tool_result.name}")
    else:
        print("Error: Tool publish failed:", publish_tool_result)
        rollback()
        exit()

    print("Retrieving latest tool version...")
    latest_tool = manager.get_tool(tool_id=created_entities["tool_id"])
    if isinstance(latest_tool, Tool):
        print(f"Success: Latest Tool: {latest_tool.name}, Description: {latest_tool.description}")
    else:
        print("Error: Tool retrieval failed:", latest_tool.errors)
        rollback()
        exit()

    # Agent Flow
    print("\n=== Agent Flow ===")
    print("Creating agent 'SummaryAgent' as draft...")
    agent = Agent(
        name="SummaryAgent",
        access_scope="private",
        public_name="summary_public",
        job_description="Generates summaries for text inputs",
        avatar_image="https://example.com/summary_avatar.png",
        description="An agent for summarizing text efficiently",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Summarize the provided text into a concise output based on user preferences.",
                inputs=["text", "length"],
                outputs=[
                    PromptOutput(key="summary", description="Concise text summary"),
                    PromptOutput(key="key_points", description="List of key points extracted")
                ],
                examples=[
                    PromptExample(
                        input_data="Text: Long article about AI advancements; Length: 50 words",
                        output='{"summary": "AI is advancing rapidly in automation and learning.", "key_points": ["Automation", "Learning"]}'
                    )
                ]
            ),
            llm_config=LlmConfig(
                max_tokens=1500,
                timeout=30,
                sampling=Sampling(temperature=0.7, top_k=40, top_p=0.9)
            ),
            models=ModelList(models=[
                Model(name="gpt-3.5-turbo"),
                Model(name="mistral-7b")
            ]),
            resource_pools=ResourcePoolList(resource_pools=[
                ResourcePool(
                    name="SummaryTools",
                    tools=[
                        ResourcePoolTool(
                            name="TextSummarizer",
                            revision=1
                        )
                    ],
                    agents=None
                )
            ])
        ),
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_agent_result = manager.create_agent(agent=agent, automatic_publish=False)
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
    agent.description = "Improved agent for text summarization tasks"
    agent.job_description = "Summarizes text and extracts key insights"

    update_agent_result = manager.update_agent(agent=agent, automatic_publish=False)
    if isinstance(update_agent_result, Agent):
        print(f"Success: Updated Agent: {update_agent_result.description}")
    else:
        print("Error: Agent update failed:", update_agent_result)
        rollback()
        exit()

    print("Publishing agent revision '1'...")
    publish_agent_result = manager.publish_agent_revision(agent_id=created_entities["agent_id"], revision="1")
    if isinstance(publish_agent_result, Agent):
        print(f"Success: Published Agent Revision: {publish_agent_result.name}")
    else:
        print("Error: Agent publish failed:", publish_agent_result)
        rollback()
        exit()

    print("Retrieving latest agent version...")
    latest_agent = manager.get_agent(agent_id=created_entities["agent_id"])
    if isinstance(latest_agent, Agent):
        print(f"Success: Latest Agent: {latest_agent.name}, Description: {latest_agent.description}")
    else:
        print("Error: Agent retrieval failed:", latest_agent.errors)
        rollback()
        exit()

    # Task Flow
    print("\n=== Task Flow ===")
    print("Creating task 'SummaryTestTask' as draft...")
    task = Task(
        name="SummaryTestTask",
        description="Generates summaries for text inputs using agents and tools",
        title_template="Summary Task #{{instance_id}}",
        prompt_data=Prompt(
            instructions="Summarize the input text and extract key points.",
            inputs=["text"],
            outputs=[PromptOutput(key="summary", description="Generated summary")],
            examples=[PromptExample(input_data="Text: AI article", output='{"summary": "AI advances discussed"}')]
        ),
        artifact_types=[
            {
                "name": "text_input",
                "description": "Input text file",
                "isRequired": True,
                "usageType": "input",
                "artifactVariableKey": "text_in"
            },
            {
                "name": "summary_output",
                "description": "Generated summary file",
                "isRequired": False,
                "usageType": "output",
                "artifactVariableKey": "summary_out"
            }
        ],
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_task_result = manager.create_task(task=task, automatic_publish=False)
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
    task.description = "Enhanced task for text summarization and analysis"
    task.prompt_data.instructions = "Summarize text and highlight key insights."

    update_task_result = manager.update_task(task=task, automatic_publish=False)
    if isinstance(update_task_result, Task):
        print(f"Success: Updated Task: {update_task_result.description}")
    else:
        print("Error: Task update failed:", update_task_result)
        rollback()
        exit()

    print("Publishing task revision '1'...")
    publish_task_result = manager.publish_task_revision(task_id=created_entities["task_id"], revision="1")
    if isinstance(publish_task_result, Task):
        print(f"Success: Published Task Revision: {publish_task_result.name}")
    else:
        print("Error: Task publish failed:", publish_task_result)
        rollback()
        exit()

    print("Retrieving latest task version...")
    latest_task = manager.get_task(task_id=created_entities["task_id"])
    if isinstance(latest_task, Task):
        print(f"Success: Latest Task: {latest_task.name}, Description: {latest_task.description}")
    else:
        print("Error: Task retrieval failed:", latest_task.errors)
        rollback()
        exit()

    # Process Flow
    print("\n=== Process Flow ===")
    print("Creating process 'TextSummaryProcess' as draft...")
    variables = VariableList(variables=[
        Variable(key="text_data", value="Article about machine learning trends"),
        Variable(key="summary_length", value="100")
    ])
    process = AgenticProcess(
        key="text_summary_process",
        name="TextSummaryProcess",
        description="A process for summarizing text inputs",
        kb=KnowledgeBase(
            name="summary-kb",
            artifact_type_name=["text_input", "summary_output"]
        ),
        agentic_activities=[
            AgenticActivity(
                key="act1",
                name="Text Summarization",
                task_name="SummaryTestTask",
                agent_name="SummaryAgent",
                agent_revision_id=1
            )
        ],
        artifact_signals=[
            ArtifactSignal(
                key="text_signal",
                name="Text Input Signal",
                handling_type="C",
                artifact_type_name=["text_input"]
            )
        ],
        user_signals=[
            UserSignal(
                key="summary_approved",
                name="Summary Approved"
            )
        ],
        start_event=Event(
            key="start_event",
            name="Process Start"
        ),
        end_event=Event(
            key="end_event",
            name="Process End"
        ),
        sequence_flows=[
            SequenceFlow(key="flow1", source_key="start_event", target_key="text_signal"),
            SequenceFlow(key="flow2", source_key="text_signal", target_key="act1"),
            SequenceFlow(key="flow3", source_key="act1", target_key="summary_approved"),
            SequenceFlow(key="flow4", source_key="summary_approved", target_key="end_event")
        ],
        variables=variables,
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_process_result = manager.create_process(process=process, automatic_publish=False)
    if isinstance(create_process_result, AgenticProcess):
        print(f"Success: Created Process: {create_process_result.name}, ID: {create_process_result.id}")
        created_entities["process_id"] = create_process_result.id
    else:
        print("Error: Process creation failed:", create_process_result)
        rollback()
        exit()

    process = create_process_result

    print("Updating process with refined description...")
    process.description = "Optimized process for text summarization workflows"
    process.agentic_activities[0].name = "Advanced Text Summarization"

    update_process_result = manager.update_process(process=process, automatic_publish=False)
    if isinstance(update_process_result, AgenticProcess):
        print(f"Success: Updated Process: {update_process_result.description}")
    else:
        print("Error: Process update failed:", update_process_result)
        rollback()
        exit()

    print("Publishing process revision '1'...")
    publish_process_result = manager.publish_process_revision(process_id=created_entities["process_id"], revision="1")
    if isinstance(publish_process_result, AgenticProcess):
        print(f"Success: Published Process Revision: {publish_process_result.name}")
    else:
        print("Error: Process publish failed:", publish_process_result)
        rollback()
        exit()

    print("Retrieving latest process version...")
    latest_process = manager.get_process(process_id=created_entities["process_id"])
    if isinstance(latest_process, AgenticProcess):
        print(f"Success: Latest Process: {latest_process.name}, Description: {latest_process.description}")
    else:
        print("Error: Process retrieval failed:", latest_process.errors)
        rollback()
        exit()

    # Process Instance Flow
    print("\n=== Process Instance Flow ===")
    print("Starting process instance for 'TextSummaryProcess'...")
    instance_result = manager.start_instance(
        project_id=project_id,
        process_name="TextSummaryProcess",
        subject="Text Summarization Workflow",
        variables=variables
    )
    if isinstance(instance_result, ProcessInstance):
        print(f"Success: Started Instance: Process: {instance_result.process.name}, ID: {instance_result.id}")
        created_entities["instance_id"] = instance_result.id
    else:
        print("Error: Instance start failed:", instance_result)
        rollback()
        exit()

    print("Retrieving instance information...")
    instance_info = manager.get_instance(instance_id=created_entities["instance_id"])
    if isinstance(instance_info, ProcessInstance):
        print(f"Success: Instance Info: Process: {instance_info.process.name}, Subject: {instance_info.subject}")
    else:
        print("Error: Instance retrieval failed:", instance_info.errors)
        rollback()
        exit()

    print("Retrieving instance history...")
    history = manager.get_instance_history(instance_id=created_entities["instance_id"])
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