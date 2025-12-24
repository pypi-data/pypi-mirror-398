import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import requests

from trustwise.sdk.features import is_beta_feature

if TYPE_CHECKING:
    from trustwise.sdk.sdk import TrustwiseSDK
from trustwise.sdk.types import GuardrailResponse


class Guardrail:
    """
    Guardrail system for Trustwise API responses.
    
    .. warning::
        This feature is currently in beta. The API and functionality may change in future releases.
    """

    def __init__(
        self,
        trustwise_client: "TrustwiseSDK",
        thresholds: dict[str, float],
        *, # This is a marker to indicate that the following arguments are keyword-only
        block_on_failure: bool = False,
        callbacks: dict[str, Callable] | None = None
    ) -> None:
        """
        Initialize the guardrail system.

        Args:
            trustwise_client: The Trustwise client instance.
            thresholds: Dictionary of metric names and their threshold values (0-100).
            block_on_failure: Whether to block responses that fail any metric.
            callbacks: Optional callbacks for metric evaluation results.

        Raises:
            ValueError: If thresholds are invalid.
        """
        if is_beta_feature("guardrails"):
            warnings.warn(
                "The guardrails feature is currently in beta. The API and functionality may change in future releases.",
                UserWarning,
                stacklevel=2
            )
            
        # Validate thresholds
        if not thresholds:
            raise ValueError("Thresholds dictionary cannot be empty")
        
        for metric, threshold in thresholds.items():
            if not isinstance(threshold, int | float) or isinstance(threshold, bool):
                raise ValueError(f"Threshold for {metric} must be a number")
            if not 0 <= threshold <= 100:
                raise ValueError(f"Threshold for {metric} must be between 0 and 100")

        self.client = trustwise_client
        self.thresholds = thresholds
        self.block_on_failure = block_on_failure
        self.callbacks = callbacks or {}
        self.evaluation_results = {}

    def _get_metric_kwargs(self, metric: str, query: str, response: str, context: list[dict[str, Any]] | dict[str, Any] | None) -> dict[str, Any]:
        """Get keyword arguments for a given metric."""
        # Define which arguments each metric requires
        metric_arg_map = {
            "faithfulness": {"query": query, "response": response, "context": context},
            "answer_relevancy": {"query": query, "response": response},
            "context_relevancy": {"query": query, "context": context},
            "summarization": {"response": response, "context": context},
            "prompt_injection": {"query": query},
            # Default for most alignment metrics
        }
        # Default for metrics requiring only 'response'
        default_args = {"response": response}
        
        return metric_arg_map.get(metric, default_args)

    def evaluate(
        self,
        query: str,
        response: str,
        context: list[dict[str, Any]] | dict[str, Any] | None = None
    ) -> GuardrailResponse:
        """Evaluate a response against configured metrics."""
        if not response:
            raise ValueError("Response is a required parameter")
        
        required_query_metrics = ["faithfulness", "answer_relevancy", "context_relevancy", "prompt_injection"]
        if any(metric in self.thresholds for metric in required_query_metrics) and not query:
            raise ValueError(f"Query is a required parameter for metrics: {', '.join(required_query_metrics)}")
        
        if context is not None and not isinstance(context, list | dict):
            raise ValueError("Context must be a list or dictionary")
        
        results = {}
        passed = True
        blocked = False
        
        for metric, threshold in self.thresholds.items():
            try:
                metric_evaluator = getattr(self.client.metrics, metric, None)
                if not metric_evaluator:
                    raise ValueError(f"Unknown metric: {metric}")

                kwargs = self._get_metric_kwargs(metric, query, response, context)
                result = metric_evaluator.evaluate(**kwargs)

                if metric == "toxicity":
                    score = max(result.scores) if hasattr(result, "scores") and result.scores else result.score
                else:
                    score = result.score
                
                metric_passed = score >= threshold
                results[metric] = {
                    "passed": metric_passed,
                    "result": result
                }
                
                if metric in self.callbacks:
                    self.callbacks[metric](metric, result)

                if not metric_passed:
                    passed = False
                    if self.block_on_failure:
                        blocked = True
                        break
                        
            except (ValueError, AttributeError, KeyError, TypeError, requests.exceptions.RequestException) as e:
                results[metric] = {
                    "passed": False,
                    "result": {"score": 0.0},
                    "error": str(e)
                }
                passed = False
                if self.block_on_failure:
                    blocked = True
                    break
        
        return GuardrailResponse(
            passed=passed,
            blocked=blocked,
            results=results
        )

    def check_pii(
        self,
        text: str,
        allowlist: list[str] | None = None,
        blocklist: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Check text for PII and determine if it should be blocked.
        
        Args:
            text: Text to check for PII
            allowlist: Optional list of allowed terms
            blocklist: Optional list of blocked terms
            
        Returns:
            Dictionary with PII detection results and pass/fail status
        """
        try:
            result = self.client.metrics.v4.pii.evaluate(
                text=text,
                allowlist=allowlist,
                blocklist=blocklist
            )
            # Consider it passed if no PII is found or only allowlisted items are found
            has_pii = len(result.pii) > 0
            return {
                "passed": not has_pii,
                "result": result,
                "blocked": self.block_on_failure and has_pii
            }
        except (ValueError, AttributeError, KeyError, requests.exceptions.RequestException) as e:
            return {
                "passed": not self.block_on_failure,
                "error": str(e),
                "blocked": self.block_on_failure
            } 