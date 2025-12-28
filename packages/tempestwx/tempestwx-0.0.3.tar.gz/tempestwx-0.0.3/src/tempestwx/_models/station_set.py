"""StationSet model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .station import Station
from .status import Status


class StationSet(Model):
    status: Status | None = None  # object
    stations: list[Station] | None = None  # array of objects

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        strict=True,
    )


__all__ = ["StationSet"]
