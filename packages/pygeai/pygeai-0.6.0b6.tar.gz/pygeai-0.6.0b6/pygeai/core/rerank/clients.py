import json
from json import JSONDecodeError
from typing import Any, Union

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.core.rerank.endpoints import RERANK_V1


class RerankClient(BaseClient):

    def rerank_chunks(
            self,
            query: str,
            model: str,
            documents: list[str],
            top_n: int = 3
    ) -> dict:
        data = {
            "query": query,
            "model": model,
            "documents": documents,
            "top_n": top_n
        }

        logger.debug(f"Generating rerank with data: {data}")

        response = self.api_service.post(
            endpoint=RERANK_V1,
            data=data
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to rerank chunks for query '{query}' with model {model}: JSON parsing error (status {response.status_code}): {e}. Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to rerank chunks for query '{query}' with model {model}: {response.text}")

