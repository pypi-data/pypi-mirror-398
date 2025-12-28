"""StationItem model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model


class StationItem(Model):
    location_item_id: int | None = None  # int32
    location_id: int | None = None  # int32
    device_id: int | None = None  # int32
    item: str | None = None  # string
    sort: int | None = None  # number
    station_id: int | None = None  # int32
    station_item_id: int | None = None  # int32

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["StationItem"]
