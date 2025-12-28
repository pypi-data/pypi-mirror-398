from typing import Optional

from pydantic.main import BaseModel


class BaseFile(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None


class UploadFile(BaseFile):
    path: str
    folder: Optional[str] = None


class File(BaseFile):
    extension: Optional[str] = None
    purpose: Optional[str] = None
    size: Optional[int] = 0
    url: Optional[str] = None


class FileList(BaseModel):
    files: list[File] = []