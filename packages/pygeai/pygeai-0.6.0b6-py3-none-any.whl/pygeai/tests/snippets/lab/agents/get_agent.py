from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, Agent


manager = AILabManager()


result = manager.get_agent(
    agent_id="9716a0a1-5eab-4cc9-a611-fa2c3237c511"
)

print(f"Retrieved agent: {result.to_dict()}")

filter_settings = FilterSettings(
    revision="0",
    version="0",
    allow_drafts=False
)
result = manager.get_agent(
    agent_id="9716a0a1-5eab-4cc9-a611-fa2c3237c511",
    filter_settings=filter_settings
)

print(f"Retrieved agent: {result.to_dict()}")
