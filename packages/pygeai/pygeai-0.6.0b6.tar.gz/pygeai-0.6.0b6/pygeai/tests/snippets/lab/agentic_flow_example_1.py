
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import (
    Agent, AgentData, Prompt, PromptExample, PromptOutput, LlmConfig, Sampling, Model, ModelList,
    Tool, ToolParameter,
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
    # Agent Flow
    print("=== Agent Flow ===")
    print("Creating agent 'AgenticTester' as draft...")
    agent = Agent(
        name="AgenticTester",
        access_scope="public",
        public_name="agentic_tester",
        job_description="Analyzes data and provides insights",
        description="An agent designed for testing agentic workflows",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Analyze the provided text and summarize it.",
                inputs=["text"],
                outputs=[PromptOutput(key="summary", description="A concise summary of the text")],
                examples=[PromptExample(input_data="The quick brown fox jumps.", output='{"summary": "Fox jumps."}')]
            ),
            llm_config=LlmConfig(
                max_tokens=1000,
                timeout=30,
                sampling=Sampling(temperature=0.7, top_k=40, top_p=0.9)
            ),
            strategy_name="Dynamic Prompting",
            models=ModelList(models=[
                Model(name="gpt-4"),
                Model(name="gpt-3.5-turbo")
            ])
        )
    )
    create_agent_result = manager.create_agent(agent=agent, automatic_publish=False)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created Agent: {create_agent_result.name}, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print("Error: Agent creation failed:", create_agent_result)
        rollback()
        exit()

    print("Updating agent description...")
    agent.description = "Updated agent for testing workflows with enhanced capabilities"
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

    # Tool Flow
    print("\n=== Tool Flow ===")
    print("Creating tool 'TestyTool' as draft...")
    tool = Tool(
        name="TestyTool",
        description="A tool for processing text data",
        parameters=[
            ToolParameter(key="input_text", data_type="String", description="Text to process", is_required=True),
            ToolParameter(key="max_length", data_type="Integer", description="Maximum length of output", is_required=False, value="100")
        ]
    )
    create_tool_result = manager.create_tool(tool=tool, automatic_publish=False)
    if isinstance(create_tool_result, Tool):
        print(f"Success: Created Tool: {create_tool_result.name}, ID: {create_tool_result.id}")
        created_entities["tool_id"] = create_tool_result.id
    else:
        print("Error: Tool creation failed:", create_tool_result)
        rollback()
        exit()

    print("Updating tool description...")
    tool.description = "Updated tool for enhanced text processing"
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

    # Task Flow
    print("\n=== Task Flow ===")
    print("Creating task 'TestyTask' as draft...")
    task = Task(
        name="TestyTask",
        description="Processes text data using an agent",
        title_template="Text Processing Task #{{id}}"
    )
    create_task_result = manager.create_task(task=task, automatic_publish=False)
    if isinstance(create_task_result, Task):
        print(f"Success: Created Task: {create_task_result.name}, ID: {create_task_result.id}")
        created_entities["task_id"] = create_task_result.id
    else:
        print("Error: Task creation failed:", create_task_result)
        rollback()
        exit()

    # Assign created task to task
    task = create_task_result

    print("Updating task description...")
    task.description = "Updated task for text processing with agent collaboration"
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
    print("Creating process 'TestyProcess' as draft...")
    process = AgenticProcess(
        key="testy_process",
        name="TestyProcess",
        description="A process to analyze text data",
        kb=KnowledgeBase(name="text-analysis-kb", artifact_type_name=["text-data"]),
        agentic_activities=[
            AgenticActivity(
                key="activity1",
                name="Analyze Text",
                task_name="TestyTask",
                agent_name="AgenticTester",
                agent_revision_id=1
            )
        ],
        artifact_signals=[
            ArtifactSignal(key="text_upload", name="Text Upload", handling_type="C", artifact_type_name=["text-data"])
        ],
        user_signals=[
            UserSignal(key="analysis_complete", name="Analysis Complete")
        ],
        start_event=Event(key="start", name="Start"),
        end_event=Event(key="end", name="End"),
        sequence_flows=[
            SequenceFlow(key="flow1", source_key="start", target_key="text_upload"),
            SequenceFlow(key="flow2", source_key="text_upload", target_key="activity1"),
            SequenceFlow(key="flow3", source_key="activity1", target_key="analysis_complete"),
            SequenceFlow(key="flow4", source_key="analysis_complete", target_key="end")
        ]
    )
    create_process_result = manager.create_process(process=process, automatic_publish=False)
    if isinstance(create_process_result, AgenticProcess):
        print(f"Success: Created Process: {create_process_result.name}, ID: {create_process_result.id}")
        created_entities["process_id"] = create_process_result.id
    else:
        print("Error: Process creation failed:", create_process_result)
        rollback()
        exit()

    print("Updating process description...")
    process.description = "Updated process for advanced text analysis"
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
    print("Starting process instance for 'TestyProcess'...")
    # variables = VariableList(variables=[Variable(key="input_text", value="Sample text for analysis")])
    # variables = [Variable(key="input_text", value="Sample text for analysis")]
    variables = []
    instance_result = manager.start_instance(
        project_id=project_id,
        process_name="TestyProcess",
        subject="Text Analysis Request",
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
    except Exception as e:
        breakpoint()
        rollback()
        print(f"\n# Critical error: {e}")