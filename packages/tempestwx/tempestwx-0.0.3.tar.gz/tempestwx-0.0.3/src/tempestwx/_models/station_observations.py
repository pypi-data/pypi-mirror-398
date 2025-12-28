"""StationObservation model."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from ._serializer import Model
from .station_units import StationUnits
from .status import Status


class StationObservation(Model):
    station_id: int | None = None  # int32
    type_: str | None = Field(None, alias="type")  # string
    ob_fields: list[str] | None = None  # array
    status: Status | None = None  # object
    source: str | None = None  # string
    units: StationUnits | None = None  # object
    timezone: str | None = None  # string

    # An array of observation value-arrays (aligned to obs_fields order)
    obs: list[list[float | int | str | None]] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["StationObservation"]
