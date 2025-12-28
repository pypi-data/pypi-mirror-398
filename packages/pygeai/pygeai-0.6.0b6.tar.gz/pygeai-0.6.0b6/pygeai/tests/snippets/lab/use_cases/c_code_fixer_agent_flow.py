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
    # Agent Creation
    print("=== Creating CodeFixerAgent ===")
    code_fixer_agent = Agent(
        name="CodeFixerAgent",
        access_scope="private",
        job_description="Diagnoses and fixes errors in C/C++ code",
        description="An agent for analyzing and repairing C/C++ code errors",
        agent_data=AgentData(
            prompt=Prompt(
                instructions="Analyze the provided C/C++ code, identify syntax, semantic, or runtime errors, and suggest fixes. Return the corrected code and an explanation.",
                inputs=["code_snippet", "error_log"],
                outputs=[
                    PromptOutput(key="fixed_code", description="Corrected C/C++ code"),
                    PromptOutput(key="explanation", description="Explanation of errors and fixes")
                ],
                examples=[
                    PromptExample(
                        input_data="Code: int main() { printf('Hello); return 0; }; Error: syntax error near ')'",
                        output='{"fixed_code": "int main() { printf(\\"Hello\\"); return 0; }", "explanation": "Missing closing quote and semicolon in printf call."}'
                    )
                ]
            ),
            llm_config=LlmConfig(
                max_tokens=3000,
                timeout=120,
                sampling=Sampling(temperature=0.7, top_k=40, top_p=0.9)
            ),
            models=ModelList(models=[Model(name="gpt-4-turbo")])
        ),
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_agent_result = manager.create_agent(project_id=project_id, agent=code_fixer_agent, automatic_publish=False)
    if isinstance(create_agent_result, Agent):
        print(f"Success: Created CodeFixerAgent, ID: {create_agent_result.id}")
        created_entities["agent_id"] = create_agent_result.id
    else:
        print(f"Error: Agent creation failed: {create_agent_result}")
        rollback()
        exit()

    # Tool Creation
    print("\n=== Creating CodeCompilerTool ===")
    compiler_tool = Tool(
        name="CodeCompilerTool",
        description="Compiles C/C++ code and returns errors",
        scope="api",
        parameters=[
            ToolParameter(
                key="source_code",
                data_type="String",
                description="C/C++ code to compile",
                is_required=True,
                type="app"
            )
        ],
        access_scope="private",
        open_api_json={"openapi": "3.0.0", "info": {"title": "Compiler API"}},
        report_events="All",
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_tool_result = manager.create_tool(project_id=project_id, tool=compiler_tool, automatic_publish=False)
    if isinstance(create_tool_result, Tool):
        print(f"Success: Created CodeCompilerTool, ID: {create_tool_result.id}")
        created_entities["tool_id"] = create_tool_result.id
    else:
        print(f"Error: Tool creation failed: {create_tool_result}")
        rollback()
        exit()

    # Task Creation
    print("\n=== Creating FixCodeTask ===")
    fix_code_task = Task(
        name="FixCodeTask",
        description="Task to fix errors in C/C++ code",
        prompt_data=Prompt(
            instructions="Use the compiler tool to identify errors in the C/C++ code, then fix them and provide an explanation.",
            inputs=["code_snippet"],
            outputs=[
                PromptOutput(key="fixed_code", description="Corrected code"),
                PromptOutput(key="explanation", description="Error details and fixes")
            ]
        ),
        artifact_types=[
            {"name": "source_code", "description": "Input C/C++ code", "isRequired": True, "usageType": "input",
             "artifactVariableKey": "src"},
            {"name": "fixed_code", "description": "Corrected C/C++ code", "isRequired": False, "usageType": "output",
             "artifactVariableKey": "fixed"}
        ],
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_task_result = manager.create_task(project_id=project_id, task=fix_code_task, automatic_publish=False)
    if isinstance(create_task_result, Task):
        print(f"Success: Created FixCodeTask, ID: {create_task_result.id}")
        created_entities["task_id"] = create_task_result.id
    else:
        print(f"Error: Task creation failed: {create_task_result}")
        rollback()
        exit()

    # Process Creation
    print("\n=== Creating CodeFixProcess ===")
    code_fix_process = AgenticProcess(
        name="CodeFixProcess",
        description="End-to-end process to fix C/C++ code errors",
        agentic_activities=[
            AgenticActivity(
                key="fix_code",
                name="Fix Code",
                task_name="FixCodeTask",
                agent_name="CodeFixerAgent",
                agent_revision_id=1
            )
        ],
        artifact_signals=[
            ArtifactSignal(key="code_input", name="Code Input", handling_type="C", artifact_type_name=["source_code"])
        ],
        start_event=Event(key="start", name="Start"),
        end_event=Event(key="end", name="End"),
        sequence_flows=[
            SequenceFlow(key="f1", source_key="start", target_key="code_input"),
            SequenceFlow(key="f2", source_key="code_input", target_key="fix_code"),
            SequenceFlow(key="f3", source_key="fix_code", target_key="end")
        ],
        is_draft=True,
        revision=1,
        status="pending"
    )
    create_process_result = manager.create_process(project_id=project_id, process=code_fix_process, automatic_publish=False)
    if isinstance(create_process_result, AgenticProcess):
        print(f"Success: Created CodeFixProcess, ID: {create_process_result.id}")
        created_entities["process_id"] = create_process_result.id
    else:
        print(f"Error: Process creation failed: {create_process_result}")
        rollback()
        exit()

    # Publish Entities
    for entity, id_key in [("agent", "agent_id"), ("tool", "tool_id"), ("task", "task_id"), ("process", "process_id")]:
        print(f"\nPublishing {entity} revision '1'...")
        publish_method = getattr(manager, f"publish_{entity}_revision")
        result = publish_method(project_id=project_id, **{f"{entity}_id": created_entities[id_key]}, revision="1")
        if isinstance(result, (Agent, Tool, Task, AgenticProcess)):
            print(f"Success: Published {entity.capitalize()} Revision: {result.name}")
        else:
            print(f"Error: {entity.capitalize()} publish failed: {result}")
            rollback()
            exit()

    # Start Instance
    print("\nStarting CodeFixProcess instance...")
    instance_result = manager.start_instance(
        project_id=project_id,
        process_name="CodeFixProcess",
        subject="Fix C++ Syntax Error",
        variables=VariableList(variables=[Variable(key="code_snippet", value="int main() { cout << 'Error; return 0; }")])
    )
    if isinstance(instance_result, ProcessInstance):
        print(f"Success: Started Instance, ID: {instance_result.id}")
        created_entities["instance_id"] = instance_result.id
    else:
        print(f"Error: Instance start failed: {instance_result}")
        rollback()
        exit()

    # Retrieve Instance Info
    print("Retrieving instance information...")
    instance_info = manager.get_instance(project_id=project_id, instance_id=created_entities["instance_id"])
    if isinstance(instance_info, ProcessInstance):
        print(f"Success: Instance Info: Process: {instance_info.process.name}, Subject: {instance_info.subject}")
    else:
        print(f"Error: Instance retrieval failed: {instance_info.errors}")
        rollback()
        exit()

    print("\n=== Workflow Completed Successfully ===")
    rollback()


if __name__ == "__main__":
    try:
        main()

        rollback()  # Delete all for testing purposes
    except Exception as e:
        rollback()
        print(f"\n# Critical error: {e}")