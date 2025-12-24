"""
Client for the Trustwise API.

This client provides methods to interact with Trustwise's safety and
alignment metrics.
"""

import json
from typing import Any

import requests

from trustwise.sdk.config import TrustwiseConfig
from trustwise.sdk.exceptions import (
    make_status_error_from_response,
)
from trustwise.sdk.logging import logger


class TrustwiseClient:
    """Client for the Trustwise API."""

    def __init__(self, config: TrustwiseConfig) -> None:
        """
        Initialize the Trustwise client.

        Args:
            config: Trustwise configuration object.
        """
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        logger.debug("Initialized Trustwise client with base URL: %s", config.base_url)

    def _post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """
        Make a POST request to the Trustwise API.

        Args:
            endpoint: The API endpoint URL.
            data: The request payload.

        Returns:
            The API response as a dictionary.

        Raises:
            requests.HTTPError: If the request fails with a non-422 status code.
            Exception: If the request fails for other reasons.
        """
        logger.debug("Making POST request to %s", endpoint)
        logger.debug("Request headers: %s", {k: "***" if k == "Authorization" else v for k, v in self.headers.items()})
        logger.debug("Request data: %s", json.dumps(data))

        try:
            response = requests.post(
                endpoint,
                json=data,
                headers=self._get_headers(),
                timeout=30  # Add timeout to prevent hanging
            )
            logger.debug("Response headers: %s", dict(response.headers))
            if response.status_code != 200:
                raise make_status_error_from_response(response)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e!s}") from e

    def _get_headers(self) -> dict[str, str]:
        return self.headers 