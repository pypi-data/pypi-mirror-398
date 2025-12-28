from typing import Optional, Union
from pydantic import Field

from pydantic.main import BaseModel

from pygeai.core.base.models import Error


class ErrorListResponse(BaseModel):
    errors: list[Error]

    def to_dict(self):
        return [error.to_dict() for error in self.errors]


class EmptyResponse(BaseModel):
    content: Optional[Union[dict, str]] = Field(default=None, description="The response content, either a dict, str, or None")

    def to_dict(self):
        """
        Serializes the EmptyResponse instance to a dictionary.

        :return: dict - A dictionary representation of the response.
        """
        return {"content": self.content} if self.content is not None else {}

    def __str__(self):
        return str(self.to_dict())