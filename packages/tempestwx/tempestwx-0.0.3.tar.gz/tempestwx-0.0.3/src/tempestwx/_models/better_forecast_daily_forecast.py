"""BetterForecastDailyForecast model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .units_default import Conditions, Icon, PrecipIcon, PrecipType


class BetterForecastDailyForecast(Model):
    day_start_local: float | int | None = None  # number
    day_num: float | int | None = None  # number
    month_num: float | int | None = None  # number
    conditions: Conditions | None = None  # string enum
    icon: Icon | None = None  # string enum
    sunrise: float | int | None = None  # number
    sunset: float | int | None = None  # number
    air_temp_high: float | int | None = None  # number
    air_temp_low: float | int | None = None  # number
    air_temp_high_color: str | None = None  # string
    air_temp_low_color: str | None = None  # string
    precip_probability: float | int | None = None
    precip_icon: PrecipIcon | None = None  # string enum
    precip_type: PrecipType | None = None  # string enum

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = [
    "BetterForecastDailyForecast",
]
