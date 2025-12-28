from pygeai.lab.managers import AILabManager
from pygeai.lab.models import FilterSettings, AgenticProcessList

manager = AILabManager()
filter_settings = FilterSettings(id="30a2ab8c-7503-4220-b6a0-77f3ee40d365", start="0", count="100", allow_drafts=True)
result = manager.list_processes(filter_settings=filter_settings)

print(f"Found {len(result.processes)} processes:")
for proc in result.processes:
    print(f"Name: {proc.name}, ID: {proc.id}")
