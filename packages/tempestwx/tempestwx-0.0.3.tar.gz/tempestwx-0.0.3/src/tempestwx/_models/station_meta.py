"""StationMeta model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model


class StationMeta(Model):
    elevation: float | int | None = None  # float
    share_with_wf: bool | None = True  # boolean
    share_with_wu: bool | None = True  # boolean

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        strict=True,
    )


__all__ = ["StationMeta"]
