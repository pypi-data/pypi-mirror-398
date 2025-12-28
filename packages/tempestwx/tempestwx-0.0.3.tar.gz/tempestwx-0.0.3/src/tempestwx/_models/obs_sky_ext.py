"""SKY Daily Observation (obs_sky_ext) array model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class SkyDailyObservation(Model):
    """Structured representation of an obs_sky_ext array entry.

    Indices (0..21):
    0: timestamp (epoch s UTC)
    1: average_illuminance (lux)
    2: average_uv (index)
    3: local_day_rain_accumulation (mm)
    4: wind_lull (m/s)
    5: average_wind_speed (m/s)
    6: wind_gust (m/s)
    7: average_wind_direction (deg)
    8: highest_illuminance (lux)
    9: lowest_illuminance (lux)
    10: highest_uv (index)
    11: lowest_uv (index)
    12: record_count
    13: average_solar_radiation (W/m^2)
    14: highest_solar_radiation (W/m^2)
    15: lowest_solar_radiation (W/m^2)
    16: battery (V)
    17: local_day_nearcast_rain_accumulation (mm)
    18: precipitation_analysis_type (0 none, 1 on, 2 off)
    19: local_day_precipitation_minutes (minutes)
    20: wind_sample_interval (seconds)
    21: precipitation_type (0 none, 1 rain, 2 hail, 3 rain+hail)
    21: local_day_nearcast_precipitation_minutes (minutes)
        Note: Docs show duplicate index 21; keeping the final field
        as an optional extra element if present.
    """

    timestamp: Numeric = None
    average_illuminance: Numeric = None
    average_uv: Numeric = None
    local_day_rain_accumulation: Numeric = None
    wind_lull: Numeric = None
    average_wind_speed: Numeric = None
    wind_gust: Numeric = None
    average_wind_direction: Numeric = None
    highest_illuminance: Numeric = None
    lowest_illuminance: Numeric = None
    highest_uv: Numeric = None
    lowest_uv: Numeric = None
    record_count: Numeric = None
    average_solar_radiation: Numeric = None
    highest_solar_radiation: Numeric = None
    lowest_solar_radiation: Numeric = None
    battery: Numeric = None
    local_day_nearcast_rain_accumulation: Numeric = None
    precipitation_analysis_type: int | None = None
    local_day_precipitation_minutes: Numeric = None
    wind_sample_interval: Numeric = None
    precipitation_type: int | None = None
    local_day_nearcast_precipitation_minutes: Numeric = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> SkyDailyObservation:
        """Convert API array format to structured model.

        Args:
            array: Raw array with 22-23 daily observation values.

        Returns:
            Structured SkyDailyObservation instance.
        """
        # The docs list duplicate index 21. We treat final length as
        # 22 values (0..21) and map nearcast precipitation minutes
        # to the last element if present.
        padded = list(array) + [None] * (22 - len(array))
        return cls(
            timestamp=padded[0],
            average_illuminance=padded[1],
            average_uv=padded[2],
            local_day_rain_accumulation=padded[3],
            wind_lull=padded[4],
            average_wind_speed=padded[5],
            wind_gust=padded[6],
            average_wind_direction=padded[7],
            highest_illuminance=padded[8],
            lowest_illuminance=padded[9],
            highest_uv=padded[10],
            lowest_uv=padded[11],
            record_count=padded[12],
            average_solar_radiation=padded[13],
            highest_solar_radiation=padded[14],
            lowest_solar_radiation=padded[15],
            battery=padded[16],
            local_day_nearcast_rain_accumulation=padded[17],
            precipitation_type=padded[21],
            local_day_nearcast_precipitation_minutes=(
                array[22] if len(array) > 22 else None  # noqa: PLR2004
            ),
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with 22-23 daily observation values in API order.
        """
        # Return up to 23 elements including optional nearcast
        # precipitation minutes at the end
        base = [
            self.timestamp,
            self.average_illuminance,
            self.average_uv,
            self.local_day_rain_accumulation,
            self.wind_lull,
            self.average_wind_speed,
            self.wind_gust,
            self.average_wind_direction,
            self.highest_illuminance,
            self.lowest_illuminance,
            self.highest_uv,
            self.lowest_uv,
            self.record_count,
            self.average_solar_radiation,
            self.highest_solar_radiation,
            self.lowest_solar_radiation,
            self.battery,
            self.local_day_nearcast_rain_accumulation,
            self.precipitation_analysis_type,
            self.local_day_precipitation_minutes,
            self.wind_sample_interval,
            self.precipitation_type,
        ]
        # Append the optional final field if present
        base.append(self.local_day_nearcast_precipitation_minutes)
        return base

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["SkyDailyObservation"]
