"""Base HTTP client with transport management.

This module provides the Client base class that manages HTTP transport selection
and synchronicity requirements. It handles:

- Automatic transport instantiation (sync vs async)
- Transport conflict resolution and warnings
- Request sending delegation to the underlying transport
- Advanced decorator for request processing (send_and_process)

The send_and_process decorator is the core of the request execution pipeline,
handling both sync and async paths while applying post-processing functions
to responses.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar, TypeVarTuple, cast
from warnings import warn

from .base import Request, Response, Transport
from .concrete import AsyncTransport, SyncTransport
from .error import UnauthorisedError
from .wrapper import TransportWrapper

R = TypeVar("R")
P = ParamSpec("P")
Ts = TypeVarTuple("Ts")


class TransportConflictWarning(RuntimeWarning):
    """Transport arguments to a client are in conflict.

    Raised when both a transport instance and an asynchronous flag are provided
    to the client, but they disagree on synchronicity. The client will create
    a new transport matching the requested asynchronicity.
    """


class Client(TransportWrapper):
    """Base class for API clients with transport management.

    Extends TransportWrapper to add intelligent transport selection based on
    the asynchronous parameter. Handles conflicts between provided transport
    and requested synchronicity, automatically instantiating the correct
    transport type when needed.

    Supports both context manager and manual close patterns. The client
    automatically closes transports it creates (when transport=None), but
    leaves user-provided transports for the user to manage.

    Args:
        transport: Request transport. If not specified, a :class:`SyncTransport`
            is used.
        asynchronous: Synchronicity requirement. If specified, overrides the
            passed transport if they are in conflict and instantiates a transport
            of the requested type.

    Warns:
        TransportConflictWarning: When transport and asynchronous parameters
            conflict, resulting in a new transport being created.

    Examples:
        Synchronous with context manager:

            with Client(transport=None) as client:
                response = client.send(request)

        Asynchronous with context manager:

            async with Client(transport=None, asynchronous=True) as client:
                response = await client.send(request)

        Manual close:

            client = Client(transport=None)
            try:
                response = client.send(request)
            finally:
                client.close()
    """

    def __init__(
        self, transport: Transport | None, asynchronous: bool | None = None
    ) -> None:
        super().__init__(transport)

        # Track whether we own the transport (and should close it)
        self._owns_transport = transport is None

        if self.transport.is_async and asynchronous is False:
            self.transport = SyncTransport()
            self._owns_transport = True
        elif not self.transport.is_async and asynchronous is True:
            self.transport = AsyncTransport()
            self._owns_transport = True

        if transport is not None and self.transport.is_async != transport.is_async:
            msg = (
                f"{type(transport)} with is_async={transport.is_async} passed"
                f" but asynchronous={asynchronous}!"
                f"\nA new {type(self.transport).__name__} was instantiated."
            )
            warn(msg, TransportConflictWarning, stacklevel=3)
            self._owns_transport = True

    def send(self, request: Request) -> Response | Coroutine[None, None, Response]:
        """Send request with underlying transport.

        Args:
            request: The HTTP request to send.

        Returns:
            Response for synchronous clients, or a coroutine yielding Response
            for asynchronous clients.
        """
        return self.transport.send(request)

    def close(self) -> None:
        """Close the underlying transport.

        Only closes the transport if this client created it (owns it).
        User-provided transports are the user's responsibility to close.

        For asynchronous clients, use :meth:`aclose` instead.
        """
        if self._owns_transport and not self.transport.is_async:
            sync_transport = cast(SyncTransport, self.transport)
            sync_transport.close()

    async def aclose(self) -> None:
        """Close the underlying async transport.

        Only closes the transport if this client created it (owns it).
        User-provided transports are the user's responsibility to close.

        For synchronous clients, use :meth:`close` instead.
        """
        if self._owns_transport and self.transport.is_async:
            async_transport = cast(AsyncTransport, self.transport)
            await async_transport.close()

    def __enter__(self) -> Client:
        """Enter synchronous context manager.

        Returns:
            This client instance.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Exit synchronous context manager and close transport.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()

    async def __aenter__(self) -> Client:
        """Enter asynchronous context manager.

        Returns:
            This client instance.
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Exit asynchronous context manager and close transport.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        await self.aclose()


def send_and_process(
    post_func: Callable[[Request, Response, *Ts], R],
) -> Callable[
    [Callable[Concatenate[Transport, P], tuple[Request, tuple[*Ts]]]],
    Callable[Concatenate[Transport, P], R | Coroutine[None, None, R]],
]:
    """Decorate a Client function to send a request and process its content.

    This is the core decorator that powers the request execution pipeline.
    It transforms methods that return (Request, extra_params) tuples into
    full request executors that:

    1. Send the request via the transport layer
    2. Receive the response
    3. Apply the post-processing function to transform the response
    4. Return the processed result

    Handles both synchronous and asynchronous execution paths transparently
    based on the transport type.

    The first parameter of a decorated function must be the instance (self)
    of a :class:`Transport` (has :meth:`send` and :attr:`is_async`).
    The decorated function must return a tuple with two items:
    a :class:`Request` and a tuple with arguments to unpack to ``post_func``.
    The result of ``post_func`` is returned to the caller.

    Args:
        post_func: Function to call with the request, response, and any
            additional arguments. Typically handles error checking and
            response deserialization.

    Returns:
        A decorator that transforms request-building methods into full
        request execution methods.

    Example:
        >>> @send_and_process(lambda req, resp: resp.content)
        ... def get_data(self: Transport) -> dict:
        ...     return (Request(method="GET", url="/data"), ())
    """

    def decorator(
        function: Callable[Concatenate[Transport, P], tuple[Request, tuple[*Ts]]],
    ) -> Callable[Concatenate[Transport, P], R | Coroutine[None, None, R]]:
        def try_post_func(request: Request, response: Response, *params: *Ts) -> R:
            try:
                return post_func(request, response, *params)
            except UnauthorisedError:
                raise

        async def async_send(
            self: AsyncTransport, request: Request, params: tuple[*Ts]
        ) -> R:
            response = await self.send(request)
            return try_post_func(request, response, *params)

        @wraps(function)
        def wrapper(
            self: Transport, *args: P.args, **kwargs: P.kwargs
        ) -> R | Coroutine[None, None, R]:
            request, params = function(self, *args, **kwargs)

            if self.is_async:
                async_self = cast(AsyncTransport, self)
                return async_send(async_self, request, params)

            # Synchronous path: 'send' returns a Response immediately.
            sync_self = cast(SyncTransport, self)
            response = sync_self.send(request)
            return try_post_func(request, response, *params)

        return wrapper  # type: ignore[return-value]

    return decorator
