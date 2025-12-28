"""Stations API endpoint implementation.

This module provides access to Tempest Weather station metadata, including
station details, device information, location coordinates, and configuration.
Stations represent physical locations with one or more weather devices that
collect atmospheric measurements.

API Reference:
    - List all stations: https://apidocs.tempestwx.com/reference/get_stations
    - Get station by ID: https://apidocs.tempestwx.com/reference/getstationbyid

Classes:
    TempestStations: Client for retrieving station metadata and details.
"""

from __future__ import annotations

from tempestwx._client.base import TempestBase
from tempestwx._client.decorators import make_request
from tempestwx._client.processor import model_instance
from tempestwx._models.station_set import StationSet


class TempestStations(TempestBase):
    """Stations API endpoints."""

    @make_request(model_instance(StationSet))
    def stations(self) -> StationSet:
        """Get metadata for all stations associated with the authenticated account.

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/get_stations

        Returns:
            Station metadata.
        """
        return self._get("stations")  # type: ignore[no-any-return]

    @make_request(model_instance(StationSet))
    def station(self, station_id: int) -> StationSet:
        """Get metadata for a specific station.

        Wrapper for Tempest Weather API endpoint:
        https://apidocs.tempestwx.com/reference/getstationbyid

        Args:
            station_id: Unique station identifier. Must be a positive integer.

        Returns:
            Station metadata for a single station.

        Raises:
            ValueError: If ``station_id`` is not positive.
        """
        if station_id <= 0:
            raise ValueError("station_id must be a positive integer.")

        return self._get(f"stations/{station_id}")  # type: ignore[no-any-return]
