"""Better Forecast API endpoint implementation.

This module provides access to the Tempest Weather "Better Forecast" API,
which delivers AI-enhanced weather forecasts tailored to station locations.
Forecasts include current conditions, hourly predictions, and daily summaries
with customizable unit preferences.

API Reference:
    https://apidocs.tempestwx.com/reference/get_better-forecast

Classes:
    TempestBetterForecast: Client for retrieving enhanced weather forecasts.
"""

from __future__ import annotations

from tempestwx._client.base import TempestBase
from tempestwx._client.decorators import make_request
from tempestwx._client.processor import model_instance
from tempestwx._models.better_forecast import BetterForecast
from tempestwx._models.units_default import (
    TEMPEST_DEFAULT_UNITS,
    UnitsDistance,
    UnitsPrecip,
    UnitsPressure,
    UnitsTemp,
    UnitsWind,
)


class TempestBetterForecast(TempestBase):
    """Better Forecast API endpoints."""

    @make_request(model_instance(BetterForecast))
    def forecast(
        self,
        station_id: int,
        units_temp: UnitsTemp | str = TEMPEST_DEFAULT_UNITS.units_temp,
        units_wind: UnitsWind | str = TEMPEST_DEFAULT_UNITS.units_wind,
        units_pressure: UnitsPressure | str = TEMPEST_DEFAULT_UNITS.units_pressure,
        units_precip: UnitsPrecip | str = TEMPEST_DEFAULT_UNITS.units_precip,
        units_distance: UnitsDistance | str = TEMPEST_DEFAULT_UNITS.units_distance,
    ) -> BetterForecast:
        """Get current conditions and Better Forecast data for a station.

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/get_better-forecast

        Args:
            station_id: Unique station identifier. Must be a positive integer.
            units_temp: Temperature units (allowed: 'c', 'f').
                Defaults to 'c'.
            units_wind: Wind units (allowed: 'mph', 'kph', 'kts', 'mps', 'bft',
                'lfm'). Defaults to 'mps'.
            units_pressure: Pressure units (allowed: 'mb', 'inhg', 'mmhg', 'hpa').
                Defaults to 'mb'.
            units_precip: Precipitation units (allowed: 'mm', 'cm', 'in').
                Defaults to 'mm'.
            units_distance: Distance units (allowed: 'km', 'mi').
                Defaults to 'km'.

        Returns:
            Current conditions plus Better Forecast.

        Raises:
            ValueError: If ``station_id`` is invalid or any unit parameter fails enum
                validation.
        """
        if station_id <= 0:
            raise ValueError("station_id must be a positive integer.")

        # Validate and convert all unit parameters
        validated_temp = self._validate_enum_param("units_temp", units_temp, UnitsTemp)
        validated_wind = self._validate_enum_param("units_wind", units_wind, UnitsWind)
        validated_pressure = self._validate_enum_param(
            "units_pressure", units_pressure, UnitsPressure
        )
        validated_precip = self._validate_enum_param(
            "units_precip", units_precip, UnitsPrecip
        )
        validated_distance = self._validate_enum_param(
            "units_distance", units_distance, UnitsDistance
        )

        return self._get(  # type: ignore[no-any-return]
            "better_forecast",
            station_id=station_id,
            units_temp=validated_temp.value,
            units_wind=validated_wind.value,
            units_pressure=validated_pressure.value,
            units_precip=validated_precip.value,
            units_distance=validated_distance.value,
        )
