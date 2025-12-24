"""
Canvelete Python SDK

Official Python client library for the Canvelete API.
Supports OAuth2 and API key authentication.
"""

__version__ = "2.0.0"

from .client import CanveleteClient
from .exceptions import (
    CanveleteError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    NotFoundError,
    ServerError,
)
from .utils import (
    with_retry,
    RetryConfig,
    validate_element,
    WebhookHandler,
)

__all__ = [
    "CanveleteClient",
    "CanveleteError",
    "AuthenticationError",
    "ValidationError",
    "RateLimitError",
    "NotFoundError",
    "ServerError",
    "with_retry",
    "RetryConfig",
    "validate_element",
    "WebhookHandler",
]
