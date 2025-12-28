from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool

manager = AILabManager()

result = manager.publish_tool_revision(
    tool_id="affd8ede-97c6-4083-b1f6-2b463ad4891e",
    revision="1"
)


print(f"Published tool: {result.name}, ID: {result.id}, Revision: {result.revision}")

