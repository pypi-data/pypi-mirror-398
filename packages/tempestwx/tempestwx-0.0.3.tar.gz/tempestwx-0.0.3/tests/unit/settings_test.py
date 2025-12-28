from __future__ import annotations

from pytest import MonkeyPatch

from tempestwx._client.client import Tempest
from tempestwx.settings_loader import load_settings


def test_load_settings_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("TEMPEST_ACCESS_TOKEN", raising=False)
    monkeypatch.delenv("TEMPEST_API_URI", raising=False)
    s = load_settings()
    # Basic shape check: ends with slash
    assert s.api_uri.endswith("/")


def test_env_overrides(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPEST_ACCESS_TOKEN", "XYZ")
    monkeypatch.setenv("TEMPEST_API_URI", "https://example.test/api/")
    s = load_settings()
    assert s.token == "XYZ"
    assert s.api_uri.startswith("https://example.test/api")


def test_client_uses_settings_env_token(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPEST_ACCESS_TOKEN", "ABC123")
    client = Tempest()
    assert client.token == "ABC123"


def test_client_explicit_token_overrides(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPEST_ACCESS_TOKEN", "ABC123")
    client = Tempest(token="OVERRIDE")
    assert client.token == "OVERRIDE"


def test_build_url_with_relative(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("TEMPEST_API_URI", "https://api.example/")
    client = Tempest(token="t")
    req, _ = client._get("stations")
    # internal request tuple first element is Request
    assert req.url.startswith("https://api.example/")
