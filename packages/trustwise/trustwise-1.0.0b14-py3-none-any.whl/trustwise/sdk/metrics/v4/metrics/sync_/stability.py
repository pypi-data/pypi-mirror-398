from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    StabilityRequest,
    StabilityResponse,
)


class StabilityMetric(BaseMetric[StabilityRequest, StabilityResponse]):
    """Stability metric for v4 API."""
    response_type = StabilityResponse

    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, responses: list[str], **kwargs) -> dict:
        """Build the request dictionary for stability evaluation."""
        return self.validate_request_model(StabilityRequest, responses=responses, **kwargs).to_dict()

    def evaluate(self, *, responses: list[str], **kwargs) -> StabilityResponse:
        request_dict = self._build_request(responses=responses, **kwargs)
        endpoint = f"{self.base_url}/stability"
        result = self.client._post(endpoint=endpoint, data=request_dict)
        return self._parse_response(result)
