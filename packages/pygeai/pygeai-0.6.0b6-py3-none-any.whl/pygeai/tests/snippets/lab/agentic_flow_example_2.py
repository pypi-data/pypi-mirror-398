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
    print("Creating agent 'SimpleAnalyzer' as draft...")
    agent = Agent(
        name="SimpleAnalyzer",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Summarize text.",
                inputs=["input"],
                outputs=[PromptOutput(key="result", description="Summary")]
            ),
            llm_config=LlmConfig(
                max_tokens=500,
                timeout=10,
                sampling=Sampling(temperature=0.5, top_k=30, top_p=0.8)
            ),
            models=ModelList(models=[Model(name="gpt-3.5-turbo")])
        )
    )
    create_agent_result = manager.create_agent(project_id=project_id, agent=agent)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created Agent: {create_agent_result.name}, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print("Error: Agent creation failed:", create_agent_result)
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

    # Tool Flow
    print("\n=== Tool Flow ===")
    print("Creating tool 'TextProcessor' as draft...")
    tool = Tool(
        name="TextProcessor",
        description="Processes text input"
    )
    create_tool_result = manager.create_tool(project_id=project_id, tool=tool)
    if isinstance(create_tool_result, Tool):
        print(f"Success: Created Tool: {create_tool_result.name}, ID: {create_tool_result.id}")
        created_entities["tool_id"] = create_tool_result.id
    else:
        print("Error: Tool creation failed:", create_tool_result)
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

    # Task Flow
    print("\n=== Task Flow ===")
    print("Creating task 'SummaryTask' as draft...")
    task = Task(
        name="SummaryTask"
    )
    create_task_result = manager.create_task(project_id=project_id, task=task)
    if isinstance(create_task_result, Task):
        print(f"Success: Created Task: {create_task_result.name}, ID: {create_task_result.id}")
        created_entities["task_id"] = create_task_result.id
    else:
        print("Error: Task creation failed:", create_task_result)
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

    # Process Flow
    print("\n=== Process Flow ===")
    print("Creating process 'TextSummaryProcess' as draft...")
    process = AgenticProcess(
        name="TextSummaryProcess",
        kb=KnowledgeBase(name="summary-kb", artifact_type_name=["text"]),
        agentic_activities=[
            AgenticActivity(
                key="act1",
                name="Summarize",
                task_name="SummaryTask",
                agent_name="SimpleAnalyzer",
                agent_revision_id=1
            )
        ],
        artifact_signals=[
            ArtifactSignal(key="text_in", name="Text Input", handling_type="C", artifact_type_name=["text"])
        ],
        user_signals=[
            UserSignal(key="done", name="Done")
        ],
        start_event=Event(key="start", name="Start"),
        end_event=Event(key="end", name="End"),
        sequence_flows=[
            SequenceFlow(key="f1", source_key="start", target_key="text_in"),
            SequenceFlow(key="f2", source_key="text_in", target_key="act1"),
            SequenceFlow(key="f3", source_key="act1", target_key="done"),
            SequenceFlow(key="f4", source_key="done", target_key="end")
        ]
    )
    create_process_result = manager.create_process(project_id=project_id, process=process)
    if isinstance(create_process_result, AgenticProcess):
        print(f"Success: Created Process: {create_process_result.name}, ID: {create_process_result.id}")
        created_entities["process_id"] = create_process_result.id
    else:
        print("Error: Process creation failed:", create_process_result)
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

    # Process Instance Flow
    print("\n=== Process Instance Flow ===")
    print("Starting process instance for 'TextSummaryProcess'...")
    instance_result = manager.start_instance(
        project_id=project_id,
        process_name="TextSummaryProcess",
        subject="Text Summary Request",
    )
    if isinstance(instance_result, ProcessInstance):
        print(f"Success: Started Instance: Process: {instance_result.process.name}, ID: {instance_result.id}")
        created_entities["instance_id"] = instance_result.id
    else:
        print("Error: Instance start failed:", instance_result)
        rollback()
        exit()

    print("\n=== Process Completed Successfully ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")