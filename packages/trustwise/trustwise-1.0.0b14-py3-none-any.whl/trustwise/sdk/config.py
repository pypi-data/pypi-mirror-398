"""Simple configuration for Trustwise API with environment variable support."""

import os
from urllib.parse import urljoin, urlparse

from pydantic import BaseModel, Field, ValidationError

from trustwise.sdk.exceptions import TrustwiseValidationError


class TrustwiseConfig(BaseModel):
    """Configuration for Trustwise API.
    
    This class handles configuration for the Trustwise API, including authentication and endpoint URLs.
    It supports both direct initialization and environment variables.
    
    Args:
        api_key (str, Optional): API key for authentication. If not provided, will be read from
            TW_API_KEY environment variable. Required for API access.
        base_url (str, Optional): Base URL for API endpoints. If not provided, will be read from
            TW_BASE_URL environment variable or default to https://api.trustwise.ai.
    
    Environment Variables:
        - TW_API_KEY: API key for authentication
        - TW_BASE_URL: Base URL for API endpoints (defaults to https://api.trustwise.ai)
    
    Example:
        >>> from trustwise.sdk.config import TrustwiseConfig
        >>> # Using environment variables
        >>> config = TrustwiseConfig()
        >>> # Using direct initialization
        >>> config = TrustwiseConfig(api_key="your-api-key", base_url="https://api.trustwise.ai")
    
    Raises:
        ValueError: If API key is missing or invalid, or if base URL is invalid
    """
    
    api_key: str = Field(
        default=None,
        description="API key for authentication"
    )
    
    base_url: str = Field(
        default_factory=lambda: os.getenv("TW_BASE_URL") or "https://api.trustwise.ai",
        description="Base URL for API endpoints"
    )
    
    def __init__(self, **data) -> None:
        # Check for API key in environment if not provided
        if "api_key" not in data:
            data["api_key"] = os.getenv("TW_API_KEY")
            
        # Validate API key before Pydantic initialization
        if not data.get("api_key"):
            raise ValueError("API key must be provided either directly or through TW_API_KEY environment variable")
            
        try:
            super().__init__(**data)
        except ValidationError as e:
            # Convert Pydantic validation errors to our own ValueError
            if "api_key" in str(e):
                raise ValueError("API key must be a valid string") from e
            if "base_url" in str(e):
                raise ValueError("Base URL must be a valid string") from e
            raise ValueError(f"Invalid configuration: {e!s}") from e
            
        self._validate_url()
        # Ensure base_url ends with a slash for consistent path joining
        if not self.base_url.endswith("/"):
            self.base_url = f"{self.base_url}/"
    
    def _validate_url(self) -> None:
        """Validate base URL format and scheme."""
        try:
            parsed = urlparse(self.base_url)
            if not all([parsed.scheme, parsed.netloc]):
                raise TrustwiseValidationError("Invalid base URL format: missing scheme or netloc.")
            if parsed.scheme not in ("http", "https"):
                raise TrustwiseValidationError(f"Invalid base URL scheme: '{parsed.scheme}'. Only 'http' and 'https' are allowed.")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid base URL: {e!s}") from e

    def get_performance_url(self, version: str) -> str:
        """Get performance API URL for specified version."""
        return urljoin(self.base_url, f"performance/{version}") 
    
    def get_metrics_url(self, version: str) -> str:
        """Get metrics API URL for specified version."""
        return urljoin(self.base_url, f"metrics/{version}")