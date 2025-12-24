from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    ContextRelevancyRequest,
    ContextRelevancyResponse,
)


class ContextRelevancyMetric(BaseMetric[ContextRelevancyRequest, ContextRelevancyResponse]):
    """Context relevancy metric for v4 API."""
    response_type = ContextRelevancyResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, query: str, context: list, *, severity: float | None = None, include_chunk_scores: bool | None = None, **kwargs) -> dict:
        """Build the request dictionary for context relevancy evaluation."""
        return self.validate_request_model(ContextRelevancyRequest, query=query, context=context, severity=severity, include_chunk_scores=include_chunk_scores, **kwargs).to_dict()

    def evaluate(self, *, query: str, context: list, severity: float | None = None, include_chunk_scores: bool | None = None, **kwargs) -> ContextRelevancyResponse:
        request_dict = self._build_request(query=query, context=context, severity=severity, include_chunk_scores=include_chunk_scores, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/context_relevancy",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[ContextRelevancyResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
