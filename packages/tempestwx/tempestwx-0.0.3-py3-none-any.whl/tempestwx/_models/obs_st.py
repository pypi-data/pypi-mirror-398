"""Tempest Observation (obs_st) array model.

Structured representation of the obs_st array returned by the API.
"""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

# Type aliases for convenience
Numeric = int | float | None
Raw = str | int | float | None


class TempestObservation(Model):
    """Structured representation of an obs_st array entry.

    Indices (0..21):
    0: timestamp (epoch s UTC)
    1: wind_lull (m/s)
    2: wind_average (m/s)
    3: wind_gust (m/s)
    4: wind_direction (deg)
    5: wind_interval (seconds)
    6: pressure (mb)
    7: air_temperature (C)
    8: relative_humidity (%)
    9: lux (illuminance, lx)
    10: uv (index)
    11: solar_radiation (W/m^2)
    12: rain_accumulation (mm)
    13: precipitation_type (0 none, 1 rain, 2 hail, 3 rain+hail)
    14: lightning_average_distance (km)
    15: lightning_strike_count
    16: battery (V)
    17: reporting_interval (min)
    18: local_day_rain_accumulation (mm)
    19: nearcast_rain_accumulation (mm)
    20: local_day_nearcast_rain_accumulation (mm)
    21: precipitation_analysis_type (0 none, 1 on, 2 off)
    """

    timestamp: Numeric = None
    wind_lull: Numeric = None
    wind_average: Numeric = None
    wind_gust: Numeric = None
    wind_direction: Numeric = None
    wind_interval: Numeric = None
    pressure: Numeric = None
    air_temperature: Numeric = None
    relative_humidity: Numeric = None
    lux: Numeric = None
    uv: Numeric = None
    solar_radiation: Numeric = None
    rain_accumulation: Numeric = None
    precipitation_type: int | None = None
    lightning_average_distance: Numeric = None
    lightning_strike_count: Numeric = None
    battery: Numeric = None
    reporting_interval: Numeric = None
    local_day_rain_accumulation: Numeric = None
    nearcast_rain_accumulation: Numeric = None
    local_day_nearcast_rain_accumulation: Numeric = None
    precipitation_analysis_type: int | None = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> TempestObservation:
        """Create an ObsStEntry from a raw obs_st array.

        Args:
            array: Raw array with 22 observation values.

        Returns:
            Structured TempestObservation instance.
        """
        padded = list(array) + [None] * (22 - len(array))
        return cls(
            timestamp=padded[0],
            wind_lull=padded[1],
            wind_average=padded[2],
            wind_gust=padded[3],
            wind_direction=padded[4],
            wind_interval=padded[5],
            pressure=padded[6],
            air_temperature=padded[7],
            relative_humidity=padded[8],
            lux=padded[9],
            uv=padded[10],
            solar_radiation=padded[11],
            rain_accumulation=padded[12],
            precipitation_type=padded[13],
            lightning_average_distance=padded[14],
            lightning_strike_count=padded[15],
            battery=padded[16],
            reporting_interval=padded[17],
            local_day_rain_accumulation=padded[18],
            nearcast_rain_accumulation=padded[19],
            local_day_nearcast_rain_accumulation=padded[20],
            precipitation_analysis_type=padded[21],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert the entry back to the obs_st array ordering.

        Returns:
            Array with 22 observation values in API order.
        """
        return [
            self.timestamp,
            self.wind_lull,
            self.wind_average,
            self.wind_gust,
            self.wind_direction,
            self.wind_interval,
            self.pressure,
            self.air_temperature,
            self.relative_humidity,
            self.lux,
            self.uv,
            self.solar_radiation,
            self.rain_accumulation,
            self.precipitation_type,
            self.lightning_average_distance,
            self.lightning_strike_count,
            self.battery,
            self.reporting_interval,
            self.local_day_rain_accumulation,
            self.nearcast_rain_accumulation,
            self.local_day_nearcast_rain_accumulation,
            self.precipitation_analysis_type,
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["TempestObservation"]
