"""API endpoint implementations.

Organizes all Tempest API endpoint handlers by category:
- ``TempestBetterForecast`` - forecast data
- ``TempestObservations`` - observation data
- ``TempestStations`` - station metadata and configuration
- ``TempestStats`` - statistical summaries

Each endpoint class provides methods corresponding to official Tempest API
routes documented at https://apidocs.tempestwx.com
"""

from .tempest_home.better_forecast import TempestBetterForecast
from .tempest_home.observations import TempestObservations
from .tempest_home.stations import TempestStations
from .tempest_home.stats import TempestStats

__all__ = [
    "TempestBetterForecast",
    "TempestObservations",
    "TempestStations",
    "TempestStats",
]
