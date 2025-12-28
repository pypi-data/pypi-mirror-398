from typing import List

from pydantic.main import BaseModel


class EmbeddingData(BaseModel):
    index: int
    embedding: List[float]
    object: str


class UsageInfo(BaseModel):
    prompt_tokens: int
    total_cost: float
    total_tokens: int
    currency: str
    prompt_cost: float


class EmbeddingResponse(BaseModel):
    data: List[EmbeddingData]
    usage: UsageInfo
    model: str
    object: str
