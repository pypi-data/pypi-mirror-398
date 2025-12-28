"""Observations API endpoint implementation.

This module provides access to historical and real-time weather observation data
from Tempest Weather stations and devices. It supports querying observations by:

- Station ID (aggregated multi-device data with time ranges)
- Device ID (raw device-level measurements)
- Latest observations (most recent readings for a station)

Observations include metrics like temperature, humidity, wind speed, pressure,
and precipitation. Data can be filtered by time range, bucketed by intervals,
and customized with unit preferences.

API Reference:
    - Station observations: https://apidocs.tempestwx.com/reference/get_observations-stn-station-id-1
    - Device observations: https://apidocs.tempestwx.com/reference/getobservationsbydeviceid
    - Latest observations: https://apidocs.tempestwx.com/reference/getstationobservation

Classes:
    TempestObservations: Client for retrieving weather observation data.
"""

from __future__ import annotations

import re as _re

from tempestwx._client.base import TempestBase
from tempestwx._client.decorators import make_request
from tempestwx._client.processor import model_instance
from tempestwx._models.device_observation import DeviceObservation
from tempestwx._models.station_observation_latest import (
    StationObservationLatest,
)
from tempestwx._models.station_observations import StationObservation
from tempestwx._models.units_default import (
    TEMPEST_DEFAULT_UNITS,
    Bucket,
    Format,
    UnitsDistance,
    UnitsPrecip,
    UnitsPressure,
    UnitsTemp,
    UnitsWind,
)


