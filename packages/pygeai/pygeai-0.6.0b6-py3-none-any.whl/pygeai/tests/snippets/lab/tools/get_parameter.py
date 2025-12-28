from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings

manager = AILabManager()

filter_settings = FilterSettings(
    revision="1",
    version="0",
    allow_drafts=True
)

result = manager.get_parameter(
    tool_id="affd8ede-97c6-4083-b1f6-2b463ad4891e",
    filter_settings=filter_settings
)


print(f"Retrieved {len(result)} parameters:")
for param in result:
    print(f"Key: {param.key}, Type: {param.data_type}, Required: {param.is_required}")

