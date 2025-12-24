from trustwise.sdk.async_client import TrustwiseAsyncClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    StabilityRequest,
    StabilityResponse,
)


class StabilityMetricAsync(BaseMetric[StabilityRequest, StabilityResponse]):
    """Stability metric async for v4 API."""
    response_type = StabilityResponse

    def __init__(self, client: TrustwiseAsyncClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, responses: list[str], **kwargs) -> dict:
        """Build the request dictionary for stability evaluation."""
        return self.validate_request_model(StabilityRequest, responses=responses, **kwargs).to_dict()

    async def evaluate(self, *, responses: list[str], **kwargs) -> StabilityResponse:
        request_dict = self._build_request(responses=responses, **kwargs)
        endpoint = f"{self.base_url}/stability"
        result = await self.client.post(endpoint=endpoint, data=request_dict)
        return self._parse_response(result)
