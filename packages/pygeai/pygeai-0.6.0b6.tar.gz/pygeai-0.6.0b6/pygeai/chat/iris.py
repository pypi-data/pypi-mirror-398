from pygeai.chat.clients import ChatClient
from pygeai.chat.settings import LLM_SETTINGS


class Iris:
    def __init__(self):
        self.client = ChatClient()

    def stream_answer(self, messages):
        result = self.client.chat_completion(
            model="saia:agent:com.globant.iris",
            messages=messages,
            stream=True,
            **LLM_SETTINGS
        )
        return result

