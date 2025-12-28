"""Station model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model, StrEnum
from .device import Device
from .station_item import StationItem
from .station_meta import StationMeta
from .units_default import Environment


class StationCapability(StrEnum):
    air_temperature_humidity = "air_temperature_humidity"
    barometric_pressure = "barometric_pressure"
    light = "light"
    lightning = "lightning"
    rain = "rain"
    wind = "wind"


class StationCapabilities(Model):
    device_id: int | None = None  # int32
    capability: StationCapability | None = None  # string enum
    agl: float | int | None = None  # float
    environment: Environment | None = None  # string enum
    show_precip_final: bool | None = None  # boolean


class Station(Model):
    location_id: int | None = None  # int32
    station_id: int | None = None  # int32
    name: str | None = None  # string
    public_name: str | None = None  # string
    latitude: float | int | None = None  # float
    longitude: float | int | None = None  # float
    timezone: str | None = None  # string
    timezone_offset_minutes: float | int | None = None  # number
    station_meta: StationMeta | None = None  # object
    last_modified_epoch: int | None = None  # number
    created_epoch: int | None = None  # number
    devices: list[Device] | None = None  # array of objects
    station_items: list[StationItem] | None = None  # array of objects
    is_local_mode: bool | None = None  # boolean

    # Omitted from docs but present in API
    capabilities: list[StationCapabilities] | None = None  # array of objects
    state: int | None = None  # boolean

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["Station", "StationCapabilities", "StationCapability"]
