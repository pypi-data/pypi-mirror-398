from pygeai.chat.managers import ChatManager
from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatTool, ChatToolList

manager = ChatManager()

llm_settings = LlmSettings(
    temperature=0.7,
    max_tokens=1000,
    frequency_penalty=0.3,
    presence_penalty=0.2
)

messages = ChatMessageList(
    messages=[
        ChatMessage(
            role="user",
            content="Can you check the weather for New York and send an email summary?"
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
            name="send_email",
            description="Sends an email to a recipient with a subject and body",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Email address"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email content"}
                },
                "required": ["recipient", "subject", "body"]
            },
            strict=False
        )
    ]
)

response = manager.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    llm_settings=llm_settings,
    tools=tools
)

print(response)