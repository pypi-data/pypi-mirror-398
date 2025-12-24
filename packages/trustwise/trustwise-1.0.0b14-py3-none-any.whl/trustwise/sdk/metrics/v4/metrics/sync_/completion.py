from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    CompletionRequest,
    CompletionResponse,
)


class CompletionMetric(BaseMetric[CompletionRequest, CompletionResponse]):
    """Completion metric for v4 API."""
    response_type = CompletionResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, query: str, response: str, **kwargs) -> dict:
        """Build the request dictionary for completion evaluation."""
        return self.validate_request_model(CompletionRequest, query=query, response=response, **kwargs).to_dict()

    def evaluate(self, *, query: str, response: str, **kwargs) -> CompletionResponse:
        request_dict = self._build_request(query=query, response=response, **kwargs)
        endpoint = f"{self.base_url}/completion"
        result = self.client._post(endpoint=endpoint, data=request_dict)
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[CompletionResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
