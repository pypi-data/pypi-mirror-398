from collections.abc import Callable

from trustwise.sdk.client import TrustwiseClient
from trustwise.sdk.config import TrustwiseConfig
from trustwise.sdk.features import get_beta_features, is_beta_feature
from trustwise.sdk.guardrails.guardrail import Guardrail
from trustwise.sdk.metrics import Metrics


class TrustwiseSDK:
    """
    Main SDK class for Trustwise API access.

    Provides access to all metrics through version-specific paths.
    """

    def __init__(self, config: TrustwiseConfig) -> None:
        """
        Initialize the Trustwise SDK with path-based versioning support.

        Args:
            config: Trustwise configuration instance.
        """
        self.client = TrustwiseClient(config)
        self.metrics = Metrics(self.client)

    def get_versions(self) -> dict[str, list[str]]:
        """
        Get the available API versions for the metrics.

        Returns:
            Dictionary mapping 'metrics' to its available versions.
            Example: {"metrics": ["v3"]}
        """
        return {"metrics": ["v3", "v4"]}

    def get_beta_features(self) -> set[str]:
        """
        Get the set of features currently in beta.

        Returns:
            Set[str]: Set of feature names that are in beta
        """
        return get_beta_features()

    def is_beta_feature(self, feature_name: str) -> bool:
        """
        Check if a feature is currently in beta.

        Args:
            feature_name: Name of the feature to check

        Returns:
            bool: True if the feature is in beta, False otherwise
        """
        return is_beta_feature(feature_name)

    def guardrails(
        self,
        thresholds: dict[str, float],
        *,
        block_on_failure: bool = False,
        callbacks: dict[str, Callable] | None = None
    ) -> Guardrail:
        """
        Create a guardrail system for response evaluation.

        Args:
            thresholds: Dictionary mapping metrics to threshold values.
            block_on_failure: Whether to block responses that fail checks.
            callbacks: Dictionary mapping metrics to callback functions.

        Returns:
            A configured Guardrail instance.

        Raises:
            ValueError: If any metric in thresholds is not supported by the current API version.
        """
        return Guardrail(
            trustwise_client=self,
            thresholds=thresholds,
            block_on_failure=block_on_failure,
            callbacks=callbacks
        ) 