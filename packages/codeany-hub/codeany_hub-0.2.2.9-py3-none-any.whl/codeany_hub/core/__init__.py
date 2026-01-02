"""Core infrastructure for the Codeany Hub SDK."""

from .auth import AuthStrategy, HubLoginAuth, OAuthBridge, SimpleJwtAuth
from .errors import (
    ApiError,
    AuthError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    raise_for_response,
)
from .pagination import Page, iter_pages
from .poller import Poller
from .tokens import FileTokenStore, InMemoryTokenStore, JwtPair, TokenStore
from .retry import (
    DEFAULT_RETRY_EXCEPTIONS,
    DEFAULT_RETRY_METHODS,
    DEFAULT_RETRY_STATUSES,
    ExponentialBackoffRetry,
    RetryPolicy,
)
from .transport import AsyncTransport, RequestContext, ResponseContext, Transport, TransportHooks
from .versioning import CapabilityProbe

__all__ = [
    "ApiError",
    "AuthError",
    "AuthStrategy",
    "CapabilityProbe",
    "HubLoginAuth",
    "FileTokenStore",
    "InMemoryTokenStore",
    "JwtPair",
    "NotFoundError",
    "OAuthBridge",
    "Page",
    "Poller",
    "RateLimitError",
    "RequestContext",
    "ResponseContext",
    "RetryPolicy",
    "ExponentialBackoffRetry",
    "DEFAULT_RETRY_STATUSES",
    "DEFAULT_RETRY_METHODS",
    "DEFAULT_RETRY_EXCEPTIONS",
    "SimpleJwtAuth",
    "TokenStore",
    "TransportHooks",
    "AsyncTransport",
    "Transport",
    "ValidationError",
    "iter_pages",
    "raise_for_response",
]
