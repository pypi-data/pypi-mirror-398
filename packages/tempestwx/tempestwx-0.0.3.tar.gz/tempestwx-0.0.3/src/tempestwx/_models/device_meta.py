"""DeviceMeta model with Environment enum."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .units_default import Environment


class DeviceMeta(Model):
    agl: float | int | None = None  # float
    name: str | None = None  # string
    environment: Environment | None = None  # string enum
    wifi_network_name: str | None = None  # string

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["DeviceMeta"]
