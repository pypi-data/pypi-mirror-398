"""Main Tempest Weather API client.

This module provides the primary ``Tempest`` client class that serves as the
unified interface for accessing all Tempest Weather API endpoints. It inherits
from multiple API endpoint mixins to provide a comprehensive set of methods for:

- Better Forecast: AI-enhanced weather forecasts
- Observations: Historical and real-time weather data
- Stations: Station metadata and device information
- Stats: Statistical summaries and aggregations

The client handles authentication, request/response cycles, error handling,
and response deserialization automatically. It supports both synchronous and
asynchronous operation modes.

Resource Management:
    The client supports both context manager (recommended) and explicit close
    patterns for proper resource cleanup.

    Synchronous context manager (recommended):

        with Tempest() as client:
            stations = client.stations()
            forecast = client.better_forecast(station_id=12345)

    Asynchronous context manager:

        async with Tempest(asynchronous=True) as client:
            stations = await client.stations()
            forecast = await client.better_forecast(station_id=12345)

    Manual close (when needed):

        client = Tempest()
        try:
            stations = client.stations()
        finally:
            client.close()

    Long-lived client (no explicit close needed):

        # For application-lifetime singletons
        app.weather_client = Tempest()

Example:
    >>> from tempestwx import Tempest
    >>> with Tempest() as client:  # Uses TEMPEST_ACCESS_TOKEN from environment
    ...     stations = client.stations()
    ...     forecast = client.better_forecast(station_id=12345)
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from tempestwx._http import Transport
from tempestwx.settings import Settings
from tempestwx.settings_loader import load_settings

from .api import (
    TempestBetterForecast,
    TempestObservations,
    TempestStations,
    TempestStats,
)


class Tempest(
    TempestBetterForecast,
    TempestObservations,
    TempestStations,
    TempestStats,
):
    """Tempest Weather API client.

    Unified client providing access to all Tempest Weather API endpoints through
    a single interface. Combines forecast, observation, station, and statistics
    capabilities via multiple inheritance from specialized endpoint classes.

    The client automatically handles:
    - Authentication via bearer tokens
    - Environment-based configuration (TEMPEST_ACCESS_TOKEN, config.json, .env)
    - Request construction and URL building
    - Error handling and exception raising
    - Response deserialization to Pydantic models
    - Resource cleanup (httpx client connections)

    Supports both synchronous and asynchronous operation modes depending on the
    transport implementation provided.

    Resource Management:
        The client implements context manager protocols for automatic cleanup.
        When using default transports (transport=None), the client will
        automatically close connections when exiting a context or when close()
        is called. User-provided transports remain the user's responsibility.

    Examples:
        Context manager (recommended):

            with Tempest() as client:
                stations = client.stations()

        Async context manager:

            async with Tempest(asynchronous=True) as client:
                stations = await client.stations()

        Manual close:

            client = Tempest()
            try:
                stations = client.stations()
            finally:
                client.close()

        Custom transport (user manages lifecycle):

            from tempestwx._http import SyncTransport
            transport = SyncTransport()
            try:
                client = Tempest(transport=transport)
                stations = client.stations()
            finally:
                transport.close()  # User's responsibility
    """

    def __init__(
        self,
        token: str | None = None,
        transport: Transport | None = None,
        asynchronous: bool | None = None,
        settings: Settings | None = None,
    ) -> None:
        """Initialize Tempest client.

        Args:
            token: Access token. If not provided, falls back to
                `settings.token` or the value resolved by `load_settings()` which
                reads TEMPEST_ACCESS_TOKEN from the environment (with .env support
                when python-dotenv is installed).
            transport: Custom HTTP transport implementation.
            asynchronous: Whether to use async/await pattern.
            settings: Preconstructed settings to use (overrides API URI/units/token
                resolution via `load_settings()` if provided). Note: token in
                settings typically comes from TEMPEST_ACCESS_TOKEN; config.json does
                not store tokens.
        """
        if token is None:
            base_settings = settings or load_settings()
            resolved_token = base_settings.token
            settings = base_settings
        else:
            resolved_token = token
        super().__init__(
            token=resolved_token,
            transport=transport,
            asynchronous=asynchronous,
            settings=settings,
        )

    @contextmanager
    def token_as(self, token: str) -> Generator[Tempest]:
        """Temporarily override the access token within a context.

        Args:
            token: Temporary access token to use for API calls within this context.

        Yields:
            This client instance with the overridden token.

        Examples:
            >>> client = Tempest()  # Uses TEMPEST_ACCESS_TOKEN from env
            >>> with client.token_as("temporary_token"):
            ...     stations = client.get_stations()  # Uses temporary_token
            >>> # Back to original token
        """
        cv_token = self._token_cv.set(token)
        try:
            yield self
        finally:
            self._token_cv.reset(cv_token)
