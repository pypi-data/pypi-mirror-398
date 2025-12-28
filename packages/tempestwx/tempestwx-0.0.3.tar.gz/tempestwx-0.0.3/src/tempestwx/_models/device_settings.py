"""DeviceMeta model with Environment enum."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model


class DeviceSettings(Model):
    show_precip_final: bool | None = None  # boolean

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["DeviceSettings"]
