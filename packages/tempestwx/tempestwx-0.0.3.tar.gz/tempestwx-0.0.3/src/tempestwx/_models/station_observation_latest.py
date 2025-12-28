"""StationObservation model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .observation import Observation
from .station_units import StationUnits
from .status import Status


class StationObservationLatest(Model):
    station_id: int | None = None  # int32
    station_name: str | None = None  # string
    public_name: str | None = None  # string
    latitude: float | int | None = None  # float
    longitude: float | int | None = None  # float
    timezone: str | None = None  # string
    elevation: float | int | None = None  # float
    is_public: bool | None = None  # boolean
    status: Status | None = None  # object
    station_units: StationUnits | None = None  # object
    outdoor_keys: list[str] | None = None  # array of strings
    obs: list[Observation] | None = None  # array of observations

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["StationObservationLatest"]
