"""Tests for the Slickdeals RSS source adapter."""

from __future__ import annotations

from typing import Any

from deal_alert_bot.models import Deal
from deal_alert_bot.sources.slickdeals import (
    SlickdealsRssSource,
    normalize_slickdeals_entry,
)


class FakeRssParser:
    """Deterministic parser double that never performs network calls."""

    def __init__(self, entries_by_url: dict[str, list[dict[str, Any]]]):
        self.entries_by_url = entries_by_url
        self.called_urls: list[str] = []

    def __call__(self, rss_url: str) -> dict[str, list[dict[str, Any]]]:
        self.called_urls.append(rss_url)
        return {"entries": self.entries_by_url.get(rss_url, [])}


class FailingRssParser:
    def __call__(self, rss_url: str) -> dict[str, list[dict[str, Any]]]:
        raise RuntimeError(f"synthetic parser failure for {rss_url}")


def fake_entry() -> dict[str, str]:
    return {
        "id": "slickdeals-fake-entry-1",
        "title": "Amazon monitor SSD RAM keyboard mouse headset price mistake $49.99",
        "summary": "Glitch deal with coupon stack and promo code for human review only.",
        "link": "https://slickdeals.example/deals/fake-entry-1",
        "published": "Fri, 08 May 2026 12:00:00 GMT",
    }


def test_slickdeals_source_name_is_slickdeals() -> None:
    source = SlickdealsRssSource(rss_urls=[], parser=FakeRssParser({}))

    assert source.name == "slickdeals"


def test_no_rss_urls_returns_empty_without_calling_parser() -> None:
    parser = FakeRssParser({})
    source = SlickdealsRssSource(rss_urls=[], parser=parser)

    assert source.fetch_deals() == []
    assert parser.called_urls == []


def test_fake_rss_entry_is_converted_to_deal_without_network() -> None:
    parser = FakeRssParser({"https://feeds.example/rss": [fake_entry()]})
    source = SlickdealsRssSource(rss_urls=["https://feeds.example/rss"], parser=parser)

    deals = source.fetch_deals()

    assert parser.called_urls == ["https://feeds.example/rss"]
    assert len(deals) == 1
    assert isinstance(deals[0], Deal)
    assert deals[0].source == "slickdeals"
    assert deals[0].url == "https://slickdeals.example/deals/fake-entry-1"
    assert deals[0].current_price == 49.99
    assert deals[0].average_price_90d == -1.0
    assert deals[0].lowest_price_90d == -1.0


def test_entries_without_title_or_link_are_skipped() -> None:
    parser = FakeRssParser(
        {
            "https://feeds.example/rss": [
                {**fake_entry(), "title": ""},
                {**fake_entry(), "link": None},
                fake_entry(),
            ]
        }
    )
    source = SlickdealsRssSource(rss_urls=["https://feeds.example/rss"], parser=parser)

    deals = source.fetch_deals()

    assert len(deals) == 1
    assert deals[0].title == fake_entry()["title"]


def test_suspicious_signals_are_extracted_from_title_and_summary() -> None:
    deal = normalize_slickdeals_entry(fake_entry())

    assert deal is not None
    for signal in ["amazon", "price mistake", "glitch", "coupon stack", "promo code"]:
        assert signal in deal.signals


def test_target_keywords_are_extracted_from_title_and_summary() -> None:
    deal = normalize_slickdeals_entry(fake_entry())

    assert deal is not None
    for keyword in ["monitor", "ssd", "ram", "keyboard", "mouse", "headset"]:
        assert keyword in deal.keywords


def test_parser_failure_is_skipped_without_killing_fetch(capsys) -> None:  # type: ignore[no-untyped-def]
    source = SlickdealsRssSource(
        rss_urls=["https://feeds.example/rss"],
        parser=FailingRssParser(),
    )

    assert source.fetch_deals() == []
    output = capsys.readouterr().out
    assert "WARNING: Slickdeals RSS URL failed" in output


def test_multiple_urls_continue_after_one_parser_failure() -> None:
    class PartiallyFailingParser:
        def __call__(self, rss_url: str) -> dict[str, list[dict[str, Any]]]:
            if rss_url == "https://feeds.example/bad-rss":
                raise RuntimeError("bad feed")
            return {"entries": [fake_entry()]}

    source = SlickdealsRssSource(
        rss_urls=["https://feeds.example/bad-rss", "https://feeds.example/good-rss"],
        parser=PartiallyFailingParser(),
    )

    deals = source.fetch_deals()

    assert len(deals) == 1
    assert deals[0].source == "slickdeals"
