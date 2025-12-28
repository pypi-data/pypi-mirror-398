"""StationObservationValues model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model, StrEnum


class ObservationType(StrEnum):
    obs_st = "obs_st"
    obs_sky = "obs_sky"
    obs_air = "obs_air"
    obs_st_ext = "obs_st_ext"
    obs_air_ext = "obs_air_ext"
    obs_sky_ext = "obs_sky_ext"
    evt_strike = "evt_strike"
    rapid_wind = "rapid_wind"


class Observation(Model):
    timestamp: float | int | None = None  # number
    air_temperature: float | int | None = None  # float
    barometric_pressure: float | int | None = None  # float
    station_pressure: float | int | None = None  # float
    sea_level_pressure: float | int | None = None  # float`
    relative_humidity: float | int | None = None  # number
    precip: float | int | None = None  # float
    precip_accum_last_1hr: float | int | None = None  # float
    precip_accum_local_day: float | int | None = None  # float
    precip_accum_local_day_final: float | int | None = None  # float
    precip_accum_local_yesterday: float | int | None = None  # float
    precip_accum_local_yesterday_final: float | int | None = None
    precip_minutes_local_day: float | int | None = None  # number
    precip_minutes_local_yesterday: float | int | None = None  # number
    precip_minutes_local_yesterday_final: float | int | None = None  # number
    precip_analysis_type_yesterday: float | int | None = None  # number
    wind_avg: float | int | None = None  # float
    wind_direction: float | int | None = None  # number
    wind_gust: float | int | None = None  # float
    wind_lull: float | int | None = None  # float
    solar_radiation: float | int | None = None  # number
    uv: float | int | None = None  # number
    brightness: float | int | None = None  # number
    lightning_strike_last_epoch: float | int | None = None  # number
    lightning_strike_last_distance: float | int | None = None  # number
    lightning_strike_count: float | int | None = None  # number
    lightning_strike_count_last_1hr: float | int | None = None  # number
    lightning_strike_count_last_3hr: float | int | None = None  # number
    feels_like: float | int | None = None  # float
    heat_index: float | int | None = None  # float
    wind_chill: float | int | None = None  # float
    dew_point: float | int | None = None  # float
    wet_bulb_temperature: float | int | None = None  # float
    wet_bulb_globe_temperature: float | int | None = None  # float
    delta_t: float | int | None = None  # float
    air_density: float | int | None = None  # float
    pressure_trend: str | None = None  # string

    # air_temperature_indoor: Optional[Union[float, int]] = None
    # barometric_pressure_indoor: Optional[Union[float, int]] = None
    # sea_level_pressure_indoor: Optional[Union[float, int]] = None
    # relative_humidity_indoor: Optional[Union[float, int]] = None
    # precip_indoor: Optional[Union[float, int]] = None
    # precip_accum_last_1hr_indoor: Optional[Union[float, int]] = None
    # wind_avg_indoor: Optional[Union[float, int]] = None
    # wind_direction_indoor: Optional[Union[float, int]] = None
    # wind_gust_indoor: Optional[Union[float, int]] = None
    # wind_lull_indoor: Optional[Union[float, int]] = None
    # solar_radiation_indoor: Optional[Union[float, int]] = None
    # uv_indoor: Optional[Union[float, int]] = None
    # brightness_indoor: Optional[Union[float, int]] = None
    # lightning_strike_last_epoch_indoor: Optional[Union[float, int]] = None
    # lightning_strike_last_distance_indoor: Optional[Union[float, int]] = None
    # lightning_strike_count_last_3hr_indoor: Optional[Union[float, int]] = None
    # feels_like_indoor: Optional[Union[float, int]] = None
    # heat_index_indoor: Optional[Union[float, int]] = None
    # wind_chill_indoor: Optional[Union[float, int]] = None
    # dew_point_indoor: Optional[Union[float, int]] = None
    # wet_bulb_temperature_indoor: Optional[Union[float, int]] = None
    # delta_t_indoor: Optional[Union[float, int]] = None
    # air_density_indoor: Optional[Union[float, int]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        strict=True,
    )


__all__ = ["Observation", "ObservationType"]
