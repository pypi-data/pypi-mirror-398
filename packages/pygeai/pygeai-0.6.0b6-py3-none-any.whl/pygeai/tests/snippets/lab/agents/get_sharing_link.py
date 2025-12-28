from pygeai.lab.managers import AILabManager
from pygeai.lab.models import SharingLink

manager = AILabManager()


result = manager.create_sharing_link(
    agent_id="9716a0a1-5eab-4cc9-a611-fa2c3237c511"
)


print(f"Sharing link created for agent ID: {result.agent_id}")
print(f"Shared Link: {result.shared_link}")
