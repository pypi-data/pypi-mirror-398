"""Device model with DeviceType enum."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model, StrEnum
from .device_meta import DeviceMeta
from .device_settings import DeviceSettings


class DeviceType(StrEnum):
    HB = "HB"
    AR = "AR"
    SK = "SK"
    ST = "ST"


class Device(Model):
    device_id: int | None = None  # int32
    serial_number: str | None = None  # string
    device_meta: DeviceMeta | None = None
    device_settings: DeviceSettings | None = None
    device_type: DeviceType | None = None  # string enum
    hardware_revision: str | None = None  # string
    firmware_revision: str | None = None  # string
    notes: str | None = None  # string

    location_id: int | None = None  # int32

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["Device", "DeviceType"]
