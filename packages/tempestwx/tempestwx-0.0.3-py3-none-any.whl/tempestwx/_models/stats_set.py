"""StatsSet model."""

from __future__ import annotations

from pydantic import ConfigDict, Field

from tempestwx._models.status import Status

from ._serializer import Model


class StatsSet(Model):
    status: Status | None = None  # object
    station_id: int | None = None  # int32
    type_: str | None = Field(None, alias="type")  # string
    first_ob_local_day: str | None = None  # string
    last_ob_local_day: str | None = None  # string
    stats_day: list[list[str | int | float | None]] | None = None  # array of arrays

    # Omitted from docs but present in API
    stats_week: list[list[str | int | float | None]] | None = (
        None  # array of arrays of string | int32 | float | null
    )
    stats_month: list[list[str | int | float | None]] | None = (
        None  # array of arrays of string | int32 | float | null
    )
    stats_year: list[list[str | int | float | None]] | None = (
        None  # array of arrays of string | int32 | float | null
    )
    stats_alltime: list[str | int | float | None] | None = (
        None  # array of string | int32 | float | null
    )
    stats_week_time: list[list[str | None]] | None = (
        None  # array of arrays of strings | nulls
    )
    stats_month_time: list[list[str | None]] | None = (
        None  # array of arrays of strings | nulls
    )
    stats_year_time: list[list[str | None]] | None = (
        None  # array of arrays of strings | nulls
    )
    stats_alltime_time: list[str | None] | None = None  # array of strings | nulls
    last_ob_day_local: str | None = None  # string
    first_ob_day_local: str | None = None  # string

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["StatsSet"]
