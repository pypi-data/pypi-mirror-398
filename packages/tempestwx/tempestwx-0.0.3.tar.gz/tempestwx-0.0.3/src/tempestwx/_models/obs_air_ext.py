"""AIR Daily Observation (obs_air_ext) array model.

Structured representation of the obs_air_ext (daily) array returned by the API.
"""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class AirDailyObservation(Model):
    """Structured representation of an obs_air_ext array entry.

    Indices (0..13):
    0: timestamp (epoch s UTC)
    1: average_pressure (mb)
    2: average_temperature (°C)
    3: average_humidity (%)
    4: strike_count
    5: average_strike_distance (km)
    6: highest_temperature (°C)
    7: lowest_temperature (°C)
    8: highest_pressure (mb)
    9: lowest_pressure (mb)
    10: highest_humidity (%)
    11: lowest_humidity (%)
    12: record_count
    13: battery (V)
    """

    timestamp: Numeric = None
    average_pressure: Numeric = None
    average_temperature: Numeric = None
    average_humidity: Numeric = None
    strike_count: Numeric = None
    average_strike_distance: Numeric = None
    highest_temperature: Numeric = None
    lowest_temperature: Numeric = None
    highest_pressure: Numeric = None
    lowest_pressure: Numeric = None
    highest_humidity: Numeric = None
    lowest_humidity: Numeric = None
    record_count: Numeric = None
    battery: Numeric = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> AirDailyObservation:
        """Convert API array format to structured model.

        Args:
            array: Raw array with 14 daily observation values.

        Returns:
            Structured AirDailyObservation instance.
        """
        padded = list(array) + [None] * (14 - len(array))
        return cls(
            timestamp=padded[0],
            average_pressure=padded[1],
            average_temperature=padded[2],
            average_humidity=padded[3],
            strike_count=padded[4],
            average_strike_distance=padded[5],
            highest_temperature=padded[6],
            lowest_temperature=padded[7],
            highest_pressure=padded[8],
            lowest_pressure=padded[9],
            highest_humidity=padded[10],
            lowest_humidity=padded[11],
            record_count=padded[12],
            battery=padded[13],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with 14 daily observation values in API order.
        """
        return [
            self.timestamp,
            self.average_pressure,
            self.average_temperature,
            self.average_humidity,
            self.strike_count,
            self.average_strike_distance,
            self.highest_temperature,
            self.lowest_temperature,
            self.highest_pressure,
            self.lowest_pressure,
            self.highest_humidity,
            self.lowest_humidity,
            self.record_count,
            self.battery,
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["AirDailyObservation"]
