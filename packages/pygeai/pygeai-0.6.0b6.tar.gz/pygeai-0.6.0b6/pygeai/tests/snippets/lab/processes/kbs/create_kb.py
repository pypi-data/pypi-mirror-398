from pygeai.lab.managers import AILabManager
from pygeai.lab.models import KnowledgeBase

manager = AILabManager()

knowledge_base = KnowledgeBase(
    name="sample-kb",
    artifact_type_name=["sample-artifact"],
    # artifacts=["artifact-001", "artifact-002"],
    metadata=["issue_id", "priority"]
)

result = manager.create_knowledge_base(
    knowledge_base=knowledge_base
)

print(f"Created knowledge base: {result.name}, ID: {result.id}")

