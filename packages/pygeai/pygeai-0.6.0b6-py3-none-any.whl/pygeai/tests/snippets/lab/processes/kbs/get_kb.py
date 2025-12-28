from pygeai.lab.managers import AILabManager
from pygeai.lab.models import KnowledgeBase

manager = AILabManager()

kb_id = "c6af1295-3ea6-4823-8ae4-730337b278c6"
result = manager.get_knowledge_base(
    kb_id=kb_id
)


print(f"Retrieved knowledge base: {result.name}, ID: {result.id}")
print(f"Artifacts: {result.artifacts}")
print(f"Metadata: {result.metadata}")
print(f"Artifact Types: {result.artifact_type_name}")

kb_name = "sample-kb"
result = manager.get_knowledge_base(
    kb_name=kb_name
)


print(f"Retrieved knowledge base: {result.name}, ID: {result.id}")
print(f"Artifacts: {result.artifacts}")
print(f"Metadata: {result.metadata}")
print(f"Artifact Types: {result.artifact_type_name}")
