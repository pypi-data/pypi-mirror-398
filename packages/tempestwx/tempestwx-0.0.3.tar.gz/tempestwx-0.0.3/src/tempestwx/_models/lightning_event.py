"""Lightning event (evt_strike) array model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

Numeric = int | float | None
Raw = str | int | float | None


class LightningEvent(Model):
    """Structured representation of an evt_strike array entry.

    Indices (0..2):
    0: timestamp (s)
    1: distance (km)
    2: energy
    """

    timestamp: Numeric = None
    distance: Numeric = None
    energy: Numeric = None

    @classmethod
    def from_array(cls, array: list[Raw]) -> LightningEvent:
        """Convert API array format to structured model.

        Args:
            array: Raw array with [timestamp, distance, energy].

        Returns:
            Structured LightningEvent instance.
        """
        padded = list(array) + [None] * (3 - len(array))
        return cls(
            timestamp=padded[0],
            distance=padded[1],
            energy=padded[2],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert model to API array format.

        Returns:
            Array with [timestamp, distance, energy].
        """
        return [self.timestamp, self.distance, self.energy]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["LightningEvent"]
