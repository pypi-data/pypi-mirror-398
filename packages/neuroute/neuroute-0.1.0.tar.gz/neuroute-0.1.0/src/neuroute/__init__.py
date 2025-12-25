"""
Claude SDK - Private beta Python SDK for rate-limited Claude API access.

This SDK requires a valid API key distributed by the service administrator.
"""

from .client import ClaudeClient
from .exceptions import (
    ClaudeSDKError,
    QueryTooLongError,
    RateLimitExceededError,
    InvalidAPIKeyError,
    ServiceDisabledError,
)

__version__ = "0.1.0"
__all__ = [
    "ClaudeClient",
    "ClaudeSDKError",
    "QueryTooLongError",
    "RateLimitExceededError",
    "InvalidAPIKeyError",
    "ServiceDisabledError",
]
