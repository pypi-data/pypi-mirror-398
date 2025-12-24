from trustwise.sdk.async_client import TrustwiseAsyncClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    FaithfulnessRequest,
    FaithfulnessResponse,
)


class FaithfulnessMetricAsync(BaseMetric[FaithfulnessRequest, FaithfulnessResponse]):
    """Faithfulness metric async for v4 API."""
    response_type = FaithfulnessResponse
    
    def __init__(self, client: TrustwiseAsyncClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, query: str, response: str, context: list, *, severity: float | None = None, include_citations: bool | None = None, **kwargs) -> dict:
        """Build the request dictionary for faithfulness evaluation."""
        return self.validate_request_model(FaithfulnessRequest, query=query, response=response, context=context, severity=severity, include_citations=include_citations, **kwargs).to_dict()

    async def evaluate(self, *, query: str, response: str, context: list, severity: float | None = None, include_citations: bool | None = None, **kwargs) -> FaithfulnessResponse:
        request_dict = self._build_request(query=query, response=response, context=context, severity=severity, include_citations=include_citations, **kwargs)
        result = await self.client.post(
            endpoint=f"{self.base_url}/faithfulness",
            data=request_dict
        )
        return self._parse_response(result)

    async def batch_evaluate(self, inputs: list[dict]) -> list[FaithfulnessResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
