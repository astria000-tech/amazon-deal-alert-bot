"""Tests for environment and dotenv configuration loading."""

from __future__ import annotations

import importlib
from pathlib import Path

import deal_alert_bot.config as config


def clear_runtime_env(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    for name in [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "SQLITE_DB_PATH",
        "ALERT_SCORE_THRESHOLD",
        "LOG_LEVEL",
        "ENABLED_SOURCES",
        "KEEPA_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_used_when_environment_is_absent(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)

    settings = config.load_settings()

    assert settings.telegram_bot_token is None
    assert settings.telegram_chat_id is None
    assert settings.sqlite_db_path == Path(config.DEFAULT_SQLITE_DB_PATH)
    assert settings.alert_score_threshold == config.DEFAULT_ALERT_SCORE_THRESHOLD
    assert settings.log_level == config.DEFAULT_LOG_LEVEL
    assert settings.enabled_sources == config.DEFAULT_ENABLED_SOURCES
    assert settings.keepa_api_key is None


def test_alert_score_threshold_env_is_parsed_as_int(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALERT_SCORE_THRESHOLD", "85")

    settings = config.load_settings()

    assert settings.alert_score_threshold == 85
    assert isinstance(settings.alert_score_threshold, int)


def test_sqlite_db_path_env_is_used(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    custom_db_path = tmp_path / "custom" / "alerts.sqlite3"
    monkeypatch.setenv("SQLITE_DB_PATH", str(custom_db_path))

    settings = config.load_settings()

    assert settings.sqlite_db_path == custom_db_path


def test_dotenv_fallback_works_when_python_dotenv_is_unavailable(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "ALERT_SCORE_THRESHOLD=88\n"
        "SQLITE_DB_PATH=./tmp/fallback-alerts.sqlite3\n"
        "LOG_LEVEL=debug\n"
    )

    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if name == "dotenv":
            return None
        return real_find_spec(name, *args, **kwargs)

    monkeypatch.setattr(config.importlib.util, "find_spec", fake_find_spec)

    settings = config.load_settings()

    assert settings.alert_score_threshold == 88
    assert settings.sqlite_db_path == Path("./tmp/fallback-alerts.sqlite3")
    assert settings.log_level == "DEBUG"


def test_enabled_sources_env_is_parsed_as_clean_list(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENABLED_SOURCES", "mock, keepa")

    settings = config.load_settings()

    assert settings.enabled_sources == ["mock", "keepa"]


def test_enabled_sources_empty_env_uses_default(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ENABLED_SOURCES", " , , ")

    settings = config.load_settings()

    assert settings.enabled_sources == ["mock"]


def test_keepa_api_key_env_is_loaded_without_logging(monkeypatch, tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    clear_runtime_env(monkeypatch)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("KEEPA_API_KEY", "fake-secret-value")

    settings = config.load_settings()

    output = capsys.readouterr().out
    assert settings.keepa_api_key == "fake-secret-value"
    assert "fake-secret-value" not in output
