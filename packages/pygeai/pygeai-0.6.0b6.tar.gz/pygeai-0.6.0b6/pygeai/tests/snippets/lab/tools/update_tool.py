from pygeai.lab.managers import AILabManager
from pygeai.lab.models import Tool, ToolParameter

parameters = [
    ToolParameter(
        key="input",
        data_type="String",
        description="some input that the tool needs. ",
        is_required=True
    ),
    ToolParameter(
        key="some_nonsensitive_id",
        data_type="String",
        description="Configuration that is static, in the sense that whenever the tool is used, the value for this parameter is configured here. The llm will not know about it.",
        is_required=True,
        type="config",
        from_secret=False,
        value="b001e30b4016001f5f76b9ae9215ac40"
    ),
    ToolParameter(
        key="api_token",
        data_type="String",
        description="Configuration that is static, but it is sensitive information . The value is stored in secret-manager",
        is_required=True,
        type="config",
        from_secret=True,
        value="0cd84dc7-f3f5-4a03-9288-cdfd8d72fde1"
    )
]

tool = Tool(
    id="affd8ede-97c6-4083-b1f6-2b463ad4891e",
    name="sample tool V5",
    description="a builtin tool that does something but really does nothing cos it does not exist. UPDATED",
    scope="builtin",
    parameters=parameters
)


manager = AILabManager()


result = manager.update_tool(
    tool=tool,
    automatic_publish=False,
    upsert=False
)


print(f"Updated tool: {result.name}, ID: {result.id}")
print(f"Description: {result.description}")
print(f"Messages: {result.messages}")
