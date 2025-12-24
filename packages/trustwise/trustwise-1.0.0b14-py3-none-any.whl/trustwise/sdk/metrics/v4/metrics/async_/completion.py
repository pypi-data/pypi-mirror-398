from trustwise.sdk.async_client import TrustwiseAsyncClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    CompletionRequest,
    CompletionResponse,
)


class CompletionMetricAsync(BaseMetric[CompletionRequest, CompletionResponse]):
    """Completion metric async for v4 API."""
    response_type = CompletionResponse
    
    def __init__(self, client: TrustwiseAsyncClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, query: str, response: str, **kwargs) -> dict:
        """Build the request dictionary for completion evaluation."""
        return self.validate_request_model(CompletionRequest, query=query, response=response, **kwargs).to_dict()

    async def evaluate(self, *, query: str, response: str, **kwargs) -> CompletionResponse:
        request_dict = self._build_request(query=query, response=response, **kwargs)
        endpoint = f"{self.base_url}/completion"
        result = await self.client.post(endpoint=endpoint, data=request_dict)
        return self._parse_response(result)

    async def batch_evaluate(self, inputs: list[dict]) -> list[CompletionResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
