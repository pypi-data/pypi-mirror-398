"""BetterForecastHourlyForecast model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .units_default import Conditions, Icon, PrecipIcon, PrecipType


class BetterForecastHourlyForecast(Model):
    time: float | int | None = None  # number
    conditions: Conditions | None = None  # string enum
    icon: Icon | None = None  # string enum
    air_temperature: float | int | None = None  # number
    sea_level_pressure: float | int | None = None  # float
    relative_humidity: float | int | None = None  # number
    precip: float | int | None = None  # float
    precip_probability: float | int | None = None  # number
    precip_icon: PrecipIcon | None = None  # string enum
    wind_avg: float | int | None = None  # number
    wind_avg_color: str | None = None  # string
    wind_direction: float | int | None = None  # number
    wind_direction_cardinal: str | None = None  # string
    wind_direction_icon: str | None = None  # string
    wind_gust: float | int | None = None  # number
    wind_gust_color: str | None = None  # string
    uv: float | int | None = None  # number
    feels_like: float | int | None = None  # number
    local_hour: float | int | None = None  # number
    local_day: float | int | None = None  # number

    # Omitted from docs but present in API
    station_pressure: float | int | None = None  # float
    precip_type: PrecipType | None = None  # string

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["BetterForecastHourlyForecast"]
