"""Tests for safe deal source adapters and registry."""

from __future__ import annotations

from pathlib import Path

import pytest

import main
from deal_alert_bot.models import Deal, ScoreResult
from deal_alert_bot.notifier import Notifier
from deal_alert_bot.sources.base import DealSource
from deal_alert_bot.sources.keepa import KeepaDealSource
from deal_alert_bot.sources.mock import MockDealSource, fetch_mock_deals
from deal_alert_bot.sources.registry import (
    available_source_names,
    get_enabled_sources,
    get_source,
)
from deal_alert_bot.storage import AlertStorage


class FakeNotifier(Notifier):
    """Notifier double that records sends without network calls."""

    def __init__(self) -> None:
        super().__init__(telegram_bot_token=None, telegram_chat_id=None)
        self.sent: list[tuple[Deal, ScoreResult]] = []

    def send(self, deal: Deal, score_result: ScoreResult) -> bool:
        self.sent.append((deal, score_result))
        return True


class FailingSource(DealSource):
    @property
    def name(self) -> str:
        return "failing"

    def fetch_deals(self) -> list[Deal]:
        raise RuntimeError("synthetic source failure")


def test_mock_deal_source_fetches_deal_models() -> None:
    source = MockDealSource()

    deals = source.fetch_deals()

    assert source.name == "mock"
    assert deals
    assert all(isinstance(deal, Deal) for deal in deals)
    assert {deal.source for deal in deals} == {"mock"}


def test_fetch_mock_deals_compatibility_wrapper_returns_deal_models() -> None:
    deals = fetch_mock_deals()

    assert deals
    assert all(isinstance(deal, Deal) for deal in deals)


def test_registry_defaults_to_mock_source() -> None:
    sources = get_enabled_sources()

    assert len(sources) == 1
    assert isinstance(sources[0], MockDealSource)
    assert sources[0].name == "mock"


def test_available_source_names_includes_mock_and_keepa() -> None:
    assert set(available_source_names()) >= {"mock", "keepa"}


def test_registry_returns_mock_source_by_name() -> None:
    source = get_source(" mock ")

    assert isinstance(source, MockDealSource)


def test_registry_returns_keepa_source_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KEEPA_API_KEY", raising=False)

    source = get_source(" keepa ")

    assert isinstance(source, KeepaDealSource)
    assert source.name == "keepa"


def test_registry_returns_enabled_mock_and_keepa_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("KEEPA_API_KEY", raising=False)

    sources = get_enabled_sources(["mock", "keepa"])

    assert len(sources) == 2
    assert isinstance(sources[0], MockDealSource)
    assert isinstance(sources[1], KeepaDealSource)


def test_registry_unknown_source_fails_closed() -> None:
    with pytest.raises(ValueError, match="Unknown source"):
        get_enabled_sources(["mock", "unknown-source"])


def test_fetch_deals_from_sources_continues_after_source_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    deals = main.fetch_deals_from_sources([FailingSource(), MockDealSource()])

    output = capsys.readouterr().out
    assert "WARNING: source 'failing' failed" in output
    assert "Loaded 6 deal(s) from source: mock" in output
    assert len(deals) == 6


def test_fetch_deals_from_sources_isolates_keepa_missing_key_failure(
    capsys: pytest.CaptureFixture[str],
) -> None:
    deals = main.fetch_deals_from_sources([MockDealSource(), KeepaDealSource(api_key=None)])

    output = capsys.readouterr().out
    assert "Loaded 6 deal(s) from source: mock" in output
    assert "WARNING: source 'keepa' failed" in output
    assert "KEEPA_API_KEY" in output
    assert len(deals) == 6


def test_main_processing_flow_scores_stores_and_notifies_source_deals(tmp_path: Path) -> None:
    storage = AlertStorage(tmp_path / "alerts.sqlite3")
    notifier = FakeNotifier()
    deals = MockDealSource().fetch_deals()

    summary = main.process_deals(
        deals=deals,
        alert_score_threshold=70,
        storage=storage,
        notifier=notifier,
    )

    assert summary.alerted_count == len(notifier.sent)
    assert summary.alerted_count > 0
    assert summary.skipped_low_score_count > 0
    assert all(storage.has_alerted(deal.deal_id) for deal, _ in notifier.sent)
