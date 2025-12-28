"""BetterForecastCurrentConditions model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .units_default import Conditions, Icon, PressureTrend


class BetterForecastCurrentConditions(Model):
    time: float | int | None = None  # number
    conditions: Conditions | None = None
    icon: Icon | None = None
    air_temperature: float | int | None = None  # number
    sea_level_pressure: float | int | None = None  # float
    station_pressure: float | int | None = None  # float
    pressure_trend: PressureTrend | None = None  # string enum
    relative_humidity: float | int | None = None  # number
    wind_avg: float | int | None = None  # number
    wind_direction: float | int | None = None  # number
    wind_direction_cardinal: str | None = None  # string
    wind_direction_icon: str | None = None  # string
    wind_gust: float | int | None = None  # number
    solar_radiation: float | int | None = None  # number
    uv: float | int | None = None  # number
    brightness: float | int | None = None  # number
    feels_like: float | int | None = None  # number
    dew_point: float | int | None = None  # number
    wet_bulb_temperature: float | int | None = None  # number
    wet_bulb_globe_temperature: float | int | None = None  # number
    delta_t: float | int | None = None  # number
    air_density: float | int | None = None  # float
    lightning_strike_count_last_1hr: float | int | None = None  # number
    lightning_strike_count_last_3hr: float | int | None = None  # number
    lightning_strike_last_distance: float | int | None = None  # number
    lightning_strike_last_distance_msg: str | None = None  # string
    lightning_strike_last_epoch: float | int | None = None  # number
    precip_accum_local_day: float | int | None = None  # float
    precip_accum_local_yesterday: float | int | None = None  # float
    precip_minutes_local_day: float | int | None = None  # number
    precip_minutes_local_yesterday: float | int | None = None  # number
    is_precip_local_day_rain_check: bool | None = None  # boolean
    is_precip_local_yesterday_rain_check: bool | None = None  # boolean

    # Omitted from docs but present in API
    precip_probability: float | int | None = None  # number

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = [
    "BetterForecastCurrentConditions",
]
