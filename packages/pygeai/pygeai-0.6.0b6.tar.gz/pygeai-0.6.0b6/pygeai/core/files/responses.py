from typing import Optional
from pydantic.main import BaseModel


class UploadFileResponse(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    success: Optional[bool] = None

    def to_dict(self):
        return {
            'dataFileId': self.id,
            'dataFileUrl': self.url,
            'success': self.success
        }

    def __str__(self):
        data = self.to_dict()
        return str(data)
