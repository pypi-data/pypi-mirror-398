"""Tempest Daily Observation (obs_st_ext) array model.

A summary of observation data collected from midnight to midnight in the
station's local timezone.
"""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class TempestDailyObservation(Model):
    """Structured representation of an obs_st_ext array entry.

    Indices (0..33):
    0: timestamp (epoch s UTC)
    1: average_pressure (mb)
    2: highest_pressure (mb)
    3: lowest_pressure (mb)
    4: average_temperature (°C)
    5: lowest_temperature (°C)
    6: highest_temperature (°C)
    7: average_humidity (%)
    8: highest_humidity (%)
    9: lowest_humidity (%)
    10: average_illuminance (lux)
    11: highest_illuminance (lux)
    12: lowest_illuminance (lux)
    13: average_uv (index)
    14: highest_uv (index)
    15: lowest_uv (index)
    16: average_solar_radiation (W/m^2)
    17: highest_solar_radiation (W/m^2)
    18: lowest_solar_radiation (W/m^2)
    19: average_wind_speed (m/s)
    20: wind_gust (m/s)
    21: wind_lull (m/s)
    22: average_wind_direction (deg)
    23: wind_sample_interval (seconds)
    24: strike_count
    25: average_strike_distance (km)
    26: record_count
    27: battery (V)
    28: local_day_rain_accumulation (mm)
    29: local_day_nearcast_rain_accumulation (mm)
    30: local_day_precipitation_minutes (minutes)
    31: local_day_nearcast_precipitation_minutes (minutes)
    32: precipitation_type (0 none, 1 rain, 2 hail, 3 rain+hail)
    33: precipitation_analysis_type (0 none, 1 on, 2 off)
    """

    timestamp: Numeric = None
    average_pressure: Numeric = None
    highest_pressure: Numeric = None
    lowest_pressure: Numeric = None
    average_temperature: Numeric = None
    lowest_temperature: Numeric = None
    highest_temperature: Numeric = None
    average_humidity: Numeric = None
    highest_humidity: Numeric = None
    lowest_humidity: Numeric = None
    average_illuminance: Numeric = None
    highest_illuminance: Numeric = None
    lowest_illuminance: Numeric = None
    average_uv: Numeric = None
    highest_uv: Numeric = None
    lowest_uv: Numeric = None
    average_solar_radiation: Numeric = None
    highest_solar_radiation: Numeric = None
    lowest_solar_radiation: Numeric = None
    average_wind_speed: Numeric = None
    wind_gust: Numeric = None
    wind_lull: Numeric = None
    average_wind_direction: Numeric = None
    wind_sample_interval: Numeric = None
    strike_count: Numeric = None
    average_strike_distance: Numeric = None
    record_count: Numeric = None
    battery: Numeric = None
    local_day_rain_accumulation: Numeric = None
    local_day_nearcast_rain_accumulation: Numeric = None
    local_day_precipitation_minutes: Numeric = None
    local_day_nearcast_precipitation_minutes: Numeric = None
    precipitation_type: int | None = None
    precipitation_analysis_type: int | None = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> TempestDailyObservation:
        """Convert API array format to structured model.

        Args:
            array: Raw array with 34 daily observation values.

        Returns:
            Structured TempestDailyObservation instance.
        """
        padded = list(array) + [None] * (34 - len(array))
        return cls(
            timestamp=padded[0],
            average_pressure=padded[1],
            highest_pressure=padded[2],
            lowest_pressure=padded[3],
            average_temperature=padded[4],
            lowest_temperature=padded[5],
            highest_temperature=padded[6],
            average_humidity=padded[7],
            highest_humidity=padded[8],
            lowest_humidity=padded[9],
            average_illuminance=padded[10],
            highest_illuminance=padded[11],
            lowest_illuminance=padded[12],
            average_uv=padded[13],
            highest_uv=padded[14],
            lowest_uv=padded[15],
            average_solar_radiation=padded[16],
            highest_solar_radiation=padded[17],
            lowest_solar_radiation=padded[18],
            average_wind_speed=padded[19],
            wind_gust=padded[20],
            wind_lull=padded[21],
            average_wind_direction=padded[22],
            wind_sample_interval=padded[23],
            strike_count=padded[24],
            average_strike_distance=padded[25],
            record_count=padded[26],
            battery=padded[27],
            local_day_rain_accumulation=padded[28],
            local_day_nearcast_rain_accumulation=padded[29],
            local_day_precipitation_minutes=padded[30],
            local_day_nearcast_precipitation_minutes=padded[31],
            precipitation_type=padded[32],
            precipitation_analysis_type=padded[33],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with 34 daily observation values in API order.
        """
        return [
            self.timestamp,
            self.average_pressure,
            self.highest_pressure,
            self.lowest_pressure,
            self.average_temperature,
            self.lowest_temperature,
            self.highest_temperature,
            self.average_humidity,
            self.highest_humidity,
            self.lowest_humidity,
            self.average_illuminance,
            self.highest_illuminance,
            self.lowest_illuminance,
            self.average_uv,
            self.highest_uv,
            self.lowest_uv,
            self.average_solar_radiation,
            self.highest_solar_radiation,
            self.lowest_solar_radiation,
            self.average_wind_speed,
            self.wind_gust,
            self.wind_lull,
            self.average_wind_direction,
            self.wind_sample_interval,
            self.strike_count,
            self.average_strike_distance,
            self.record_count,
            self.battery,
            self.local_day_rain_accumulation,
            self.local_day_nearcast_rain_accumulation,
            self.local_day_precipitation_minutes,
            self.local_day_nearcast_precipitation_minutes,
            self.precipitation_type,
            self.precipitation_analysis_type,
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["TempestDailyObservation"]
