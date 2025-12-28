"""Basic smoke checks for installed artifacts (wheel/sdist).

This test is intentionally lightweight and makes no network calls.
It verifies that the package can be imported, that distribution
metadata matches the module version, and that a minimal client can be
constructed using both explicit and environment-provided tokens.

Run this against the built wheel/sdist in a clean virtualenv to
validate publishable artifacts.
"""

from __future__ import annotations

import os
from importlib import metadata as importlib_metadata

from tempestwx import Tempest, load_settings

try:
    import pytest
except Exception:  # pragma: no cover - optional for script-mode
    pytest = None  # type: ignore

import tempestwx


def test_import_and_version_consistency() -> None:
    """Package imports and exposes a version matching dist metadata."""
    # Module-level version
    assert hasattr(tempestwx, "__version__"), "tempestwx.__version__ missing"
    module_version = tempestwx.__version__

    # Distribution metadata version (from installed artifact)
    try:
        dist_version = importlib_metadata.version("tempestwx")
    except importlib_metadata.PackageNotFoundError:
        # Likely running from source tree without an installed dist
        if pytest is not None:  # running under pytest
            pytest.skip("Distribution metadata not available (not installed artifact)")
            return
        # Script mode: print note and return without failing
        print("[smoke] Skipping dist version check: package not installed")
        return

    assert module_version == dist_version, (
        f"module __version__ ({module_version}) != dist version ({dist_version})"
    )


def test_client_constructs_and_uses_env_token() -> None:
    """Client can be constructed with explicit and env-provided tokens.

    No HTTP calls are performed; we only exercise header building and URL
    composition to ensure core plumbing works from the installed package.
    """
    # 1) Explicit token
    c = Tempest(token="abc123")
    assert c.token == "abc123"
    # Authorization header uses the provided token
    headers = c._create_headers()  # protected, but safe for smoke validation
    assert headers["Authorization"] == "Bearer abc123"
    assert headers["Content-Type"] == "application/json"

    # _build_url should prefix non-absolute paths with the API base
    base = load_settings().api_uri_normalized
    assert c._build_url("stations").startswith(base)

    # 2) Environment-provided token via settings loader
    # Stash prior env value and set a temporary token
    prior = os.environ.get("TEMPEST_ACCESS_TOKEN")
    try:
        os.environ["TEMPEST_ACCESS_TOKEN"] = "envtoken"
        # Ensure settings cache is cleared so environment is re-read
        load_settings.cache_clear()

        c2 = Tempest()
        assert c2.token == "envtoken"
        headers2 = c2._create_headers()
        assert headers2["Authorization"] == "Bearer envtoken"

        # Sanity: repr does not crash and includes class name
        r = repr(c2)
        assert "Tempest(" in r
    finally:
        # Restore prior env and reload settings to not leak state
        if prior is None:
            os.environ.pop("TEMPEST_ACCESS_TOKEN", None)
        else:
            os.environ["TEMPEST_ACCESS_TOKEN"] = prior
        load_settings.cache_clear()


def _run_as_script() -> None:
    """Execute checks when run as a plain script (no pytest)."""
    test_import_and_version_consistency()
    test_client_constructs_and_uses_env_token()


if __name__ == "__main__":  # pragma: no cover - manual script entrypoint
    _run_as_script()
