from __future__ import annotations

from typing import Any

import pytest

from tempestwx._client.client import Tempest
from tempestwx._http import Request, Response, Transport
from tempestwx._models.better_forecast import BetterForecast
from tempestwx._models.device_observation import DeviceObservation
from tempestwx._models.station_observation_latest import StationObservationLatest
from tempestwx._models.station_observations import StationObservation
from tempestwx._models.station_set import StationSet
from tempestwx._models.stats_set import StatsSet


class DummyTransport(Transport):
    """Synchronous dummy transport.

    Captures the last request and returns a canned response.
    """

    def __init__(self, content: dict[str, Any] | None = None, status_code: int = 200):
        """Initialize dummy transport with canned response."""
        self.last_request: Request | None = None
        self._content = content or {}
        self._status = status_code

    def send(self, request: Request) -> Response:
        """Send request and return canned response."""
        self.last_request = request
        return Response(
            url=request.url,
            headers={},
            status_code=self._status,
            content=self._content,
        )

    @property
    def is_async(self) -> bool:
        """Return transport asynchronicity mode."""
        return False

    def close(self) -> None:
        """Close transport (no-op for dummy)."""
        return


def make_client_with(
    content: dict[str, Any] | None = None,
) -> tuple[Tempest, DummyTransport]:
    transport = DummyTransport(content=content)
    client = Tempest(token="t", transport=transport)
    return client, transport


# Stations


def test_stations_success() -> None:
    client, tr = make_client_with({"stations": []})
    result = client.stations()
    assert isinstance(result, StationSet)
    assert tr.last_request is not None
    assert tr.last_request.method == "GET"
    assert tr.last_request.url.endswith("stations")


def test_station_success() -> None:
    client, tr = make_client_with({"stations": []})
    result = client.station(123)
    assert isinstance(result, StationSet)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("stations/123")


def test_station_invalid_id_raises() -> None:
    client, _ = make_client_with({"stations": []})
    with pytest.raises(ValueError):
        client.station(0)


# Observations (station range)


def test_obs_station_success_defaults() -> None:
    content = {"station_id": 1, "obs": []}
    client, tr = make_client_with(content)
    result = client.obs_station(1)
    assert isinstance(result, StationObservation)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("observations/stn/1")
    # Default bucket and units should be present (values are enums/strings)
    params = tr.last_request.params or {}
    assert params.get("bucket") == 1
    assert params.get("units_temp") in {"c", "f"}


def test_obs_station_invalid_time_range_raises() -> None:
    client, _ = make_client_with({})
    with pytest.raises(ValueError):
        client.obs_station(1, start_time=10, end_time=5)


# Observations (device)


def test_obs_device_success() -> None:
    content = {"device_id": 99, "obs": []}
    client, tr = make_client_with(content)
    result = client.obs_device(99, day_offset=1)
    assert isinstance(result, DeviceObservation)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("observations/device/99")
    assert (tr.last_request.params or {}).get("day_offset") == 1


def test_obs_device_invalid_format_raises() -> None:
    client, _ = make_client_with({})
    with pytest.raises(ValueError):
        client.obs_device(5, format="xml")


# Observations latest


def test_obs_station_latest_success() -> None:
    content = {"station_id": 1, "obs": []}
    client, tr = make_client_with(content)
    result = client.obs_station_latest(1)
    assert isinstance(result, StationObservationLatest)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("observations/station/1")


# Better Forecast


def test_better_forecast_success() -> None:
    content = {"status": {"status_code": 0}}
    client, tr = make_client_with(content)
    result = client.forecast(1)
    assert isinstance(result, BetterForecast)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("better_forecast")
    params = tr.last_request.params or {}
    # Expect unit codes to be strings like 'c','mps','mb','mm','km'
    assert params.get("units_temp") in {"c", "f"}
    assert params.get("units_wind") in {"mph", "kph", "kts", "mps", "bft", "lfm"}
    assert params.get("units_pressure") in {"mb", "inhg", "mmhg", "hpa"}
    assert params.get("units_precip") in {"mm", "cm", "in"}
    assert params.get("units_distance") in {"km", "mi"}


def test_better_forecast_invalid_id_raises() -> None:
    client, _ = make_client_with({})
    with pytest.raises(ValueError):
        client.forecast(0)


# Stats


def test_stats_success() -> None:
    client, tr = make_client_with({"status": {"status_code": 0}})
    result = client.stats(1)
    assert isinstance(result, StatsSet)
    assert tr.last_request is not None
    assert tr.last_request.url.endswith("stats/station/1")


def test_stats_invalid_id_raises() -> None:
    client, _ = make_client_with({})
    with pytest.raises(ValueError):
        client.stats(0)
