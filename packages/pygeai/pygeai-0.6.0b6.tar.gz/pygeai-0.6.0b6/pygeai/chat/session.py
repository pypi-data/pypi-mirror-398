from pygeai import logger
from pygeai.chat.clients import ChatClient

from pygeai.chat.settings import LLM_SETTINGS
from pygeai.core.common.exceptions import InvalidAPIResponseException


class AgentChatSession:

    def __init__(self, agent_name: str):
        self.client = ChatClient()
        self.agent_name = agent_name

    def stream_answer(self, messages):
        result = self.client.chat_completion(
            model=f"saia:agent:{self.agent_name}",
            messages=messages,
            stream=True,
            **LLM_SETTINGS
        )
        return result

    def get_answer(self, messages):
        answer = ""
        try:
            result = self.client.chat_completion(
                model=f"saia:agent:{self.agent_name}",
                messages=messages,
                stream=False,
                **LLM_SETTINGS
            )
            answer = result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Unable to communicate with specified agent {self.agent_name}: {e}")
            raise InvalidAPIResponseException(f"Unable to communicate with specified agent {self.agent_name}: {e}")

        return answer

