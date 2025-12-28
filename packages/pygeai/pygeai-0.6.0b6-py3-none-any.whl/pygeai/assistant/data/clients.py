import json

from pygeai.assistant.clients import AssistantClient
from pygeai.assistant.endpoints import GET_ASSISTANT_DATA_V1, CREATE_ASSISTANT_V1, UPDATE_ASSISTANT_V1, BEGIN_CONVERSATION_V1, \
    SEND_TEXT_PROMPT_V1, SEND_CHAT_REQUEST_V1, GET_REQUEST_STATUS_V1, CANCEL_REQUEST_V1
from pygeai.assistant.data_analyst.endpoints import GET_DATA_ANALYST_STATUS_V1, EXTEND_DATA_ANALYST_DATASET_V1
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.decorators import handler_server_error


class ChatWithDataAssistantClient(AssistantClient):
    # TODO -> load_metadata(
    pass

