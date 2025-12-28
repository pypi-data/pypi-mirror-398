"""BetterForecastForecast model."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model
from .better_forecast_daily_forecast import BetterForecastDailyForecast
from .better_forecast_hourly_forecast import BetterForecastHourlyForecast


class BetterForecastForecast(Model):
    daily: list[BetterForecastDailyForecast] | None = None
    hourly: list[BetterForecastHourlyForecast] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        strict=True,
    )


__all__ = ["BetterForecastForecast"]
