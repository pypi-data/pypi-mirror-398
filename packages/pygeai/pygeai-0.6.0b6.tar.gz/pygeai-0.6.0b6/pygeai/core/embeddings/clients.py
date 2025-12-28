from json import JSONDecodeError

from pygeai import logger
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.core.embeddings.endpoints import GENERATE_EMBEDDINGS


class EmbeddingsClient(BaseClient):

    def generate_embeddings(
            self,
            input_list: list,
            model: str,
            encoding_format: str = None,
            dimensions: int = None,
            user: str = None,
            input_type: str = None,
            timeout: int = None,
            cache: bool = False
    ) -> dict:
        """
        Generates an embedding vector representing the provided input(s) using the specified model.

        This method calls the API to create a vector representation of the input(s), which can be used
        in machine learning models and algorithms. The request is sent to the embeddings API endpoint.

        :param input_list: list - A list of strings representing the input(s) to embed.
                                 Each input must not exceed the maximum input tokens for the model
                                 and cannot be an empty string.
        :param model: str - The provider/modelId to use for generating embeddings.
        :param encoding_format: str, optional - The format for the returned embeddings, either 'float'
                                               (default) or 'base64'. Only supported by OpenAI.
        :param dimensions: int, optional - The number of dimensions for the resulting output embeddings.
                                            Only supported in text-embedding-3* and later models.
        :param user: str, optional - A unique identifier representing the end-user. Specific to OpenAI.
        :param input_type: str, optional - Defines how the input data will be used when generating
                                            embeddings. Check if the selected embeddings model supports this option.
        :param timeout: int, optional - The maximum time, in seconds, to wait for the API to respond.
                                        Defaults to 600 seconds.
        :param cache: bool, optional - Whether to enable caching for the embeddings. Defaults to False.

        :return: dict - A dictionary containing the embedding results, including the model used, the generated
                        embedding vectors, and usage statistics.
        """
        data = {
            'model': model,
            'input': input_list,
        }
        if encoding_format is not None:
            data["encoding_format"] = encoding_format

        if dimensions is not None:
            data["dimensions"] = dimensions

        if user is not None:
            data["user"] = user

        if input_type is not None:
            data["input_type"] = input_type

        if timeout is not None:
            data["timeout"] = timeout

        logger.debug(f"Generating embeddings with data: {data}")

        headers = {}
        if cache:
            headers['X-Saia-Cache-Enabled'] = "true"

        response = self.api_service.post(
            endpoint=GENERATE_EMBEDDINGS,
            data=data,
            headers=headers
        )
        try:
            result = response.json()
            return result
        except JSONDecodeError as e:
            logger.error(f"Unable to generate embeddings: JSON parsin error: {e}; Response: {response.text}")
            raise InvalidAPIResponseException(f"Unable to generate embeddings: {response.text}")

