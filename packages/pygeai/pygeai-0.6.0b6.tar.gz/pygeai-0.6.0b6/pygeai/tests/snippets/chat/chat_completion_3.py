from pygeai.chat.managers import ChatManager
from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage

manager = ChatManager()

llm_settings = LlmSettings(
    temperature=0.5,
    max_tokens=500,
    frequency_penalty=0.2
)

messages = ChatMessageList(
    messages=[
        ChatMessage(
            role="user",
            content="Can you explain what Globant Enterprise AI does?"
        )
    ]
)

response = manager.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    llm_settings=llm_settings
)

print(response)