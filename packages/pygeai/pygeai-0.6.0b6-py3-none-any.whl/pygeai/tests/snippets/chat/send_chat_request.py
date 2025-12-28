from pygeai.assistant.managers import AssistantManager
from pygeai.core.models import Assistant, ChatMessageList, ChatMessage, AssistantRevision, \
    ChatVariableList, ChatVariable

assistant = Assistant(
    id="3372b866-36b3-4541-8897-d371dab99f10",
    name='Welcome data Assistant 4',
)

messages = ChatMessageList(
    messages=[
        ChatMessage(role="user", content="Hello!"),
        ChatMessage(role="assistant", content="Hi there! How can I help?")
    ]
)

revision = AssistantRevision(
    revision_id=1.0,
    revision_name="Default"
)

variables = ChatVariableList(
    variables=[
        ChatVariable(key="user_name", value="John Doe")
    ]
)


manager = AssistantManager()
#response = client.send_chat_request(assistant, messages, revision, variables)
response = manager.send_chat_request(assistant, messages)

print("Response:", response)
