"""Core HTTP abstractions and interfaces.

This module defines the foundational types for the HTTP transport layer:

- Request: Dataclass encapsulating HTTP request parameters
- Response: Dataclass encapsulating HTTP response data
- Transport: Abstract interface for sending requests (sync or async)

These abstractions allow the SDK to remain independent of specific HTTP
libraries while supporting both synchronous and asynchronous operation modes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any


@dataclass
class Request:
    """Wrapper for parameters of a HTTP request.

    Encapsulates all information needed to execute an HTTP request,
    including method, URL, headers, query parameters, and body content.
    Supports multiple body formats (data, json, content).

    Attributes:
        method: HTTP method (GET, POST, PUT, DELETE, etc.).
        url: Target URL (may be relative or absolute).
        params: Optional query string parameters.
        headers: Optional HTTP headers.
        data: Optional form data body.
        json: Optional JSON body (mutually exclusive with data/content).
        content: Optional raw string body.
    """

    method: str
    url: str
    params: dict[str, Any] | None = None
    headers: dict[str, str] | None = None
    data: dict[str, Any] | None = None
    json: dict[str, Any] | None = None
    content: str | None = None


@dataclass
class Response:
    """Wrapper for result of a HTTP request.

    Encapsulates the essential components of an HTTP response.
    Content is pre-parsed as JSON (or None if not JSON or parsing failed).

    Attributes:
        url: Final URL after any redirects.
        headers: Response HTTP headers.
        status_code: HTTP status code (200, 404, 500, etc.).
        content: Parsed JSON content as a dictionary, or None.
    """

    url: str
    headers: dict[str, str]
    status_code: int
    content: dict[str, Any] | None


class Transport(ABC):
    """Transport interface for sending HTTP requests.

    Abstract base class defining the contract for HTTP transports.
    Implementations must provide synchronous or asynchronous request
    sending, identified via the is_async property.

    Subclasses:
        SyncTransport: Synchronous implementation using httpx.Client
        AsyncTransport: Asynchronous implementation using httpx.AsyncClient
    """

    def __repr__(self) -> str:
        return type(self).__name__ + "()"

    @abstractmethod
    def send(self, request: Request) -> Response | Coroutine[None, None, Response]:
        """Send a request and return response (sync) or response coroutine (async).

        Args:
            request: The HTTP request to send.

        Returns:
            Response for synchronous transports, or a coroutine that yields
            Response for asynchronous transports.
        """

    @property
    @abstractmethod
    def is_async(self) -> bool:
        """Transport asynchronicity mode.

        Returns:
            True for asynchronous transports, False for synchronous.
        """

    @abstractmethod
    def close(self) -> None | Coroutine[None, None, None]:
        """Close underlying client.

        Returns:
            None for synchronous transports, coroutine for asynchronous.
        """
