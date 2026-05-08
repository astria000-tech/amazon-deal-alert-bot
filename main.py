"""Run the mock-only Amazon suspicious error-deal alert bot MVP."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deal_alert_bot.config import load_settings
from deal_alert_bot.models import Deal
from deal_alert_bot.notifier import Notifier
from deal_alert_bot.scoring import calculate_score
from deal_alert_bot.sources.base import DealSource
from deal_alert_bot.sources.registry import get_enabled_sources
from deal_alert_bot.storage import AlertStorage


@dataclass(frozen=True)
class RunSummary:
    """Counters from one alert bot run."""

    alerted_count: int
    skipped_low_score_count: int
    skipped_duplicate_count: int


def fetch_deals_from_sources(sources: list[DealSource]) -> list[Deal]:
    """Fetch deals from enabled sources without letting one source kill the run."""

    deals: list[Deal] = []
    for source in sources:
        try:
            source_deals = source.fetch_deals()
        except Exception as error:
            print(f"WARNING: source {source.name!r} failed to fetch deals: {error}")
            continue

        print(f"Loaded {len(source_deals)} deal(s) from source: {source.name}")
        deals.extend(source_deals)

    return deals


def process_deals(
    deals: list[Deal],
    alert_score_threshold: int,
    storage: AlertStorage,
    notifier: Notifier,
) -> RunSummary:
    """Score, de-duplicate, and notify about fetched deal candidates."""

    alerted_count = 0
    skipped_low_score_count = 0
    skipped_duplicate_count = 0

    for deal in deals:
        score_result = calculate_score(deal)
        print(
            f"- {deal.deal_id}: source={deal.source}, score={score_result.score}, "
            f"discount={score_result.discount_percent_vs_average:.1f}%"
        )

        if score_result.score < alert_score_threshold:
            skipped_low_score_count += 1
            print("  skipped: below threshold")
            continue

        if storage.has_alerted(deal.deal_id):
            skipped_duplicate_count += 1
            print("  skipped: duplicate alert already recorded")
            continue

        if notifier.send(deal, score_result):
            storage.record_alert(deal, score_result)
            alerted_count += 1
            print("  alerted and recorded")
        else:
            print("  notification failed; alert history was not recorded")

    return RunSummary(
        alerted_count=alerted_count,
        skipped_low_score_count=skipped_low_score_count,
        skipped_duplicate_count=skipped_duplicate_count,
    )


def main() -> int:
    settings = load_settings()
    storage = AlertStorage(settings.sqlite_db_path)
    notifier = Notifier(settings.telegram_bot_token, settings.telegram_chat_id)

    print("Amazon suspicious error-deal alert bot MVP")
    print("Mode: mock data only; no Amazon login, cart automation, or purchasing")
    print(f"SQLite DB: {settings.sqlite_db_path}")
    print(f"Alert score threshold: {settings.alert_score_threshold}")
    print(f"Enabled sources: {', '.join(settings.enabled_sources)}")

    try:
        sources = get_enabled_sources(settings.enabled_sources)
    except ValueError as error:
        print(f"Configuration error: {error}")
        return 1

    deals = fetch_deals_from_sources(sources)
    print(f"Loaded total deals: {len(deals)}")
    summary = process_deals(deals, settings.alert_score_threshold, storage, notifier)

    print("\nRun summary")
    print(f"- New alerts sent or printed: {summary.alerted_count}")
    print(f"- Skipped below threshold: {summary.skipped_low_score_count}")
    print(f"- Skipped duplicates: {summary.skipped_duplicate_count}")
    print("- Safety: no purchasing, login automation, cart testing, coupon clicking, CAPTCHA bypass, or crawling performed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
