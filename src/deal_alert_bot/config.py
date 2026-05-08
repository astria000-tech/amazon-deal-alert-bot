"""Runtime configuration loaded from environment variables and .env."""

from __future__ import annotations

import importlib
import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_SQLITE_DB_PATH = "./data/alerts.sqlite3"
DEFAULT_ALERT_SCORE_THRESHOLD = 70
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_ENABLED_SOURCES = ["mock"]


def _load_dotenv() -> None:
    """Load .env with python-dotenv when installed, otherwise use a tiny fallback.

    `python-dotenv` remains the intended dependency and is listed in
    requirements.txt. The fallback keeps the mock-only MVP runnable in restricted
    environments where dependency installation is blocked.
    """

    if importlib.util.find_spec("dotenv") is not None:
        dotenv = importlib.import_module("dotenv")
        dotenv.load_dotenv()
        return

    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _read_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value)
    except ValueError:
        print(f"Invalid integer for {name}={raw_value!r}; using default {default}.")
        return default


def _read_csv_env(
    name: str, default: list[str], *, lowercase: bool = True
) -> list[str]:
    """Read a comma-separated environment variable as a cleaned string list."""

    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return list(default)

    values = [part.strip() for part in raw_value.split(",")]
    if lowercase:
        values = [value.lower() for value in values]
    cleaned_values = [value for value in values if value]
    if not cleaned_values:
        return list(default)
    return cleaned_values


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    telegram_bot_token: str | None
    telegram_chat_id: str | None
    sqlite_db_path: Path
    alert_score_threshold: int
    log_level: str
    enabled_sources: list[str]
    keepa_api_key: str | None
    slickdeals_rss_urls: list[str]


def load_settings() -> Settings:
    """Load settings from .env and process environment."""

    _load_dotenv()

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or None
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID") or None
    sqlite_db_path = Path(os.getenv("SQLITE_DB_PATH", DEFAULT_SQLITE_DB_PATH))
    alert_score_threshold = _read_int_env(
        "ALERT_SCORE_THRESHOLD", DEFAULT_ALERT_SCORE_THRESHOLD
    )
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    enabled_sources = _read_csv_env("ENABLED_SOURCES", DEFAULT_ENABLED_SOURCES)
    keepa_api_key = os.getenv("KEEPA_API_KEY") or None
    slickdeals_rss_urls = _read_csv_env("SLICKDEALS_RSS_URLS", [], lowercase=False)

    return Settings(
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        sqlite_db_path=sqlite_db_path,
        alert_score_threshold=alert_score_threshold,
        log_level=log_level,
        enabled_sources=enabled_sources,
        keepa_api_key=keepa_api_key,
        slickdeals_rss_urls=slickdeals_rss_urls,
    )
