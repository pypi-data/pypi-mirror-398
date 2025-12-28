from __future__ import annotations

from collections.abc import Generator

import pytest

from tempestwx.settings_loader import load_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> Generator[None]:
    """Ensure a fresh Settings instance for every test.

    Clears the memoized load_settings cache before and after each test so
    environment changes (via monkeypatch or .env updates) are respected
    consistently and don't leak across tests.
    """
    # Clear memoized settings before each test so first load reflects test's env
    load_settings.cache_clear()
    try:
        yield
    finally:
        # Clear after test to avoid leaking into subsequent tests
        load_settings.cache_clear()
