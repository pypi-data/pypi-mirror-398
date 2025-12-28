"""Transport wrapper base class.

This module provides TransportWrapper, a base class for objects that delegate
to an underlying Transport. It implements the Transport interface by forwarding
all operations to the wrapped transport.

Useful for:
- Building decorator-style transport extensions
- Adding middleware-like behavior (logging, caching, etc.)
- Creating client classes that manage transport instances
"""

from __future__ import annotations

from collections.abc import Coroutine

from .base import Transport
from .concrete import SyncTransport


class TransportWrapper(Transport):
    """Base class for transports that wrap/delegate to another transport.

    Args:
        transport: Request transport, :class:`SyncTransport` if not specified.
    """

    def __init__(self, transport: Transport | None) -> None:
        self.transport = transport or SyncTransport()

    @property
    def is_async(self) -> bool:
        """Transport asynchronicity, delegated to the underlying transport."""
        return self.transport.is_async

    def close(self) -> None | Coroutine[None, None, None]:
        """Close the underlying transport.

        The return type depends on the wrapped transport:
        - For synchronous transports: returns None immediately
        - For asynchronous transports: returns a coroutine to await

        To close synchronous transports, call :meth:`close`.
        To close asynchronous transports, await :meth:`close`.

        Example:
            >>> # Synchronous
            >>> wrapper.close()
            >>> # Asynchronous
            >>> await wrapper.close()
        """
        return self.transport.close()
