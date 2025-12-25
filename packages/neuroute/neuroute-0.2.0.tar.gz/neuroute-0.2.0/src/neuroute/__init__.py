"""
Neuroute SDK - Private beta Python SDK for rate-limited AI API access.

This SDK requires a valid API key distributed by the service administrator.
"""

from .client import NeurouteClient
from .exceptions import (
    NeurouteSDKError,
    QueryTooLongError,
    RateLimitExceededError,
    InvalidAPIKeyError,
    ServiceDisabledError,
)

__version__ = "0.2.0"
__all__ = [
    "NeurouteClient",
    "NeurouteSDKError",
    "QueryTooLongError",
    "RateLimitExceededError",
    "InvalidAPIKeyError",
    "ServiceDisabledError",
]
