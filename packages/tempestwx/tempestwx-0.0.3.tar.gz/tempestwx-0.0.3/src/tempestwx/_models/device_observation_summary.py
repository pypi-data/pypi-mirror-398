"""StationObservation model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model


class DeviceObservationSummary(Model):
    pressure_trend: str | None = None  # string
    strike_count_1h: float | int | None = None  # number
    strike_count_3h: float | int | None = None  # number
    precip_total_1h: float | int | None = None  # number
    strike_last_dist: float | int | None = None  # number
    strike_last_epoch: float | int | None = None  # number
    precip_accum_local_yesterday: float | int | None = None  # number
    precip_accum_local_yesterday_final: float | int | None = None  # number
    precip_analysis_type_yesterday: float | int | None = None  # number
    feels_like: float | int | None = None  # number
    heat_index: float | int | None = None  # number
    wind_chill: float | int | None = None  # number
    dew_point: float | int | None = None  # number
    wet_bulb_temperature: float | int | None = None  # number
    wet_bulb_globe_temperature: float | int | None = None  # number
    air_density: float | int | None = None  # number
    delta_t: float | int | None = None  # numberv
    precip_minutes_local_day: float | int | None = None  # number
    precip_minutes_local_yesterday: float | int | None = None  # number

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["DeviceObservationSummary"]
