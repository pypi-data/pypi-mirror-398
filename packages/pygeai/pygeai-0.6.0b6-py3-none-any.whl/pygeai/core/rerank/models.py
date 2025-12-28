from typing import List

from pydantic import BaseModel


class RerankResult(BaseModel):
    index: int
    relevance_score: float


class ApiVersion(BaseModel):
    version: str


class BilledUnits(BaseModel):
    search_units: int


class RerankMetaData(BaseModel):
    api_version: ApiVersion
    billed_units: BilledUnits


class RerankResponse(BaseModel):
    id: str
    results: List[RerankResult]
    meta: RerankMetaData
