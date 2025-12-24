import warnings
from typing import Any

from trustwise.sdk.metrics.v3 import (
    CostMetric,
)
from trustwise.sdk.metrics.v4 import (
    AdherenceMetric as AdherenceMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    AnswerRelevancyMetric as AnswerRelevancyMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    CarbonMetric as CarbonMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    ClarityMetric as ClarityMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    CompletionMetric as CompletionMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    ContextRelevancyMetric as ContextRelevancyMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    FaithfulnessMetric as FaithfulnessMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    FormalityMetric as FormalityMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    HelpfulnessMetric as HelpfulnessMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    PIIMetric as PIIMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    PromptManipulationMetric,
)
from trustwise.sdk.metrics.v4 import (
    RefusalMetric as RefusalMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    SensitivityMetric as SensitivityMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    SimplicityMetric as SimplicityMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    StabilityMetric as StabilityMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    ToneMetric as ToneMetricV4,
)
from trustwise.sdk.metrics.v4 import (
    ToxicityMetric as ToxicityMetricV4,
)


class DeprecatedMetricWrapper:
    """Wrapper class that adds deprecation warnings to v3 metrics."""
    
    def __init__(self, metric_instance: Any) -> None:
        self._metric = metric_instance
        
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped metric."""
        return getattr(self._metric, name)
    
    def evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Evaluate the metric with deprecation warning."""
        warnings.warn(
            "V3 metrics are deprecated and will be removed in a future version. "
            "Please migrate to V4 metrics for continued support and enhanced features. "
            "See the migration guide for more details: https://trustwiseai.github.io/trustwise/migration_guide.html",
            FutureWarning,
            stacklevel=3
        )
        return self._metric.evaluate(*args, **kwargs)
    
    def batch_evaluate(self, *args: Any, **kwargs: Any) -> Any:
        """Batch evaluate the metric with deprecation warning."""
        warnings.warn(
            "V3 metrics are deprecated and will be removed in a future version. "
            "Please migrate to V4 metrics for continued support and enhanced features. "
            "See the migration guide for more details: https://trustwiseai.github.io/trustwise/migration_guide.html",
            FutureWarning,
            stacklevel=3
        )
        return self._metric.batch_evaluate(*args, **kwargs)


class MetricsV3:
    def __init__(self, client: Any) -> None:
        self.cost = CostMetric(client)


class MetricsV4:
    def __init__(self, client: Any) -> None:
        self.prompt_manipulation = PromptManipulationMetric(client)
        self.answer_relevancy = AnswerRelevancyMetricV4(client)
        self.carbon = CarbonMetricV4(client)
        self.context_relevancy = ContextRelevancyMetricV4(client)
        self.faithfulness = FaithfulnessMetricV4(client)
        self.formality = FormalityMetricV4(client)
        self.clarity = ClarityMetricV4(client)
        self.helpfulness = HelpfulnessMetricV4(client)
        self.simplicity = SimplicityMetricV4(client)
        self.sensitivity = SensitivityMetricV4(client)
        self.tone = ToneMetricV4(client)
        self.toxicity = ToxicityMetricV4(client)
        self.pii = PIIMetricV4(client)
        self.refusal = RefusalMetricV4(client)
        self.completion = CompletionMetricV4(client)
        self.adherence = AdherenceMetricV4(client)
        self.stability = StabilityMetricV4(client)

class Metrics:
    def __init__(self, client: Any) -> None:
        self.v3 = MetricsV3(client)
        self.v4 = MetricsV4(client)
        
        # Expose v4 metrics directly as default
        self.prompt_manipulation = self.v4.prompt_manipulation
        self.answer_relevancy = self.v4.answer_relevancy
        self.carbon = self.v4.carbon
        self.context_relevancy = self.v4.context_relevancy
        self.faithfulness = self.v4.faithfulness
        self.formality = self.v4.formality
        self.clarity = self.v4.clarity
        self.helpfulness = self.v4.helpfulness
        self.simplicity = self.v4.simplicity
        self.sensitivity = self.v4.sensitivity
        self.tone = self.v4.tone
        self.toxicity = self.v4.toxicity
        self.pii = self.v4.pii
        self.refusal = self.v4.refusal
        self.completion = self.v4.completion
        self.adherence = self.v4.adherence
        self.stability = self.v4.stability

    @property
    def version(self) -> str:
        return "v4"

__all__ = ["Metrics", "MetricsV3"] 