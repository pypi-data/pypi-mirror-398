from pygeai.chat.managers import ChatManager
from pygeai.core.models import LlmSettings, ChatMessageList, ChatMessage


manager = ChatManager()


llm_settings = LlmSettings(
    temperature=0.7,
    max_tokens=1000
)

messages = ChatMessageList(
    messages=[
        ChatMessage(
            role="user",
            content="Hi, welcome to Globant Enterprise AI!!"
        )
    ]
)

response = manager.chat_completion(
    model="saia:assistant:Welcome data Assistant 3",
    messages=messages,
    llm_settings=llm_settings
)

print(response)
