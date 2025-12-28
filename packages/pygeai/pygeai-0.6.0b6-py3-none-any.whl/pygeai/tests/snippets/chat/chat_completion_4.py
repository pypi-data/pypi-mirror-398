from pygeai.chat.managers import ChatManager
from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList, ToolChoice, ToolChoiceObject, ToolChoiceFunction

manager = ChatManager()

llm_settings = LlmSettings(
    temperature=0.6,
    max_tokens=800,
    frequency_penalty=0.1,
    presence_penalty=0.2
)

messages = ChatMessageList(
    messages=[
        ChatMessage(
            role="user",
            content="Please get the current weather for San Francisco."
        )
    ]
)

tools = ChatToolList(
    tools=[
        ChatTool(
            name="get_weather",
            description="Fetches the current weather for a given location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            },
            strict=True
        ),
        ChatTool(
            name="send_notification",
            description="Sends a notification with a message",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Notification content"}
                },
                "required": ["message"]
            },
            strict=False
        )
    ]
)

tool_choice = ToolChoice(
    value=ToolChoiceObject(
        function=ToolChoiceFunction(
            name="get_weather"
        )
    )
)

response = manager.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    llm_settings=llm_settings,
    tool_choice=tool_choice,
    tools=tools
)

print(response)