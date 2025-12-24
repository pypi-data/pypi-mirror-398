from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    AdherenceRequest,
    AdherenceResponse,
)


class AdherenceMetric(BaseMetric[AdherenceRequest, AdherenceResponse]):
    """Adherence metric for v4 API."""
    response_type = AdherenceResponse

    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, policy: str, response: str, **kwargs) -> dict:
        """Build the request dictionary for adherence evaluation."""
        return self.validate_request_model(AdherenceRequest, policy=policy, response=response, **kwargs).to_dict()

    def evaluate(self, *, policy: str, response: str, **kwargs) -> AdherenceResponse:
        request_dict = self._build_request(policy=policy, response=response, **kwargs)
        endpoint = f"{self.base_url}/adherence"
        result = self.client._post(endpoint=endpoint, data=request_dict)
        return self._parse_response(result)
