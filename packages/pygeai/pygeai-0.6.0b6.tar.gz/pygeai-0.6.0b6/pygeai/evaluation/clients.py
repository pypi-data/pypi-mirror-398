from pygeai.core.base.clients import BaseClient
from pygeai.core.base.session import Session
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.services.rest import ApiService


class EvaluationClient(BaseClient):

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default", eval_url: str = None):
        super().__init__(api_key, base_url, alias)
        eval_url = self.session.eval_url if not eval_url else None
        if not eval_url:
            raise MissingRequirementException("EVAL URL must be defined in order to use the Evaluation module.")

        self.session.eval_url = eval_url
        self.api_service = ApiService(base_url=self.session.eval_url, token=self.session.api_key)