class TempestObservations(TempestBase):
    """Observations API endpoints."""

    @make_request(model_instance(StationObservation))
    def obs_station(
        self,
        station_id: int,
        start_time: int | None = None,
        end_time: int | None = None,
        bucket: Bucket | int = TEMPEST_DEFAULT_UNITS.bucket.value,
        obs_fields: str = "",  # comma-separated observation field names
        units_temp: UnitsTemp | str = TEMPEST_DEFAULT_UNITS.units_temp,
        units_wind: UnitsWind | str = TEMPEST_DEFAULT_UNITS.units_wind,
        units_pressure: UnitsPressure | str = (TEMPEST_DEFAULT_UNITS.units_pressure),
        units_precip: UnitsPrecip | str = TEMPEST_DEFAULT_UNITS.units_precip,
        units_distance: UnitsDistance | str = (TEMPEST_DEFAULT_UNITS.units_distance),
    ) -> StationObservation:
        """Get observations for a station (historical / range query).

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/get_observations-stn-station-id-1

        Args:
            station_id: Unique station identifier. Must be a positive integer.
            start_time: Unix epoch seconds (UTC) for the beginning of the time range. If
                provided must be > 0 and (if ``end_time`` given) <= ``end_time``.
            end_time: Unix epoch seconds (UTC) for the end of the time range. If
                provided must be > 0 and (if ``start_time`` given) >=
                ``start_time``.
            bucket: Aggregation bucket size (minutes) accepted by the API. May be
                either a ``Bucket`` enum member or its underlying integer value.
                Defaults to 1 (no aggregation). Allowed values: 1, 5, 30, 180.
            obs_fields: Comma separated list of observation field names to limit the
                response. Field names must be in the allowed set published by the
                API (e.g. "timestamp,air_temperature,wind_avg" - list subject to
                API docs). Empty string requests all default fields.
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
            Station observations.

        Raises:
            ValueError: If any validation fails (invalid station_id, time range, bucket,
                units or obs_fields).
        """
        if station_id <= 0:
            raise ValueError("station_id must be a positive integer.")

        # Validate time range
        if start_time is not None and start_time <= 0:
            raise ValueError("start_time must be a positive Unix epoch seconds value.")
        if end_time is not None and end_time <= 0:
            raise ValueError("end_time must be a positive Unix epoch seconds value.")
        if start_time is not None and end_time is not None and start_time > end_time:
            raise ValueError("start_time cannot be greater than end_time.")

        # Validate and convert all unit parameters
        if isinstance(bucket, int):
            bucket_for_validate: Bucket | str = Bucket(bucket)
        else:
            bucket_for_validate = bucket

        validate_bucket = self._validate_enum_param(
            "bucket", bucket_for_validate, Bucket
        )
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

        # Basic obs_fields validation
        if obs_fields:
            raw_fields = [f.strip() for f in obs_fields.split(",") if f.strip()]
            if not raw_fields:
                raise ValueError("obs_fields provided but no valid field names parsed.")

            # Accept simple snake_case alphanum + underscore names
            invalid = [f for f in raw_fields if not _re.fullmatch(r"[a-z0-9_]+", f)]
            if invalid:
                raise ValueError(
                    "Invalid field name(s) in obs_fields: "
                    f"{invalid}. Field names must be snake_case alphanumeric."
                )

        return self._get(  # type: ignore[no-any-return]
            f"observations/stn/{station_id}",
            start_time=start_time,
            end_time=end_time,
            bucket=validate_bucket.value,  # send raw integer expected by API
            obs_fields=obs_fields,
            units_temp=validated_temp,
            units_wind=validated_wind,
            units_pressure=validated_pressure,
            units_precip=validated_precip,
            units_distance=validated_distance,
        )

    @make_request(model_instance(DeviceObservation))
    def obs_device(
        self,
        device_id: int,
        day_offset: int = 0,
        time_start: int | None = None,
        time_end: int | None = None,
        format: Format | str | None = None,
    ) -> DeviceObservation:
        """Get observations for a specific device (e.g., Tempest sensor).

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/getobservationsbydeviceid

        Args:
            device_id: Unique device identifier. Must be positive.
            day_offset: Day offset relative to today for which to retrieve observations.
                API typically supports a small negative/positive window (e.g. 0 for
                today, 1 for yesterday).
            time_start: Unix epoch seconds (UTC) lower bound inside the chosen day (if
                provided must be > 0). Must be <= ``time_end`` if both provided.
            time_end: Unix epoch seconds (UTC) upper bound (if provided must be > 0).
            format: Optional response format (e.g. "json" or "csv") if supported. Case
                insensitive. If provided must be one of {"json","csv"}.
                Format units (allowed: 'csv').
                Defaults to JSON response if not provided.

        Returns:
            Device observations.

        Raises:
            ValueError: If any input parameter fails validation.
        """
        if device_id <= 0:
            raise ValueError("device_id must be a positive integer.")

        if time_start is not None and time_start <= 0:
            raise ValueError("time_start must be a positive Unix epoch seconds value.")
        if time_end is not None and time_end <= 0:
            raise ValueError("time_end must be a positive Unix epoch seconds value.")
        if time_start is not None and time_end is not None and time_start > time_end:
            raise ValueError("time_start cannot be greater than time_end.")

        if format is not None:
            fmt = format.lower()
            allowed_formats = {"csv"}
            if fmt not in allowed_formats:
                allowed = sorted(allowed_formats)
                raise ValueError(f"Invalid format '{format}'. Allowed: {allowed}")
            format = fmt

        return self._get(  # type: ignore[no-any-return]
            f"observations/device/{device_id}",
            day_offset=day_offset,
            time_start=time_start,
            time_end=time_end,
            format=format,
        )

    @make_request(model_instance(StationObservationLatest))
    def obs_station_latest(
        self,
        station_id: int,
    ) -> StationObservationLatest:
        """Get the latest observation snapshot for a station.

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/getstationobservation

        Args:
            station_id: Unique station identifier. Must be positive.

        Returns:
            Latest Station observation

        Raises:
            ValueError: If ``station_id`` is invalid.
        """
        if station_id <= 0:
            raise ValueError("station_id must be a positive integer.")

        return self._get(f"observations/station/{station_id}")  # type: ignore[no-any-return]
