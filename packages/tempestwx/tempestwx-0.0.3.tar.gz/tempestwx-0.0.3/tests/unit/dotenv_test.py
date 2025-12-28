from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from tempestwx.settings_loader import load_settings, reload_settings


def test_env_token_loaded_from_dotenv(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    # Create temporary .env file
    env_file = tmp_path / ".env"
    env_file.write_text("TEMPEST_ACCESS_TOKEN=DOTENV_TOKEN\n")
    # Ensure current working directory is tmp_path for load_settings
    monkeypatch.chdir(tmp_path)
    # Clear any prior cache
    reload_settings()
    s = load_settings()
    assert s.token == "DOTENV_TOKEN"


def test_reload_settings_after_env_change(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("TEMPEST_ACCESS_TOKEN=FIRST_TOKEN\n")
    monkeypatch.chdir(tmp_path)
    reload_settings()
    first = load_settings().token
    assert first == "FIRST_TOKEN"
    # Update .env and reload
    env_file.write_text("TEMPEST_ACCESS_TOKEN=SECOND_TOKEN\n")
    reload_settings()
    second = load_settings().token
    assert second == "SECOND_TOKEN"  # confirm cache cleared
