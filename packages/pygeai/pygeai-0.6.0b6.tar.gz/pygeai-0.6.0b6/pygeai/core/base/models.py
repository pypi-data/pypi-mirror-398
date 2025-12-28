from typing import Optional

from pydantic import Field

from pygeai.core import CustomBaseModel


class Error(CustomBaseModel):
    id: Optional[int] = Field(None, alias="id")
    description: str = Field(..., alias="description")

    def to_dict(self):
        return self.model_dump(by_alias=True, exclude_none=True)

    def __str__(self):
        return str(self.to_dict())
