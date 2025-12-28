from typing import List

from pydantic.main import BaseModel

from pygeai.assistant.rag.models import Document


class DocumentListResponse(BaseModel):
    count: int
    documents: List[Document]