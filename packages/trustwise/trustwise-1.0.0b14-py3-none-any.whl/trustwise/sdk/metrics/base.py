import logging
import warnings
from abc import ABC, abstractmethod
from typing import (
    Any,
    Generic,
    TypeVar,
)

from pydantic import ValidationError

from trustwise.sdk.exceptions import TrustwiseValidationError
from trustwise.sdk.types import (
    CostRequestV3,
    CostResponseV3,
    SDKBaseModel,
)

logger = logging.getLogger(__name__)

# Generic type variables for request and response
TRequest = TypeVar("TRequest")
TResponse = TypeVar("TResponse")


class BaseMetric(ABC, Generic[TRequest, TResponse]):  # noqa: UP046
    """
    Base class for all metrics. Each metric should inherit from this class
    and implement the required methods.
    """
    response_type = None  # Subclasses must set this
    
    def __init__(self, client: Any, base_url: str, endpoint: str) -> None:
        """
        Initialize a metric.
        
        Args:
            client: The client instance (sync or async)
            base_url: Base URL for the API
            endpoint: The specific endpoint for this metric
        """
        self.client = client
        self.base_url = base_url
        self.endpoint = endpoint
        logger.debug("Initialized %s with base_url: %s, endpoint: %s", 
                    self.__class__.__name__, base_url, endpoint)

    def _get_endpoint(self) -> str:
        """Get the full URL for this metric's endpoint."""
        return f"{self.base_url}/{self.endpoint}"

    def _check_deprecation(self) -> None:
        """Check if this metric is deprecated and emit a warning if so."""
        # Check if this is a v3 metric by looking at the base_url
        if "v3" in self.base_url:
            warnings.warn(
                "V3 metrics are deprecated and will be removed in a future version. "
                "Please migrate to V4 metrics for continued support and enhanced features. "
                "See the migration guide for more details: https://trustwiseai.github.io/trustwise/migration_guide.html",
                FutureWarning,
                stacklevel=3
            )

    @abstractmethod
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Evaluate the metric. Must be implemented by concrete classes."""
        raise NotImplementedError

    @abstractmethod
    def _build_request(self, *args, **kwargs) -> dict:
        """Build the request dictionary. Must be implemented by concrete classes."""
        raise NotImplementedError
    
    @staticmethod
    def _handle_new_api_response(result: dict) -> tuple[dict, dict | None]:
        """
        Handle the new API response format with data wrapper.
        Returns a tuple of (data, metadata).
        """
        data = result["data"]
        metadata = result.get("metadata", None)
        if "message" in result:
            logger.debug("API response message: %s", result["message"])
        return data, metadata

    def _parse_response(self, result: dict) -> TResponse:
        """
        Parse the response using the metric's response type.
        Attaches metadata as _metadata attribute if present.
        
        Returns:
            The parsed response object with _metadata attribute if metadata exists.
        """
        logger.debug("Parsing response for %s", self.response_type.__name__)
        if self.response_type is None:
            raise NotImplementedError("Subclasses must set response_type")

        # Handle new API response format with data wrapper
        if "data" in result and isinstance(result["data"], dict):
            data, metadata = self._handle_new_api_response(result)
        else:
            # Handle legacy direct response format
            data = result
            metadata = result.get("metadata", None)
        
        original_response = result

        try:
            parsed_data = self.response_type(**data)
            
            # Attach metadata as _metadata attribute if it exists
            # Using underscore prefix to clearly indicate this is API-level metadata
            # not part of the evaluation result data
            if metadata is not None:
                parsed_data._metadata = metadata
            
            return parsed_data
            
        except Exception as e:
            # Log additional context for better debugging
            if original_response != data:
                # Wrapped response format - log both original and extracted data
                logger.error(
                    "Failed to parse %s from wrapped response. "
                    "Original response: %s, Extracted data: %s, Error: %s",
                    self.response_type.__name__, original_response, data, e
                )
            else:
                # Direct response format
                logger.error(
                    "Failed to parse %s from response: %s, Error: %s",
                    self.response_type.__name__, data, e
                )
            # Re-raise the original exception to preserve Pydantic validation details
            raise

    def batch_evaluate(self, inputs: list[TRequest]) -> list[TResponse]:
        """Evaluate multiple inputs in a single request. Optional implementation."""
        raise NotImplementedError("Batch evaluation not supported for this metric")

    @staticmethod
    def validate_request_model(model_cls: type, **kwargs: Any) -> object:
        """
        Standardized Trustwise validation for all metric request models.
        Usage: req = BaseMetric.validate_request_model(RequestModel, **kwargs)
        Raises TrustwiseValidationError with a formatted message on error.
        """
        try:
            return model_cls(**kwargs)
        except ValidationError as ve:
            raise TrustwiseValidationError(SDKBaseModel.format_validation_error(model_cls, ve)) from ve
        except TypeError as te:
            # Detect missing required arguments
            import inspect
            sig = inspect.signature(model_cls)
            missing_args = []
            for name, param in sig.parameters.items():
                if param.default is param.empty and name not in kwargs:
                    missing_args.append(name)
            if missing_args:
                class DummyValidationError(Exception):
                    def errors(self) -> list:
                        return [
                            {"loc": [arg], "msg": "field required"} for arg in missing_args
                        ]
                ve = DummyValidationError()
                raise TrustwiseValidationError(SDKBaseModel.format_validation_error(model_cls, ve)) from te
            else:
                raise


class CostMetricBase(BaseMetric[CostRequestV3, CostResponseV3]):
    """Base class for cost metric implementations."""
    response_type = CostResponseV3
    
    def _build_request(self, model_name: str, model_type: str, model_provider: str,
                      number_of_queries: int, total_prompt_tokens: int,
                      total_completion_tokens: int, **kwargs) -> dict:
        """Build the request dictionary for cost evaluation."""
        return self.validate_request_model(
            CostRequestV3,
            model_name=model_name,
            model_type=model_type,
            model_provider=model_provider,
            number_of_queries=number_of_queries,
            total_prompt_tokens=total_prompt_tokens,
            total_completion_tokens=total_completion_tokens,
            **kwargs
        ).to_dict()
