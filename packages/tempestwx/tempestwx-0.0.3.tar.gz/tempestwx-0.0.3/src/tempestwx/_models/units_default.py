"""UnitsDefault model.

Represents the Tempest API default units when no units are specified.
Source: https://apidocs.tempestwx.com/reference/default-units-1
"""

from __future__ import annotations

from enum import Enum

from pydantic import ConfigDict

from ._serializer import Model, StrEnum


class UnitsTemp(StrEnum):
    c = "c"
    f = "f"


class UnitsWind(StrEnum):
    mph = "mph"
    kph = "kph"
    kts = "kts"
    mps = "mps"
    bft = "bft"
    lfm = "lfm"


class UnitsPressure(StrEnum):
    mb = "mb"
    inhg = "inhg"
    mmhg = "mmhg"
    hpa = "hpa"


class PressureTrend(StrEnum):
    falling = "falling"
    rising = "rising"
    steady = "steady"


class UnitsPrecip(StrEnum):
    mm = "mm"
    cm = "cm"
    in_ = "in"  # 'in' is a Python keyword, so we use 'in_' with alias


class PrecipIcon(StrEnum):
    chance_rain = "chance-rain"
    chance_snow = "chance-snow"
    chance_sleet = "chance-sleet"
    possibly_rainy_day = "possibly-rainy-day"


class PrecipType(StrEnum):
    rain = "rain"
    snow = "snow"
    sleet = "sleet"
    storm = "storm"


class UnitsDistance(StrEnum):
    km = "km"
    mi = "mi"


class UnitsBrightness(StrEnum):
    lux = "lux"


class UnitsSolarRadiation(StrEnum):
    w_m2 = "w/m2"


class UnitsOther(StrEnum):
    imperial = "imperial"
    metric = "metric"


class UnitsAirDensity(StrEnum):
    kg_m3 = "kg/m3"
    lbs_ft3 = "lbs/ft3"


class UnitsDirection(StrEnum):
    carinal = "cardinal"
    degrees = "degrees"


class Environment(StrEnum):
    indoor = "indoor"
    outdoor = "outdoor"


class Bucket(Enum):
    ONE = 1
    FIVE = 5
    THIRTY = 30
    ONE_EIGHTY = 180


class Format(StrEnum):
    csv = "csv"


class Conditions(StrEnum):
    clear = "Clear"
    sunny = "Sunny"
    cloudy = "Cloudy"
    partly_cloudy = "Partly Cloudy"
    foggy = "Foggy"
    windy = "Windy"
    rain_likely = "Rain Likely"
    rain_possible = "Rain Possible"
    very_light_rain = "Very Light Rain"
    light_rain = "Light Rain"
    moderate_rain = "Moderate Rain"
    heavy_rain = "Heavy Rain"
    very_heavy_rain = "Very Heavy Rain"
    extreme_rain = "Extreme Rain"
    thunderstorms_likely = "Thunderstorms Likely"
    thunderstorms_possible = "Thunderstorms Possible"
    snow_likely = "Snow Likely"
    snow_possible = "Snow Possible"
    wintry_mix_likely = "Wintry Mix Likely"
    wintry_mix_possible = "Wintry Mix Possible"


class Icon(StrEnum):
    clear_day = "clear-day"
    clear_night = "clear-night"
    rainy = "rainy"
    possibly_rainy_day = "possibly-rainy-day"
    possibly_rainy_night = "possibly-rainy-night"
    possible_rainy_day = "possible-rainy-day"
    possible_rainy_night = "possible-rainy-night"
    snow = "snow"
    possibly_snow_day = "possibly-snow-day"
    possibly_snow_night = "possibly-snow-night"
    possible_snow_day = "possible-snow-day"
    possible_snow_night = "possible-snow-night"
    sleet = "sleet"
    possibly_sleet_day = "possibly-sleet-day"
    possibly_sleet_night = "possibly-sleet-night"
    possible_sleet_day = "possible-sleet-day"
    possible_sleet_night = "possible-sleet-night"
    thunderstorm = "thunderstorm"
    possibly_thunderstorm_day = "possibly-thunderstorm-day"
    possibly_thunderstorm_night = "possibly-thunderstorm-night"
    windy = "windy"
    foggy = "foggy"
    cloudy = "cloudy"
    partly_cloudy_day = "partly-cloudy-day"
    partly_cloudy_night = "partly-cloudy-night"


class UnitsDefault(Model):
    """Default units for API responses when unspecified."""

    units_temp: UnitsTemp = UnitsTemp.c
    units_pressure: UnitsPressure = UnitsPressure.mb
    units_wind: UnitsWind = UnitsWind.mps
    units_distance: UnitsDistance = UnitsDistance.km
    units_brightness: UnitsBrightness = UnitsBrightness.lux
    units_solar_radiation: UnitsSolarRadiation = UnitsSolarRadiation.w_m2

    # Not listed explicitly on the Default Units page
    units_precip: UnitsPrecip = UnitsPrecip.mm
    # units_direction: UnitsDirection = UnitsDirection.degrees
    # units_other: UnitsOther = UnitsOther.metric

    bucket: Bucket = Bucket.ONE
    # format_: Format = None # Default is JSON if not specified

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
        strict=True,
    )


# A reusable instance of default units for importing across the codebase.
# This avoids accessing Pydantic model fields on the class, which raises
# AttributeError via Pydantic's __getattr__. Use TEMPEST_DEFAULT_UNITS.<field>.
TEMPEST_DEFAULT_UNITS: UnitsDefault = UnitsDefault()


__all__ = ["UnitsDefault", "TEMPEST_DEFAULT_UNITS"]
