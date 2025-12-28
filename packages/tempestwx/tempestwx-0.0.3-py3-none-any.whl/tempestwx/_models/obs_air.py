"""AIR Observation (obs_air) array model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class AirObservation(Model):
    """Structured representation of an obs_air array entry.

    Indices (0..7):
    0: timestamp (s)
    1: pressure (mb)
    2: air_temperature (C)
    3: relative_humidity (%)
    4: lightning_strike_count
    5: lightning_average_distance (km)
    6: battery (V)
    7: reporting_interval (min)
    """

    timestamp: Numeric = None
    pressure: Numeric = None
    air_temperature: Numeric = None
    relative_humidity: Numeric = None
    lightning_strike_count: Numeric = None
    lightning_average_distance: Numeric = None
    battery: Numeric = None
    reporting_interval: Numeric = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> AirObservation:
        """Convert API array format to structured model.

        Args:
            array: Raw array with 8 observation values.

        Returns:
            Structured AirObservation instance.
        """
        padded = list(array) + [None] * (8 - len(array))
        return cls(
            timestamp=padded[0],
            pressure=padded[1],
            air_temperature=padded[2],
            relative_humidity=padded[3],
            lightning_strike_count=padded[4],
            lightning_average_distance=padded[5],
            battery=padded[6],
            reporting_interval=padded[7],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with 8 observation values in API order.
        """
        return [
            self.timestamp,
            self.pressure,
            self.air_temperature,
            self.relative_humidity,
            self.lightning_strike_count,
            self.lightning_average_distance,
            self.battery,
            self.reporting_interval,
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["AirObservation"]
