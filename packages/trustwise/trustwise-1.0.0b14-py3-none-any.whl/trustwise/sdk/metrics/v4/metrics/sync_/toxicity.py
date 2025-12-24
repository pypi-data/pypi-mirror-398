from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    ToxicityRequest,
    ToxicityResponse,
)


class ToxicityMetric(BaseMetric[ToxicityRequest, ToxicityResponse]):
    """Toxicity metric for v4 API."""
    response_type = ToxicityResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, text: str, severity: int | None = None, **kwargs) -> dict:
        """Build the request dictionary for toxicity evaluation."""
        return self.validate_request_model(ToxicityRequest, text=text, severity=severity, **kwargs).to_dict()

    def evaluate(self, *, text: str, severity: int | None = None, **kwargs) -> ToxicityResponse:
        request_dict = self._build_request(text=text, severity=severity, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/toxicity",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[ToxicityResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
