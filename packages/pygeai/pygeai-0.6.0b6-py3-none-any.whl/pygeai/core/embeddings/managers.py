from pygeai import logger
from pygeai.core.base.mappers import ErrorMapper
from pygeai.core.common.exceptions import APIError
from pygeai.core.embeddings.clients import EmbeddingsClient
from pygeai.core.embeddings.mappers import EmbeddingsResponseMapper
from pygeai.core.embeddings.models import EmbeddingConfiguration
from pygeai.core.embeddings.responses import EmbeddingResponse
from pygeai.core.handlers import ErrorHandler


class EmbeddingsManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = "default"):
        self.__client = EmbeddingsClient(api_key, base_url, alias)

    def generate_embeddings(
            self,
            configuration: EmbeddingConfiguration
    ) -> EmbeddingResponse:
        """
        Generates an embedding vector representing the provided input(s) using the specified model.

        This method calls the API to create a vector representation of the input(s), which can be used
        in machine learning models and algorithms. The request is sent to the embeddings API endpoint.

        :param configuration: EmbeddingConfiguration - An instance containing the configuration for generating
                                                      embeddings, including:
            - inputs: list - A list of strings representing the input(s) to embed. Each input must not
                             exceed the maximum input tokens for the model and cannot be an empty string.
            - model: str - The provider/modelId to use for generating embeddings.
            - encoding_format: str, optional - The format for the returned embeddings, either 'float'
                                                  (default) or 'base64'. Only supported by OpenAI.
            - dimensions: int, optional - The number of dimensions for the resulting output embeddings.
                                           Only supported in text-embedding-3* and later models.
            - user: str, optional - A unique identifier representing the end-user. Specific to OpenAI.
            - input_type: str, optional - Defines how the input data will be used when generating
                                           embeddings. Check if the selected embeddings model supports this option.
            - timeout: int, optional - The maximum time, in seconds, to wait for the API to respond.
                                       Defaults to 600 seconds.
            - cache: bool, optional - Whether to enable caching for the embeddings. Defaults to False.

        :return: EmbeddingResponse - A response object containing the generated embeddings and usage information.
        :raises APIError - If the API returns errors.
        """
        response_data = self.__client.generate_embeddings(
            input_list=configuration.inputs,
            model=configuration.model,
            encoding_format=configuration.encoding_format,
            dimensions=configuration.dimensions,
            user=configuration.user,
            input_type=configuration.input_type,
            timeout=configuration.timeout,
            cache=configuration.cache,
        )

        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while generating embeddings: {error}")
            raise APIError(f"Error received while generating embeddings: {error}")

        result = EmbeddingsResponseMapper.map_to_embedding_response(response_data)
        return result
