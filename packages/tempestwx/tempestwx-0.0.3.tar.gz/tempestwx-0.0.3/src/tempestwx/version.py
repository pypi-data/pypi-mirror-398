"""Tempest SDK package version.

This module exports ``__version__``, where the runtime version is derived
from ``importlib.metadata``. This preserves the public import path
``tempestwx.version.__version__`` without duplicating version logic.
"""

from importlib import metadata as _metadata

try:
    __version__ = _metadata.version("tempestwx")
except _metadata.PackageNotFoundError:  # not installed (e.g., running from source tree)
    __version__ = "0.0.0+unknown"

__all__ = ["__version__"]
