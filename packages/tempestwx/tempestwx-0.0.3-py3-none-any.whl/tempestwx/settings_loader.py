"""Settings cascade loader.

Resolves configuration in the following precedence order (highest last):
    1. Library defaults (code)
    2. JSON config file (if present)
    3. ``.env`` and live environment variables (``.env`` loaded non-overriding)
    4. Explicit overrides provided by caller (applied outside this module)

This module exposes :func:`load_settings` which returns a cached
(:func:`functools.lru_cache`) :class:`~tempestwx.settings.Settings` instance.

Callers can derive variants via :meth:`tempestwx.settings.Settings.with_overrides`.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

from dotenv import load_dotenv as _load_dotenv

from ._models.units_default import Bucket, UnitsDefault
from .settings import Settings, UnitsOverrides

# Candidate config file paths to scan (first existing wins)
_CONFIG_CANDIDATES = [
    # Explicit path via env var
    os.environ.get("TEMPEST_CONFIG_PATH"),
    # Project local
    str(Path.cwd() / "config.json"),
]

_JSON_KEY_MAP = {
    "api_uri": "api_uri",
    # Units
    "default_unit_temperature": "units_temp",
    "default_unit_pressure": "units_pressure",
    "default_unit_wind": "units_wind",
    "default_unit_distance": "units_distance",
    "default_units_precip": "units_precip",
    "default_units_brightness": "units_brightness",
    "default_units_solar_radiation": "units_solar_radiation",
    "default_units_bucket_step_minutes": "bucket",
}

_ENV_UNIT_MAP = {
    "TEMPEST_DEFAULT_UNIT_TEMPERATURE": "units_temp",
    "TEMPEST_DEFAULT_UNIT_PRESSURE": "units_pressure",
    "TEMPEST_DEFAULT_UNIT_WIND": "units_wind",
    "TEMPEST_DEFAULT_UNIT_DISTANCE": "units_distance",
    "TEMPEST_DEFAULT_UNIT_PRECIP": "units_precip",
    "TEMPEST_DEFAULT_UNIT_BRIGHTNESS": "units_brightness",
    "TEMPEST_DEFAULT_UNIT_SOLAR_RADIATION": "units_solar_radiation",
    "TEMPEST_DEFAULT_UNIT_BUCKET_STEP_MINUTES": "bucket",
}


def _first_existing_path() -> Path | None:
    """Find the first existing config file from candidate paths.

    Checks candidate paths in order:
    1. Path from TEMPEST_CONFIG_PATH environment variable
    2. config.json in current working directory

    Returns:
        Path to the first existing config file, or None if none found.
    """
    for candidate in _CONFIG_CANDIDATES:
        if candidate:
            p = Path(candidate)
            if p.is_file():
                return p
    return None


def _load_json(path: Path | None) -> dict[str, Any]:
    """Load and parse JSON configuration file.

    Args:
        path: Path to JSON config file, or None.

    Returns:
        Parsed JSON as a dictionary, or empty dict if path is None,
        file doesn't exist, or JSON parsing fails.
    """
    if not path:
        return {}
    try:
        return cast(dict[str, Any], json.loads(path.read_text()))
    except Exception:
        return {}


def _build_units(default: UnitsDefault, json_cfg: dict[str, Any]) -> UnitsDefault:
    """Build UnitsDefault by layering JSON and environment overrides.

    Applies configuration in order of precedence:
    1. Start with provided default units
    2. Apply values from JSON config (if present)
    3. Apply values from environment variables (highest precedence)

    Special handling for bucket field: converts string to int if possible.

    Args:
        default: Base UnitsDefault instance to start from.
        json_cfg: Parsed JSON configuration dictionary.

    Returns:
        New UnitsDefault instance with overrides applied, or the original
        default if no overrides were found.
    """
    # Start with defaults and overlay JSON + env
    updates: dict[str, Any] = {}
    # JSON first
    for json_key, attr in _JSON_KEY_MAP.items():
        if (
            json_key.startswith(("default_unit", "default_units"))
        ) and json_key in json_cfg:
            updates[attr] = json_cfg[json_key]
    # Env overrides
    for env_key, attr in _ENV_UNIT_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            updates[attr] = val
    if not updates:
        return default
    # Normalize bucket to Bucket enum, else leave textual enums as-is
    bucket_val = updates.get("bucket")
    if bucket_val is not None:
        try:
            # Convert to int first, then to Bucket enum
            bucket_int = int(bucket_val)
            updates["bucket"] = Bucket(bucket_int)
        except (ValueError, TypeError):
            # If conversion fails, remove the bucket update
            updates.pop("bucket", None)
    return default.model_copy(update=updates)


@lru_cache
def load_settings() -> Settings:
    """Load and cache Settings from defaults, JSON, and environment.

    Implements the full configuration cascade:
    1. Library defaults (hardcoded in Settings class)
    2. JSON config file (from TEMPEST_CONFIG_PATH or ./config.json)
    3. .env file values (loaded with override=False to respect existing env)
    4. Environment variables (TEMPEST_ACCESS_TOKEN, TEMPEST_API_URI, etc.)

    The result is cached via @lru_cache, so subsequent calls return the same
    Settings instance without re-reading files or environment. Use
    reload_settings() to clear the cache and force a fresh load.

    The ``.env`` file (if present) is loaded once on first call with
    ``override=False`` to preserve already-exported environment variables.

    Returns:
        Cached Settings instance with resolved configuration.

    Note:
        Token is never stored in config.json - it comes only from
        TEMPEST_ACCESS_TOKEN environment variable.
    """
    # Ensure .env is considered early (only once due to caching)
    if _load_dotenv is not None:
        # Respect real environment variables over .env by default
        _load_dotenv(".env", override=False)
    json_cfg = _load_json(_first_existing_path())
    base = Settings()
    units = _build_units(base.units, json_cfg)
    api_uri = (
        os.environ.get("TEMPEST_API_URI") or json_cfg.get("api_uri") or base.api_uri
    )
    token = os.environ.get("TEMPEST_ACCESS_TOKEN") or None
    return Settings(api_uri=api_uri, token=token, units=units)


def reload_settings() -> Settings:
    """Clear cached settings and reload (useful after env mutation).

    Forces a fresh load of configuration by clearing the lru_cache on
    load_settings(). Useful when:
    - Environment variables have been modified during runtime
    - .env file has been changed
    - config.json has been updated
    - Testing scenarios that need fresh configuration

    On reload, refresh ``.env`` values with ``override=True`` so changes in
    the file are applied even if a prior call populated ``os.environ``. This
    does not impact callers who explicitly set environment variables within
    the same process after this call.

    Returns:
        Freshly loaded Settings instance.

    Example:
        >>> import os
        >>> os.environ["TEMPEST_ACCESS_TOKEN"] = "new_token"
        >>> settings = reload_settings()  # Picks up the new token
    """
    load_settings.cache_clear()
    if _load_dotenv is not None:
        _load_dotenv(".env", override=True)
    return load_settings()


__all__ = ["load_settings", "reload_settings", "UnitsOverrides"]
