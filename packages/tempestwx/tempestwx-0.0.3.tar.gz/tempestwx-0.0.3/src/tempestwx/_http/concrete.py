"""Concrete HTTP transport implementations using httpx.

This module provides synchronous and asynchronous transport implementations
that wrap httpx clients. Both transports:

- Convert Request dataclasses to httpx request parameters
- Execute HTTP requests via httpx.Client or httpx.AsyncClient
- Parse JSON responses automatically
- Wrap results in Response dataclasses

Note:
    When using the high-level :class:`tempestwx.Tempest` client, transports are
    managed automatically via context managers or explicit close() calls. Direct
    use of these transport classes requires manual resource management.

Warning:
    If instantiating these transports directly (not through the Tempest client),
    the underlying httpx clients must be closed manually via transport.close()
    or await transport.aclose() to prevent resource leaks.
"""

from __future__ import annotations

from typing import Any, cast

from httpx import AsyncClient, Client
from httpx import Response as HTTPXResponse

from .base import Request, Response, Transport


def try_parse_json(response: HTTPXResponse) -> dict[str, Any] | None:
    """Parse JSON content from httpx response, returning None on failure.

    Args:
        response: The httpx Response object.

    Returns:
        Parsed JSON as a dictionary, or None if response is not JSON or
        parsing fails.
    """
    try:
        return cast(dict[str, Any], response.json())
    except ValueError:
        return None


class SyncTransport(Transport):
    """Send requests synchronously.

    Note:
        When used via :class:`tempestwx.Tempest`, the transport is closed
        automatically. Direct instantiation requires manual cleanup.

    Warning:
        If instantiating directly, the underlying httpx client is *not* closed
        automatically. Use :code:`transport.close()` to close it, particularly
        if multiple transports are instantiated.

    Args:
        client: :class:`httpx.Client` to use when sending requests.
    """

    def __init__(self, client: Client | None = None) -> None:
        self.client = client or Client()

    def send(self, request: Request) -> Response:
        """Send request synchronously with :class:`httpx.Client`.

        Args:
            request: The request to send.

        Returns:
            Response with parsed JSON content.
        """
        response = self.client.request(
            method=request.method,
            url=request.url,
            params=request.params,
            headers=request.headers,
            data=request.data,
            json=request.json,
            content=request.content,
        )
        return Response(
            url=str(response.url),
            headers=dict(response.headers),
            status_code=response.status_code,
            content=try_parse_json(response),
        )

    @property
    def is_async(self) -> bool:
        """Transport asynchronicity, always :class:`False`."""
        return False

    def close(self) -> None:
        """Close the underlying synchronous client."""
        return self.client.close()


class AsyncTransport(Transport):
    """Send requests asynchronously.

    Note:
        When used via :class:`tempestwx.Tempest`, the transport is closed
        automatically. Direct instantiation requires manual cleanup.

    Warning:
        If instantiating directly, the underlying httpx client is **not** closed
        automatically. Use :code:`await transport.aclose()` to close it,
        particularly if multiple transports are instantiated.

    Args:
        client: :class:`httpx.AsyncClient` to use when sending requests.
    """

    def __init__(self, client: AsyncClient | None = None) -> None:
        self.client = client or AsyncClient()

    async def send(self, request: Request) -> Response:
        """Send request asynchronously with :class:`httpx.AsyncClient`.

        Args:
            request: The request to send.

        Returns:
            Response with parsed JSON content.
        """
        response = await self.client.request(
            method=request.method,
            url=request.url,
            params=request.params,
            headers=request.headers,
            data=request.data,
            json=request.json,
            content=request.content,
        )
        return Response(
            url=str(response.url),
            headers=dict(response.headers),
            status_code=response.status_code,
            content=try_parse_json(response),
        )

    @property
    def is_async(self) -> bool:
        """Transport asynchronicity, always :class:`True`."""
        return True

    async def close(self) -> None:
        """Close the underlying asynchronous client."""
        return await self.client.aclose()
