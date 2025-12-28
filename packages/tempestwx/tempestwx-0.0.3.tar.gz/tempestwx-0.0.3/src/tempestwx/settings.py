"""Configuration settings and overrides for the Tempest SDK.

This module defines a structured, immutable configuration object used by
the client to avoid reliance on scattered globals. Resolution of values
from files and environment is handled externally (see ``settings_loader.py``).

The goal is to keep :class:`Settings` immutable so that a single
instance can be safely shared across threads and async contexts.
"""

from __future__ import annotations

from functools import cached_property

from pydantic import BaseModel, Field

from ._models.units_default import (
    Bucket,
    UnitsBrightness,
    UnitsDefault,
    UnitsDistance,
    UnitsPrecip,
    UnitsPressure,
    UnitsSolarRadiation,
    UnitsTemp,
    UnitsWind,
)

_DEFAULT_API_URI = "https://swd.weatherflow.com/swd/rest/"


class UnitsOverrides(BaseModel):
    """Partial override fields for units.

    Only supply the fields you want to change relative to the base
    UnitsDefault. The `apply` method returns a new UnitsDefault instance
    with modifications.
    """

    temp: UnitsTemp | None = None
    wind: UnitsWind | None = None
    pressure: UnitsPressure | None = None
    precip: UnitsPrecip | None = None
    distance: UnitsDistance | None = None
    brightness: UnitsBrightness | None = None
    solar_radiation: UnitsSolarRadiation | None = None
    bucket: Bucket | None = None

    def apply(self, base: UnitsDefault) -> UnitsDefault:
        """Return a new UnitsDefault with these overrides applied.

        Only fields set on this overrides object are changed; all others
        inherit from the provided ``base``.

        Args:
            base: The base UnitsDefault to start from.

        Returns:
            New UnitsDefault instance with selective overrides applied.

        Example:
            >>> base_units = UnitsDefault()
            >>> overrides = UnitsOverrides(temp=UnitsTemp.FAHRENHEIT)
            >>> new_units = overrides.apply(base_units)
            >>> # new_units has Fahrenheit temp, all other units from base
        """
        return UnitsDefault(
            units_temp=self.temp or base.units_temp,
            units_pressure=self.pressure or base.units_pressure,
            units_wind=self.wind or base.units_wind,
            units_distance=self.distance or base.units_distance,
            units_brightness=self.brightness or base.units_brightness,
            units_solar_radiation=(self.solar_radiation or base.units_solar_radiation),
            units_precip=self.precip or base.units_precip,
            bucket=self.bucket or base.bucket,
        )


class Settings(BaseModel):
    """Immutable configuration for a Tempest client instance.

    Provides structured, frozen configuration combining:
    - API base URI for endpoint requests
    - Optional access token for authentication
    - Default unit preferences for weather data

    Immutability (via frozen=True) ensures thread-safety and prevents
    accidental modification. Use with_overrides() to create derived
    instances with changed values.

    Attributes:
        api_uri: Base URL for Tempest API endpoints. Defaults to the
            official Tempest Weather API.
        token: Optional bearer token for API authentication. Typically
            set from TEMPEST_ACCESS_TOKEN environment variable.
        units: Default unit preferences for temperature, pressure, wind,
            distance, precipitation, brightness, and solar radiation.
    """

    api_uri: str = Field(default=_DEFAULT_API_URI)
    token: str | None = None
    units: UnitsDefault = Field(default_factory=UnitsDefault)

    model_config = {
        "frozen": True,
        "extra": "ignore",
        "str_strip_whitespace": True,
    }

    def with_overrides(
        self,
        *,
        token: str | None = None,
        api_uri: str | None = None,
        units: UnitsDefault | None = None,
        units_overrides: UnitsOverrides | None = None,
    ) -> Settings:
        """Return a new Settings with selected fields overridden.

        Creates a new immutable Settings instance by copying this instance
        and applying specified overrides. Useful for creating per-request
        or per-context configuration variants without mutating shared state.

        Args:
            token: If provided, overrides the current token. If omitted, the
                existing token is preserved.
            api_uri: If provided, overrides the current API base URI. If omitted,
                the existing URI is preserved.
            units: If provided, replaces the current units entirely.
            units_overrides: If provided (and ``units`` is not), applies only those unit
                fields set on the overrides object.

        Returns:
            A new immutable Settings instance reflecting the requested changes.

        Example:
            >>> base = Settings(token="base_token")
            >>> temp_settings = base.with_overrides(token="temp_token")
            >>> # base still has "base_token", temp_settings has "temp_token"
        """
        new_units = units or (
            units_overrides.apply(self.units) if units_overrides else self.units
        )
        return Settings(
            api_uri=api_uri or self.api_uri,
            token=self.token if token is None else token,
            units=new_units,
        )

    @cached_property
    def api_uri_normalized(self) -> str:
        """Return the API base URI guaranteed to end with a single slash.

        Normalizes the configured api_uri by:
        1. Removing any trailing slashes
        2. Adding exactly one trailing slash

        This ensures consistent URL joining behavior when building endpoint
        URLs by concatenating the base with relative paths.

        Returns:
            Normalized API base URI ending with exactly one slash.

        Example:
            >>> s = Settings(api_uri="https://api.example.com")
            >>> s.api_uri_normalized
            'https://api.example.com/'
            >>> s2 = Settings(api_uri="https://api.example.com///")
            >>> s2.api_uri_normalized
            'https://api.example.com/'
        """
        return self.api_uri.rstrip("/") + "/"


__all__ = ["Settings", "UnitsOverrides"]
