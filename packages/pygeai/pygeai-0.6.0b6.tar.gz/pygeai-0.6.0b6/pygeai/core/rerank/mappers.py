from pygeai.core.rerank.models import RerankResponse, RerankResult, RerankMetaData, ApiVersion, BilledUnits


class RerankResponseMapper:

    @classmethod
    def map_to_rerank_response(cls, data: dict) -> RerankResponse:
        return RerankResponse(
            id=data.get("id"),
            results=cls.map_to_rerank_results(data.get("results", [])),
            meta=cls.map_to_rerank_metadata(data.get("meta", {}))
        )

    @classmethod
    def map_to_rerank_results(cls, results: list) -> list[RerankResult]:
        return [RerankResult(index=item["index"], relevance_score=item["relevance_score"]) for item in results]

    @classmethod
    def map_to_rerank_metadata(cls, data: dict) -> RerankMetaData:
        return RerankMetaData(
            api_version=ApiVersion(version=data.get("api_version", {}).get("version", "")),
            billed_units=BilledUnits(search_units=data.get("billed_units", {}).get("search_units", 0))
        )
