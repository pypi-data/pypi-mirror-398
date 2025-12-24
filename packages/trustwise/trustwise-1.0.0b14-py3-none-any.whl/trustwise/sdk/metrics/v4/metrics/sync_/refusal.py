from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.metrics.base import BaseMetric
from trustwise.sdk.metrics.v4.types import (
    RefusalRequest,
    RefusalResponse,
)


class RefusalMetric(BaseMetric[RefusalRequest, RefusalResponse]):
    """Refusal metric for v4 API."""
    response_type = RefusalResponse
    
    def __init__(self, client: TrustwiseClient) -> None:
        self.client = client
        self.base_url = client.config.get_metrics_url("v4")

    def _build_request(self, query: str, response: str, **kwargs) -> dict:
        """Build the request dictionary for refusal evaluation."""
        return self.validate_request_model(RefusalRequest, query=query, response=response, **kwargs).to_dict()

    def evaluate(self, *, query: str, response: str, **kwargs) -> RefusalResponse:
        request_dict = self._build_request(query=query, response=response, **kwargs)
        result = self.client._post(
            endpoint=f"{self.base_url}/refusal",
            data=request_dict
        )
        return self._parse_response(result)

    def batch_evaluate(self, inputs: list[dict]) -> list[RefusalResponse]:
        raise NotImplementedError("Batch evaluation not yet supported")
