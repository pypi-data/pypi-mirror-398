from pygeai import logger
from pygeai.core.common.exceptions import APIError
from pygeai.core.handlers import ErrorHandler
from pygeai.core.rerank.clients import RerankClient
from pygeai.core.rerank.mappers import RerankResponseMapper
from pygeai.core.rerank.models import RerankResponse


class RerankManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default"):
        self.__client = RerankClient(api_key, base_url, alias)

    def rerank_chunks(
            self,
            query: str,
            model: str,
            documents: list[str],
            top_n: int = 3
    ) -> RerankResponse:
        """
        Reranks a list of documents based on their relevance to the given query.

        This method sends a rerank request to the RerankClient using the specified
        model, query, and list of documents. It processes the API response by
        checking for errors and mapping the result into a structured RerankResponse.

        :param query: str - The query string used to evaluate document relevance.
        :param model: str - The identifier of the reranking model to use.
        :param documents: list[str] - A list of document strings to be evaluated and reranked.
        :param top_n: int, optional - The number of top-ranked documents to return. Defaults to 3.
        :return: RerankResponse - The structured reranking response containing the top documents and scores.
        :raises APIError: If the API returns errors.
        """
        response_data = self.__client.rerank_chunks(
            query=query,
            model=model,
            documents=documents,
            top_n=top_n
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while reranking chunks: {error}")
            raise APIError(f"Error received while reranking chunks: {error}")

        result = RerankResponseMapper.map_to_rerank_response(response_data)
        return result
