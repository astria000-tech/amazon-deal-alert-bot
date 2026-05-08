"""Run the mock-only Amazon suspicious error-deal alert bot MVP."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from deal_alert_bot.config import load_settings
from deal_alert_bot.notifier import Notifier
from deal_alert_bot.scoring import calculate_score
from deal_alert_bot.sources.mock import fetch_mock_deals
from deal_alert_bot.storage import AlertStorage


def main() -> int:
    settings = load_settings()
    storage = AlertStorage(settings.sqlite_db_path)
    notifier = Notifier(settings.telegram_bot_token, settings.telegram_chat_id)
    deals = fetch_mock_deals()

    print("Amazon suspicious error-deal alert bot MVP")
    print("Mode: mock data only; no Amazon login, cart automation, or purchasing")
    print(f"SQLite DB: {settings.sqlite_db_path}")
    print(f"Alert score threshold: {settings.alert_score_threshold}")
    print(f"Loaded mock deals: {len(deals)}")

    alerted_count = 0
    skipped_low_score_count = 0
    skipped_duplicate_count = 0

    for deal in deals:
        score_result = calculate_score(deal)
        print(
            f"- {deal.deal_id}: score={score_result.score}, "
            f"discount={score_result.discount_percent_vs_average:.1f}%"
        )

        if score_result.score < settings.alert_score_threshold:
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

    print("\nRun summary")
    print(f"- New alerts sent or printed: {alerted_count}")
    print(f"- Skipped below threshold: {skipped_low_score_count}")
    print(f"- Skipped duplicates: {skipped_duplicate_count}")
    print("- Safety: no purchasing, login automation, cart testing, coupon clicking, CAPTCHA bypass, or crawling performed")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
