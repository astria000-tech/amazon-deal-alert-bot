"""Registry for safe deal source adapters."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterable

from .base import DealSource
from .keepa import KeepaDealSource
from .mock import MockDealSource
from .slickdeals import SlickdealsRssSource

SourceFactory = Callable[[], DealSource]

DEFAULT_ENABLED_SOURCES = ["mock"]


def _build_keepa_source() -> KeepaDealSource:
    return KeepaDealSource(api_key=os.getenv("KEEPA_API_KEY") or None)


def _build_slickdeals_source() -> SlickdealsRssSource:
    rss_urls = _read_csv_env("SLICKDEALS_RSS_URLS")
    return SlickdealsRssSource(rss_urls=rss_urls)


def _read_csv_env(name: str) -> list[str]:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return []
    return [part.strip() for part in raw_value.split(",") if part.strip()]


_SOURCE_FACTORIES: dict[str, SourceFactory] = {
    "keepa": _build_keepa_source,
    "mock": MockDealSource,
    "slickdeals": _build_slickdeals_source,
}


def available_source_names() -> list[str]:
    """Return source names that can currently be enabled."""

    return sorted(_SOURCE_FACTORIES)


def get_source(name: str) -> DealSource:
    """Build a source adapter by name.

    Raises:
        ValueError: If the name is not registered. This intentionally fails
            closed so typos or future real-source names cannot silently trigger
            unexpected behavior.
    """

    normalized_name = name.strip().lower()
    try:
        return _SOURCE_FACTORIES[normalized_name]()
    except KeyError as error:
        available = ", ".join(available_source_names())
        raise ValueError(
            f"Unknown source {name!r}. Available sources: {available}. "
            "Only registered safe adapters can be enabled."
        ) from error


def get_enabled_sources(enabled_source_names: Iterable[str] | None = None) -> list[DealSource]:
    """Return source adapters enabled by configuration.

    When no names are supplied, the safe mock source is enabled by default.
    """

    names = list(enabled_source_names or DEFAULT_ENABLED_SOURCES)
    return [get_source(name) for name in names]
