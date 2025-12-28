from pygeai.lab.managers import AILabManager
from pygeai.lab.models import AgenticProcess, KnowledgeBase, AgenticActivity, ArtifactSignal, UserSignal, Event, SequenceFlow

manager = AILabManager()
process = AgenticProcess(
    key="product_def",
    name="Basic Process V6",
    description="This is a sample process",
    kb=KnowledgeBase(name="basic-sample", artifact_type_name=["sample-artifact"]),
    agentic_activities=[AgenticActivity(key="activityOne", name="First Step", task_name="basic-task", agent_name="sample-translator", agent_revision_id=0)],
    artifact_signals=[ArtifactSignal(key="artifact.upload.1", name="artifact.upload", handling_type="C", artifact_type_name=["sample-artifact"])],
    user_signals=[UserSignal(key="signal_done", name="process-completed")],
    start_event=Event(key="artifact.upload.1", name="artifact.upload"),
    end_event=Event(key="end", name="Done"),
    sequence_flows=[
        SequenceFlow(key="step1", source_key="artifact.upload.1", target_key="activityOne"),
        SequenceFlow(key="step2", source_key="activityOne", target_key="signal_done"),
        SequenceFlow(key="stepEnd", source_key="signal_done", target_key="end")
    ]
)

result = manager.create_process(process=process, automatic_publish=False)

print(f"Created process: {result.name}, ID: {result.id}")
