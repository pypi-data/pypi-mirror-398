"""SKY Observation (obs_sky) array model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class SkyObservation(Model):
    """Structured representation of an obs_sky array entry.

    Indices (0..16):
    0: timestamp (s)
    1: lux
    2: uv
    3: rain_accumulation (mm)
    4: wind_lull (m/s)
    5: wind_average (m/s)
    6: wind_gust (m/s)
    7: wind_direction (deg)
    8: battery (V)
    9: reporting_interval (min)
    10: solar_radiation (W/m^2)
    11: local_day_rain_accumulation (mm)
    12: precipitation_type
    13: wind_interval (seconds)
    14: nearcast_rain_accumulation (mm)
    15: local_day_nearcast_rain_accumulation (mm)
    16: precipitation_analysis_type
    """

    timestamp: Numeric = None
    lux: Numeric = None
    uv: Numeric = None
    rain_accumulation: Numeric = None
    wind_lull: Numeric = None
    wind_average: Numeric = None
    wind_gust: Numeric = None
    wind_direction: Numeric = None
    battery: Numeric = None
    reporting_interval: Numeric = None
    solar_radiation: Numeric = None
    local_day_rain_accumulation: Numeric = None
    precipitation_type: int | None = None
    wind_interval: Numeric = None
    nearcast_rain_accumulation: Numeric = None
    local_day_nearcast_rain_accumulation: Numeric = None
    precipitation_analysis_type: int | None = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> SkyObservation:
        """Convert API array format to structured model.

        Args:
            array: Raw array with 17 observation values.

        Returns:
            Structured SkyObservation instance.
        """
        padded = list(array) + [None] * (17 - len(array))
        return cls(
            timestamp=padded[0],
            lux=padded[1],
            uv=padded[2],
            rain_accumulation=padded[3],
            wind_lull=padded[4],
            wind_average=padded[5],
            wind_gust=padded[6],
            wind_direction=padded[7],
            battery=padded[8],
            reporting_interval=padded[9],
            solar_radiation=padded[10],
            local_day_rain_accumulation=padded[11],
            precipitation_type=padded[12],
            wind_interval=padded[13],
            nearcast_rain_accumulation=padded[14],
            local_day_nearcast_rain_accumulation=padded[15],
            precipitation_analysis_type=padded[16],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with 17 observation values in API order.
        """
        return [
            self.timestamp,
            self.lux,
            self.uv,
            self.rain_accumulation,
            self.wind_lull,
            self.wind_average,
            self.wind_gust,
            self.wind_direction,
            self.battery,
            self.reporting_interval,
            self.solar_radiation,
            self.local_day_rain_accumulation,
            self.precipitation_type,
            self.wind_interval,
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


__all__ = ["SkyObservation"]
