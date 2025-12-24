from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    ToneRequest,
    ToneResponse,
)


class ToneMetric(BaseMetric[ToneRequest, ToneResponse]):
    """Tone metric for v4 API."""
    response_type = ToneResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, text: str, tones: list[str] | None = None, **kwargs) -> dict:
        """Build the request dictionary for tone evaluation."""
        return self.validate_request_model(ToneRequest, text=text, tones=tones, **kwargs).to_dict()

    def evaluate(self, *, text: str, tones: list[str] | None = None, **kwargs) -> ToneResponse:
        request_dict = self._build_request(text=text, tones=tones, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/tone",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[ToneResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
