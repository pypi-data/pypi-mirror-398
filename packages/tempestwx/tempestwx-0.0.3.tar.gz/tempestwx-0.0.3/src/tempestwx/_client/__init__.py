"""High-level client interfaces.

Provides the unified ``Tempest`` client that aggregates all API endpoints
into a single interface. This is the primary entry point for users.
"""

from .client import Tempest

__all__ = ["Tempest"]
