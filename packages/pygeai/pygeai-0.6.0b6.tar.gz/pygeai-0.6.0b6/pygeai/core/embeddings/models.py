from typing import List, Optional

from pydantic.main import BaseModel


class EmbeddingConfiguration(BaseModel):
    inputs: List[str]
    model: str
    encoding_format: Optional[str] = None
    dimensions: Optional[int] = None
    user: Optional[str] = None
    input_type: Optional[str] = None
    timeout: Optional[int] = None
    cache: Optional[bool] = False
