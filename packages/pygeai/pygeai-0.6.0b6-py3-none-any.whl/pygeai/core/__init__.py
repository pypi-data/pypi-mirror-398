"""
GEAI - Core
-----------
Core functionality for the PyGEAI SDK
"""

from pydantic import BaseModel


class CustomBaseModel(BaseModel):

    class Config:
        populate_by_name = True
