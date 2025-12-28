from pydantic import BaseModel, Field

from pygeai.core import CustomBaseModel


class FeedbackRequest(CustomBaseModel):
    request_id: str = Field(..., alias="requestId")
    origin: str = Field("user-feedback", alias="origin")
    answer_score: int = Field(..., alias="answerScore")
    comments: str = Field(None, alias="comments")
