from pygeai.core.base.responses import EmptyResponse
from pygeai.lab.managers import AILabManager

manager = AILabManager()

agent_id = "3c06e604-26a9-485c-b84e-8eba3ff9a218"

result = manager.delete_agent(
    agent_id=agent_id
)

print(f"Agent deleted successfully")
