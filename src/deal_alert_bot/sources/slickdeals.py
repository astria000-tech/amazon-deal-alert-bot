"""Slickdeals RSS source adapter for public, user-configured feeds."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from typing import Any

from ..models import Deal
from ..scoring import HIGH_SIGNAL_TERMS, INTEREST_KEYWORDS
from .base import DealSource

RSSParser = Callable[[str], Any]

_PRICE_PATTERN = re.compile(r"(?<![\w.])\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")


class SlickdealsRssSource(DealSource):
    """Fetch user-configured Slickdeals RSS feeds and normalize entries.

    This adapter only reads public RSS URLs explicitly supplied by the user. It
    does not crawl Amazon, automate accounts, purchase products, test carts,
    click coupons, or bypass anti-bot systems.
    """

    def __init__(self, rss_urls: list[str] | None = None, parser: RSSParser | None = None):
        self._rss_urls = [url.strip() for url in (rss_urls or []) if url.strip()]
        self._parser = parser or _default_feedparser_parse

    @property
    def name(self) -> str:
        """Return the source registry name."""

        return "slickdeals"

    def fetch_deals(self) -> list[Deal]:
        """Fetch configured RSS URLs and return normalized deal candidates.

        Missing RSS URLs safely produce an empty result. Parser/network failures
        are isolated per URL so one unavailable feed cannot stop the bot run.
        """

        if not self._rss_urls:
            return []

        deals: list[Deal] = []
        for rss_url in self._rss_urls:
            try:
                parsed_feed = self._parser(rss_url)
                entries = _read_entries(parsed_feed)
            except Exception as error:
                print(f"WARNING: Slickdeals RSS URL failed and was skipped: {error}")
                continue

            for entry in entries:
                deal = normalize_slickdeals_entry(entry)
                if deal is not None:
                    deals.append(deal)

        return deals


def normalize_slickdeals_entry(entry: dict[str, Any] | Any) -> Deal | None:
    """Normalize one Slickdeals RSS entry into a ``Deal`` candidate.

    RSS entries do not provide reliable historical Amazon pricing, so the
    resulting deal intentionally uses invalid historical-price sentinels. The
    scorer treats those values as unavailable and relies on keywords/signals
    rather than awarding price-drop points.
    """

    title = _clean_string(_read_entry_value(entry, "title"))
    link = _clean_string(_read_entry_value(entry, "link"))
    if title is None or link is None:
        return None

    summary = _clean_string(
        _read_entry_value(entry, "summary")
        or _read_entry_value(entry, "description")
        or _read_entry_value(entry, "content")
    ) or ""
    published = _clean_string(
        _read_entry_value(entry, "published")
        or _read_entry_value(entry, "updated")
        or _read_entry_value(entry, "pubDate")
    )
    identifier = (
        _clean_string(_read_entry_value(entry, "guid"))
        or _clean_string(_read_entry_value(entry, "id"))
        or link
    )
    deal_id = "slickdeals-" + hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:16]

    searchable_text = f"{title} {summary}"
    keywords = _extract_terms(searchable_text, INTEREST_KEYWORDS)
    signals = _extract_terms(searchable_text, HIGH_SIGNAL_TERMS | {"amazon"})
    current_price = _extract_price(searchable_text) or -1.0

    return Deal(
        deal_id=deal_id,
        title=title,
        category=_infer_category(keywords),
        current_price=current_price,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        url=link,
        source="slickdeals",
        keywords=keywords,
        signals=_append_published_signal(signals, published),
    )


def _default_feedparser_parse(rss_url: str) -> Any:
    import feedparser

    return feedparser.parse(rss_url)


def _read_entries(parsed_feed: Any) -> list[Any]:
    entries = _read_entry_value(parsed_feed, "entries")
    if entries is None:
        return []
    return list(entries)


def _read_entry_value(entry: Any, key: str) -> Any:
    if isinstance(entry, dict):
        return entry.get(key)
    return getattr(entry, key, None)


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list | tuple) and value:
        value = value[0]
    if isinstance(value, dict):
        value = value.get("value") or value.get("text")
    text = str(value).strip()
    return text or None


def _extract_price(text: str) -> float | None:
    match = _PRICE_PATTERN.search(text)
    if match is None:
        return None
    try:
        return round(float(match.group(1).replace(",", "")), 2)
    except ValueError:
        return None


def _extract_terms(text: str, terms: set[str]) -> list[str]:
    lowered_text = text.lower()
    return sorted(term for term in terms if term.lower() in lowered_text)


def _infer_category(keywords: list[str]) -> str:
    lowered_keywords = {keyword.lower() for keyword in keywords}
    if {"ssd", "nvme", "ram", "ddr4", "ddr5"} & lowered_keywords:
        return "Computer components"
    if {
        "monitor",
        "gaming monitor",
        "oled monitor",
        "keyboard",
        "mechanical keyboard",
        "mouse",
        "wireless mouse",
        "headset",
        "docking station",
        "usb hub",
    } & lowered_keywords:
        return "Computer peripherals"
    if {"robot vacuum", "air purifier", "coffee machine"} & lowered_keywords:
        return "Appliances"
    return "Community deal"


def _append_published_signal(signals: list[str], published: str | None) -> list[str]:
    if published is None:
        return signals
    return [*signals, f"published: {published}"]
