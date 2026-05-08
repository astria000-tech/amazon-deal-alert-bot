"""Registry for safe deal source adapters."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from .base import DealSource
from .mock import MockDealSource

SourceFactory = Callable[[], DealSource]

DEFAULT_ENABLED_SOURCES = ["mock"]
_SOURCE_FACTORIES: dict[str, SourceFactory] = {
    "mock": MockDealSource,
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
