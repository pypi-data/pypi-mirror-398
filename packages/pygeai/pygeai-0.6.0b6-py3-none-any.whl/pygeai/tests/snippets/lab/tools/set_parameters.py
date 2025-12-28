from pygeai.core.base.responses import ErrorListResponse
from pygeai.lab.managers import AILabManager
from pygeai.lab.models import ToolParameter, Tool

manager = AILabManager()

parameters = [
    ToolParameter(
        key="input",
        data_type="String",
        description="some input that the tool needs.",
        is_required=True
    ),
    ToolParameter(
        key="api_token",
        data_type="String",
        description="Updated API token",
        is_required=True,
        type="config",
        from_secret=True,
        value="new-token-value"
    )
]

result = manager.set_parameter(
    tool_id="affd8ede-97c6-4083-b1f6-2b463ad4891e",
    parameters=parameters
)


print(f"Updated tool: {result.name}, ID: {result.id}")
for param in result.parameters:
    print(f"Parameter: {param.key}, Value: {param.value}")
