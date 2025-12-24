"""Trustwise SDK for evaluating AI-generated content."""

try:
    from importlib.metadata import version
    __version__ = version("trustwise")
except ImportError:
    # Fallback for Python < 3.8
    from pkg_resources import get_distribution
    __version__ = get_distribution("trustwise").version

# Export exceptions using absolute imports
from trustwise.sdk.exceptions import (
    TrustwiseAPIError,
    TrustwiseSDKError,
    TrustwiseValidationError,
)

# Export types for type checking and user convenience
from trustwise.sdk.types import (
    CostRequestV3,
    CostResponseV3,
    GuardrailResponse,
)

__all__ = [
    "CostRequestV3",
    "CostResponseV3",
    "GuardrailResponse",
    "TrustwiseAPIError",
    "TrustwiseSDKError",
    "TrustwiseValidationError",
]
