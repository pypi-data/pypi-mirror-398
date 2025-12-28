from pygeai.core.base.responses import EmptyResponse
from pygeai.lab.managers import AILabManager

manager = AILabManager(api_key="your-api-key")


result = manager.delete_tool(
    tool_id="affd8ede-97c6-4083-b1f6-2b463ad4891e"
)

if isinstance(result, EmptyResponse):
    print("Tool deleted successfully")
else:
    print("Errors:", result.errors)

result = manager.delete_tool(
    tool_name="sample tool V5"
)

print("Tool deleted successfully")

