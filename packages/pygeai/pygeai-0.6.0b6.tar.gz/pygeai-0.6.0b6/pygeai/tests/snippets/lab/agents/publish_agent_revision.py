from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Agent

manager = AILabManager()

result = manager.publish_agent_revision(
    agent_id="9716a0a1-5eab-4cc9-a611-fa2c3237c511",
    revision="6"
)

print(f"Published agent: {result.name}, ID: {result.id}")
print(f"Revision: {result.revision}, Draft: {result.is_draft}")
