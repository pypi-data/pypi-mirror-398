from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings

manager = AILabManager()

filter_settings = FilterSettings(
    id="",
    count="100",
    access_scope="public",
    allow_drafts=True,
    scope="builtin",
    allow_external=True
)


result = manager.list_tools(
    filter_settings=filter_settings
)

print(f"Found {len(result)} tools:")
for tool in result:
    print(f"Tool: {tool.name}, ID: {tool.id}, Scope: {tool.scope}")

