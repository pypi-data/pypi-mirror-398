from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, Tool

manager = AILabManager()

filter_settings = FilterSettings(
    revision="0",
    version="0",
    allow_drafts=True
)


result = manager.get_tool(
    tool_id="affd8ede-97c6-4083-b1f6-2b463ad4891e",
    filter_settings=filter_settings
)


print(f"Retrieved tool: {result.name}, ID: {result.id}")
print(f"Description: {result.description}")
print(f"Messages: {result.messages}")

