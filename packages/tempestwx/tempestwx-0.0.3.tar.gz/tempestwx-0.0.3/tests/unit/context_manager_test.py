"""Tests for client context manager and resource cleanup."""

import asyncio

import pytest

from tempestwx import Tempest
from tempestwx._http import AsyncTransport, SyncTransport


def test_sync_context_manager_creates_and_owns_transport() -> None:
    """Test that sync context manager works and owns default transport."""
    with Tempest() as client:
        assert client is not None
        assert client._owns_transport is True
        assert client.transport.is_async is False


@pytest.mark.asyncio
async def test_async_context_manager_creates_and_owns_transport() -> None:
    """Test that async context manager works and owns default transport."""
    async with Tempest(asynchronous=True) as client:
        assert client is not None
        assert client._owns_transport is True
        assert client.transport.is_async is True


def test_manual_close_works() -> None:
    """Test that explicit close() method works."""
    client = Tempest()
    assert client._owns_transport is True
    client.close()  # Should not raise


@pytest.mark.asyncio
async def test_manual_aclose_works() -> None:
    """Test that explicit aclose() method works."""
    client = Tempest(asynchronous=True)
    assert client._owns_transport is True
    await client.aclose()  # Should not raise


def test_user_provided_transport_not_owned() -> None:
    """Test that user-provided transports are not owned by client."""
    transport = SyncTransport()
    try:
        client = Tempest(transport=transport)
        assert client._owns_transport is False
        client.close()  # Should not close user's transport
    finally:
        transport.close()  # User is responsible


@pytest.mark.asyncio
async def test_user_provided_async_transport_not_owned() -> None:
    """Test that user-provided async transports are not owned by client."""
    transport = AsyncTransport()
    try:
        client = Tempest(transport=transport)
        assert client._owns_transport is False
        await client.aclose()  # Should not close user's transport
    finally:
        await transport.close()  # User is responsible


def test_transport_replaced_is_owned() -> None:
    """Test that when transport is replaced due to conflict, new one is owned."""
    # Provide async transport but request sync
    async_transport = AsyncTransport()
    try:
        with pytest.warns(match="A new SyncTransport was instantiated"):
            client = Tempest(transport=async_transport, asynchronous=False)

        # Client should own the new transport it created
        assert client._owns_transport is True
        assert client.transport.is_async is False
        assert client.transport is not async_transport

        client.close()
    finally:
        # Clean up the user's original async transport (need to use asyncio)
        asyncio.run(async_transport.close())
