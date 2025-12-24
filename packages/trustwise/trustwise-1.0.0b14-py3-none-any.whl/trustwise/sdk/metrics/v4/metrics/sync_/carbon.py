from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    CarbonRequest,
    CarbonResponse,
)


class CarbonMetric(BaseMetric[CarbonRequest, CarbonResponse]):
    """Carbon metric for v4 API."""
    response_type = CarbonResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, provider: str, region: str, instance_type: str, latency: float | int, **kwargs) -> dict:
        """Build the request dictionary for carbon evaluation."""
        return self.validate_request_model(CarbonRequest, provider=provider, region=region, instance_type=instance_type, latency=latency, **kwargs).to_dict()

    def evaluate(self, *, provider: str, region: str, instance_type: str, latency: float | int, **kwargs) -> CarbonResponse:
        request_dict = self._build_request(provider=provider, region=region, instance_type=instance_type, latency=latency, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/carbon",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[CarbonResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
