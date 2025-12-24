from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    SimplicityRequest,
    SimplicityResponse,
)


class SimplicityMetric(BaseMetric[SimplicityRequest, SimplicityResponse]):
    """Simplicity metric for v4 API."""
    response_type = SimplicityResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, text: str, **kwargs) -> dict:
        """Build the request dictionary for simplicity evaluation."""
        return self.validate_request_model(SimplicityRequest, text=text, **kwargs).to_dict()

    def evaluate(self, *, text: str, **kwargs) -> SimplicityResponse:
        request_dict = self._build_request(text=text, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/simplicity",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[SimplicityResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
