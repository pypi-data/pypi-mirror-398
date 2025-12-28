"""BetterForecast model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .better_forecast_current_conditions import BetterForecastCurrentConditions
from .better_forecast_forecast import BetterForecastForecast
from .better_forecast_units import BetterForecastUnits
from .status import Status


class BetterForecast(Model):
    latitude: float | int | None = None  # float
    longitude: float | int | None = None  # float
    timezone: str | None = None  # string
    timezone_offset_minutes: float | int | None = None  # number
    location_name: str | None = None  # string
    current_conditions: BetterForecastCurrentConditions | None = None  # object
    forecast: BetterForecastForecast | None = None  # object
    status: Status | None = None  # object
    units: BetterForecastUnits | None = None  # object
    source_id_conditions: float | int | None = None  # number

    # Omitted from docs but present in API
    # station:

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = [
    "BetterForecast",
]
