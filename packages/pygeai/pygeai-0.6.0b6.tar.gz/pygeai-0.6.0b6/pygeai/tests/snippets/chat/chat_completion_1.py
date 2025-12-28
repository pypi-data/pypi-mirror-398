from pygeai.chat.managers import ChatManager
from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage, ChatVariable, ChatVariableList

manager = ChatManager()

llm_settings = LlmSettings(
    temperature=0.8,
    max_tokens=2000,
    presence_penalty=0.1
)

messages = ChatMessageList(
    messages=[
        ChatMessage(
            role="system",
            content="You are a helpful assistant for Globant Enterprise AI."
        ),
        ChatMessage(
            role="user",
            content="What AI solutions does Globant offer?"
        )
    ]
)

variables = ChatVariableList(
    variables=[
        ChatVariable(key="user_region", value="North America"),
        ChatVariable(key="industry", value="Technology")
    ]
)

response = manager.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    llm_settings=llm_settings,
    thread_id="thread_123e4567-e89b-12d3-a456-426614174000",
    variables=variables
)

print(response)