from pygeai.core.embeddings.responses import EmbeddingResponse, EmbeddingData, UsageInfo


class EmbeddingsResponseMapper:

    @classmethod
    def map_to_embedding_response(cls, data: dict) -> EmbeddingResponse:
        embedding_data_list = cls.map_to_embedding_data_list(data.get('data', []))
        usage_info = cls.map_to_usage_info(data.get('usage', {}))

        return EmbeddingResponse(
            data=embedding_data_list,
            usage=usage_info,
            model=data.get('model', ''),
            object=data.get('object', '')
        )

    @classmethod
    def map_to_embedding_data_list(cls, data: list) -> list[EmbeddingData]:
        embedding_data_list = []
        for item in data:
            embedding_data = EmbeddingData(
                index=item.get('index', 0),
                embedding=item.get('embedding', []),
                object=item.get('object', '')
            )
            embedding_data_list.append(embedding_data)
        return embedding_data_list

    @classmethod
    def map_to_usage_info(cls, data: dict) -> UsageInfo:
        return UsageInfo(
            prompt_tokens=data.get('prompt_tokens', 0),
            total_cost=data.get('total_cost', 0.0),
            total_tokens=data.get('total_tokens', 0),
            currency=data.get('currency', ''),
            prompt_cost=data.get('prompt_cost', 0.0)
        )