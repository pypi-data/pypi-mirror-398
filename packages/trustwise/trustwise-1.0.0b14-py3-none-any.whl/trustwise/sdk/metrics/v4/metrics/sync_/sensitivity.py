from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    SensitivityRequest,
    SensitivityResponse,
)


class SensitivityMetric(BaseMetric[SensitivityRequest, SensitivityResponse]):
    """Sensitivity metric for v4 API."""
    response_type = SensitivityResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, text: str, topics: list[str], **kwargs) -> dict:
        """Build the request dictionary for sensitivity evaluation."""
        return self.validate_request_model(SensitivityRequest, text=text, topics=topics, **kwargs).to_dict()

    def evaluate(self, *, text: str, topics: list[str], **kwargs) -> SensitivityResponse:
        request_dict = self._build_request(text=text, topics=topics, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/sensitivity",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[SensitivityResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
