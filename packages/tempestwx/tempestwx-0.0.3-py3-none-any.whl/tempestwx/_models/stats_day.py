"""StatsDay entry model - structured representation of stats_day array."""

from __future__ import annotations

from pydantic import ConfigDict

from ._serializer import Model

# Type alias for numeric values that can be null
NumericValue = int | float | None
# Type for raw API values (can include strings for coercion)
RawValue = str | int | float | None


class StatsDay(Model):
    """Structured representation of a stats_day array entry.

    Each stats_day array contains 33 values at fixed indices representing
    various weather metrics and their statistics.
    """

    # Pressure metrics (mb)
    pressure: NumericValue = None
    pressure_high: NumericValue = None
    pressure_low: NumericValue = None

    # Temperature metrics (°C)
    temperature: NumericValue = None
    temperature_high: NumericValue = None
    temperature_low: NumericValue = None

    # Humidity metrics (%)
    humidity: NumericValue = None
    humidity_high: NumericValue = None
    humidity_low: NumericValue = None

    # Lux metrics (lx)
    lux: NumericValue = None
    lux_high: NumericValue = None
    lux_low: NumericValue = None

    # UV metrics (index)
    uv: NumericValue = None
    uv_high: NumericValue = None
    uv_low: NumericValue = None

    # Solar radiation metrics (W/m²)
    solar_radiation: NumericValue = None
    solar_radiation_high: NumericValue = None
    solar_radiation_low: NumericValue = None

    # Wind metrics (m/s and °)
    wind_average: NumericValue = None  # m/s
    wind_gust: NumericValue = None  # m/s
    wind_lull: NumericValue = None  # m/s
    wind_direction: NumericValue = None  # degrees
    wind_interval: NumericValue = None

    # Lightning metrics
    strike_count: NumericValue = None
    strike_average_distance: NumericValue = None  # km

    # System metrics
    record_count: NumericValue = None
    battery: NumericValue = None

    # Precipitation metrics (mm)
    precipitation_accum_today: NumericValue = None  # mm
    precipitation_accum_final: NumericValue = None  # mm
    precipitation_minutes_today: NumericValue = None
    precipitation_minutes_final: NumericValue = None

    # Precipitation type: 0=none, 1=rain, 2=hail, 3=rain+hail
    precipitation_type: int | None = None

    # Precipitation analysis: 0=none, 1=Nearcast on, 2=Nearcast off
    precipitation_analysis_type: int | None = None

    @classmethod
    def from_array(cls, array: list[RawValue]) -> StatsDay:
        """Create a StatsDay from a raw API array.

        Args:
            array: List of 33 values from the API response

        Returns:
            StatsDay instance with named fields
        """
        # Ensure we have at least 33 elements (pad with None if needed)
        padded = list(array) + [None] * (33 - len(array))

        # Type ignore for the constructor as Pydantic will coerce strings
        return cls(
            pressure=padded[0],
            pressure_high=padded[1],
            pressure_low=padded[2],
            temperature=padded[3],
            temperature_high=padded[4],
            temperature_low=padded[5],
            humidity=padded[6],
            humidity_high=padded[7],
            humidity_low=padded[8],
            lux=padded[9],
            lux_high=padded[10],
            lux_low=padded[11],
            uv=padded[12],
            uv_high=padded[13],
            uv_low=padded[14],
            solar_radiation=padded[15],
            solar_radiation_high=padded[16],
            solar_radiation_low=padded[17],
            wind_average=padded[18],
            wind_gust=padded[19],
            wind_lull=padded[20],
            wind_direction=padded[21],
            wind_interval=padded[22],
            strike_count=padded[23],
            strike_average_distance=padded[24],
            record_count=padded[25],
            battery=padded[26],
            precipitation_accum_today=padded[27],
            precipitation_accum_final=padded[28],
            precipitation_minutes_today=padded[29],
            precipitation_minutes_final=padded[30],
            precipitation_type=padded[31],
            precipitation_analysis_type=padded[32],
        )

    def to_array(self) -> list[int | float | None]:
        """Convert the structured data back to the API array format.

        Returns:
            List of 33 values in the expected API order
        """
        return [
            self.pressure,
            self.pressure_high,
            self.pressure_low,
            self.temperature,
            self.temperature_high,
            self.temperature_low,
            self.humidity,
            self.humidity_high,
            self.humidity_low,
            self.lux,
            self.lux_high,
            self.lux_low,
            self.uv,
            self.uv_high,
            self.uv_low,
            self.solar_radiation,
            self.solar_radiation_high,
            self.solar_radiation_low,
            self.wind_average,
            self.wind_gust,
            self.wind_lull,
            self.wind_direction,
            self.wind_interval,
            self.strike_count,
            self.strike_average_distance,
            self.record_count,
            self.battery,
            self.precipitation_accum_today,
            self.precipitation_accum_final,
            self.precipitation_minutes_today,
            self.precipitation_minutes_final,
            self.precipitation_type,
            self.precipitation_analysis_type,
        ]

    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="ignore",
        str_strip_whitespace=True,
    )


__all__ = ["StatsDay"]
