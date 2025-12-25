"""
Custom exceptions for the Neuroute SDK.
"""


class NeurouteSDKError(Exception):
    """Base exception for all SDK errors."""
    pass


class QueryTooLongError(NeurouteSDKError):
    """Query exceeds 100 character limit."""
    pass


class RateLimitExceededError(NeurouteSDKError):
    """User has exceeded rate limit (1 query/hour)."""

    def __init__(self, retry_after_seconds: int):
        """
        Initialize rate limit error.

        Args:
            retry_after_seconds: Seconds until user can query again
        """
        self.retry_after_seconds = retry_after_seconds
        minutes = retry_after_seconds // 60
        super().__init__(
            f"Rate limit exceeded. Try again in {minutes} minutes "
            f"({retry_after_seconds} seconds)"
        )


class InvalidAPIKeyError(NeurouteSDKError):
    """API key is invalid or inactive."""

    def __init__(self):
        super().__init__("Invalid or inactive API key")


class ServiceDisabledError(NeurouteSDKError):
    """Service is temporarily disabled."""

    def __init__(self):
        super().__init__("Service is temporarily disabled. Contact admin.")
