from typing import Optional
import requests as req
import json


class ResponseMock:
    def __init__(self, status_code: int, content: str, url: Optional[str], reason: str):
        self.status_code = status_code
        self.content = content
        self.url = url
        self.reason = reason

    def raise_for_status(self):
        if self.status_code >= 400:
            raise req.exceptions.HTTPError(f"{self.status_code} {self.reason}")

    def json(self):
        return json.loads(self.content)