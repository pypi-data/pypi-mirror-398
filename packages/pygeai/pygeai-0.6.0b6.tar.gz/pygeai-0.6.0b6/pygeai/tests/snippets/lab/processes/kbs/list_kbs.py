from pygeai.lab.managers import AILabManager
from pygeai.lab.models import KnowledgeBaseList

manager = AILabManager()

result = manager.list_knowledge_bases(
    start=0,
    count=10
)

print(f"Retrieved {len(result.knowledge_bases)} knowledge bases:")
for kb in result.knowledge_bases:
    print(f"- Name: {kb.name}, ID: {kb.id}")
    print(f"  Artifacts: {kb.artifacts}")
    print(f"  Metadata: {kb.metadata}")
    print(f"  Artifact Types: {kb.artifact_type_name}")

result = manager.list_knowledge_bases(
    name="sample-kb",
    start=0,
    count=5
)


print(f"Retrieved {len(result.knowledge_bases)} knowledge bases with name 'sample-kb':")
for kb in result.knowledge_bases:
    print(f"- Name: {kb.name}, ID: {kb.id}")
    print(f"  Artifacts: {kb.artifacts}")
    print(f"  Metadata: {kb.metadata}")
    print(f"  Artifact Types: {kb.artifact_type_name}")
