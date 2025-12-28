"""StationUnits model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .units_default import (
    UnitsAirDensity,
    UnitsBrightness,
    UnitsDirection,
    UnitsDistance,
    UnitsOther,
    UnitsPrecip,
    UnitsPressure,
    UnitsSolarRadiation,
    UnitsTemp,
    UnitsWind,
)


class StationUnits(Model):
    units_temp: UnitsTemp | None = None  # string
    units_wind: UnitsWind | None = None  # string
    units_precip: UnitsPrecip | None = None  # string
    units_pressure: UnitsPressure | None = None  # string
    units_distance: UnitsDistance | None = None  # string
    units_direction: UnitsDirection | None = None  # string
    units_other: UnitsOther | None = None  # string
    units_brightness: UnitsBrightness | None = None  # string
    units_solar_radiation: UnitsSolarRadiation | None = None  # string
    units_air_density: UnitsAirDensity | None = None  # string

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


__all__ = ["StationUnits"]
