"""
Claude SDK Client - Main interface for querying Claude API.
"""

import requests
from typing import Optional

from .exceptions import (
    QueryTooLongError,
    RateLimitExceededError,
    InvalidAPIKeyError,
    ServiceDisabledError,
)


class ClaudeClient:
    """
    Client for interacting with the Claude SDK backend.

    This client provides rate-limited access to Claude AI via a backend service.

    Usage:
        >>> from neuroute import ClaudeClient
        >>> client = ClaudeClient(api_key="csk_your_api_key")
        >>> response = client.query("What is Python?")
        >>> print(response)

    Attributes:
        api_key: User's API key (required)
        backend_url: URL of the backend service
    """

    # Default backend URL (update after deployment)
    DEFAULT_BACKEND_URL = "https://ai-social-media-chat-agent-production.up.railway.app"

    def __init__(self, api_key: str, backend_url: Optional[str] = None):
        """
        Initialize the Claude client.

        Args:
            api_key: Your API key (starts with 'csk_')
            backend_url: Optional custom backend URL (uses default if not provided)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.backend_url = backend_url or self.DEFAULT_BACKEND_URL

    def query(self, prompt: str) -> str:
        """
        Send a query to Claude and return the text response.

        Args:
            prompt: User query (max 100 characters)

        Returns:
            str: Claude's response text

        Raises:
            QueryTooLongError: If prompt > 100 characters
            RateLimitExceededError: If user has queried within the last hour
            InvalidAPIKeyError: If API key is invalid or inactive
            ServiceDisabledError: If service is temporarily disabled
            requests.RequestException: For network errors

        Example:
            >>> client = ClaudeClient(api_key="csk_xxx")
            >>> response = client.query("Explain recursion briefly")
            >>> print(response)
        """
        # Client-side validation (UX only, server validates again)
        if len(prompt) > 100:
            raise QueryTooLongError(
                f"Query must be ≤100 chars (got {len(prompt)})"
            )

        # Send request to backend
        try:
            response = requests.post(
                f"{self.backend_url}/api/v1/query",
                headers={"X-API-Key": self.api_key},
                json={"prompt": prompt},
                timeout=30
            )

            # Handle error responses
            if response.status_code == 429:
                # Rate limit exceeded
                data = response.json()
                retry_after = data.get("retry_after_seconds", 3600)
                raise RateLimitExceededError(retry_after)

            elif response.status_code == 401:
                # Invalid API key
                raise InvalidAPIKeyError()

            elif response.status_code == 503:
                # Service disabled
                raise ServiceDisabledError()

            elif response.status_code == 400:
                # Bad request (query too long)
                raise QueryTooLongError()

            # Raise for other HTTP errors
            response.raise_for_status()

            # Return simple string response
            return response.json()["response"]

        except requests.RequestException as e:
            # Network or connection error
            if isinstance(e, (RateLimitExceededError, InvalidAPIKeyError,
                            ServiceDisabledError, QueryTooLongError)):
                raise
            raise RuntimeError(f"Failed to connect to backend: {str(e)}")

    def __repr__(self):
        """String representation of the client."""
        masked_key = f"{self.api_key[:10]}..." if len(self.api_key) > 10 else self.api_key
        return f"ClaudeClient(api_key={masked_key}, backend_url={self.backend_url})"
