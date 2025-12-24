from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    PromptManipulationRequest,
    PromptManipulationResponse,
)


class PromptManipulationMetric(BaseMetric[PromptManipulationRequest, PromptManipulationResponse]):
    """Prompt manipulation metric for v4 API."""
    response_type = PromptManipulationResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, text: str, severity: int | None = None, **kwargs) -> dict:
        """Build the request dictionary for prompt manipulation evaluation."""
        return self.validate_request_model(PromptManipulationRequest, text=text, severity=severity, **kwargs).to_dict()

    def evaluate(self, *, text: str, severity: int | None = None, **kwargs) -> PromptManipulationResponse:
        request_dict = self._build_request(text=text, severity=severity, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/prompt_manipulation",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[PromptManipulationResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
