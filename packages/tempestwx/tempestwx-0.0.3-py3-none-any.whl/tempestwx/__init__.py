"""Tempest SDK for Python.

Primary entry points:
- ``Tempest`` - high-level synchronous client
- Settings helpers: ``Settings``, ``UnitsOverrides``, ``load_settings``,
    ``reload_settings``

The official Tempest API documentation: https://apidocs.tempestwx.com

Note: The top-level package intentionally exposes a narrow surface area.
HTTP primitives, error classes, and data models are available from their
subpackages (e.g., ``tempestwx._http`` and ``tempestwx._models``).
"""

from ._client import Tempest
from .settings import Settings, UnitsOverrides
from .settings_loader import load_settings, reload_settings
from .version import __version__

__all__ = [
    # Version
    "__version__",
    # Client
    "Tempest",
    # Settings helpers
    "Settings",
    "UnitsOverrides",
    "load_settings",
    "reload_settings",
]
