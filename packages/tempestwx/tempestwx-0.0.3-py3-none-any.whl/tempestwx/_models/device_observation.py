"""StationObservation model."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from ._serializer import Model
from .device_observation_summary import DeviceObservationSummary
from .status import Status


class DeviceObservation(Model):
    status: Status | None = None  # object
    device_id: int | None = None  # int32
    type_: str | None = Field(None, alias="type")  # string
    source: str | None = None  # string
    summary: DeviceObservationSummary | None = None  # object
    bucket_step_minutes: float | int | None = None  # number

    # An array of observation value-arrays (aligned to obs_fields order)
    obs: list[list[float | int | str | None]] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["DeviceObservation"]
