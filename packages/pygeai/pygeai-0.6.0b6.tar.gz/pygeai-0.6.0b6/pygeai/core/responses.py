from typing import Optional, List

from pydantic.main import BaseModel

from pygeai.core.models import Project, Assistant, ChatMessage


class AssistantResponse(BaseModel):
    assistant: Assistant


class NewAssistantResponse(BaseModel):
    assistant: Optional[Assistant] = None
    project: Optional[Project] = None


class TokenDetails(BaseModel):
    reasoning_tokens: Optional[int] = None
    cached_tokens: Optional[int] = None


class UsageDetails(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_cost: float
    completion_tokens_details: Optional[TokenDetails] = None
    prompt_tokens_details: Optional[TokenDetails] = None
    total_tokens: int
    currency: str
    completion_cost: float
    prompt_cost: float


class Choice(BaseModel):
    finish_reason: str
    index: int
    message: Optional[ChatMessage] = None


class ProviderResponse(BaseModel):
    created: int
    usage: UsageDetails
    model: str
    service_tier: Optional[str] = None
    id: Optional[str] = None
    system_fingerprint: Optional[str] = None
    choices: List[Choice]
    object: Optional[str] = None


class ChatResponse(BaseModel):
    """
    {
    'progress': 100,
    'providerName': 'openai',
    'providerResponse': '{
        "created":1738936741,
        "usage":{
            "completion_tokens":15,
            "prompt_tokens":34,
            "total_cost":0.00192,
            "completion_tokens_details":{
                "reasoning_tokens":0
            },
            "prompt_tokens_details":{
                "cached_tokens":0
            },
            "total_tokens":49,
            "currency":"USD",
            "completion_cost":0.0009,
            "prompt_cost":0.00102
        },
        "model":"gpt-4o-2024-08-06",
        "service_tier":"default",
        "id":"chatcmpl-AyJAjwWvbcvKQ5HO29YbGS7t4b5hr",
        "system_fingerprint":"fp_4691090a87",
        "choices":[
            {
            "finish_reason":"stop",
            "index":0,
            "message":{
                "role":"assistant",
                "function_call":null,
                "refusal":null,
                "tool_calls":null,
                "content":"Le logiciel libre est le logiciel qui protège les libertés des utilisateurs."
                }
            }
        ],
        "object":"chat.completion"
    }',
    'requestId': '458c003a-d7fb-4d31-867c-d009ebb9d9c5',
    'status': 'succeeded',
    'success': True,
    'text': 'Le logiciel libre est le logiciel qui protège les libertés des utilisateurs.'
    }
    """
    progress: Optional[int] = None
    provider_name: Optional[str] = None
    provider_response: Optional[ProviderResponse] = None
    request_id: Optional[str] = None
    status: Optional[str] = None
    success: Optional[bool] = False
    text: Optional[str] = False
