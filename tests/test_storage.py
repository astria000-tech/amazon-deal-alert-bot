"""Tests for SQLite alert-history storage."""

from __future__ import annotations

from pathlib import Path

from deal_alert_bot.models import Deal, ScoreResult
from deal_alert_bot.storage import AlertStorage


def make_deal(deal_id: str = "storage-test-deal") -> Deal:
    return Deal(
        deal_id=deal_id,
        title="Mock SSD price mistake",
        category="Computer components",
        current_price=49.99,
        average_price_90d=249.99,
        lowest_price_90d=149.99,
        url="https://example.com/mock/storage-test",
        source="mock",
        keywords=["SSD"],
        signals=["price mistake"],
    )


def test_new_deal_id_is_eligible_for_alert(tmp_path: Path) -> None:
    db_path = tmp_path / "alerts.sqlite3"
    storage = AlertStorage(db_path)

    assert storage.has_alerted("new-deal-id") is False
    assert db_path.exists()
    assert "data/alerts.sqlite3" not in db_path.as_posix()


def test_recorded_deal_id_blocks_duplicate_alerts(tmp_path: Path) -> None:
    db_path = tmp_path / "alerts.sqlite3"
    storage = AlertStorage(db_path)
    deal = make_deal()
    score_result = ScoreResult(score=90, reasons=["mock test reason"], discount_percent_vs_average=80.0)

    assert storage.has_alerted(deal.deal_id) is False

    storage.record_alert(deal, score_result)

    assert storage.has_alerted(deal.deal_id) is True


def test_storage_uses_temporary_sqlite_file_not_default_data_db(tmp_path: Path) -> None:
    db_path = tmp_path / "nested" / "test-alerts.sqlite3"
    storage = AlertStorage(db_path)
    deal = make_deal("temporary-db-deal")
    score_result = ScoreResult(score=75, reasons=["temporary sqlite file"], discount_percent_vs_average=72.0)

    storage.record_alert(deal, score_result)

    assert db_path.exists()
    assert db_path.is_file()
    assert Path("data/alerts.sqlite3") != db_path
