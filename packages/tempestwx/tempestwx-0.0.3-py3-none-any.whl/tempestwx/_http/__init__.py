"""HTTP transport layer for the Tempest SDK.

This package provides the low-level HTTP request/response infrastructure used
by the Tempest API client. It abstracts over httpx to provide:

- Request/Response dataclasses for structured HTTP operations
- Transport interface supporting both sync and async operation modes
- Concrete sync/async transport implementations using httpx
- HTTP error hierarchy with specific exception types for status codes
- Client base class with transport management
- Decorator utilities for request processing

The transport layer is designed to be swappable, allowing custom implementations
for testing, caching, or alternative HTTP libraries.

Internal API:
    Most components here are internal. Users should interact with the high-level
    ``Tempest`` client class instead.
"""

from .base import Request, Response, Transport
from .client import Client, TransportConflictWarning
from .concrete import AsyncTransport, SyncTransport
from .error import (
    BadGatewayError,
    BadRequestError,
    ClientError,
    ForbiddenError,
    HTTPError,
    InternalServerError,
    NotFoundError,
    ServerError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnauthorisedError,
)
from .wrapper import TransportWrapper

__all__ = [
    # Core types
    "Request",
    "Response",
    "Transport",
    # Client
    "Client",
    "TransportConflictWarning",
    # Concrete transports
    "AsyncTransport",
    "SyncTransport",
    # Error hierarchy
    "BadGatewayError",
    "BadRequestError",
    "ClientError",
    "ForbiddenError",
    "HTTPError",
    "InternalServerError",
    "NotFoundError",
    "ServerError",
    "ServiceUnavailableError",
    "TooManyRequestsError",
    "UnauthorisedError",
    # Wrappers
    "TransportWrapper",
]
