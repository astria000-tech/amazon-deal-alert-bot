"""Telegram and console notification delivery."""

from __future__ import annotations

import importlib

from .models import Deal, ScoreResult

HUMAN_REVIEW_CHECKLIST = [
    "Verify the final price directly on the Amazon page",
    "Verify option- and quantity-specific pricing directly",
    "Verify whether coupons or promotions are applied",
    "Confirm the seller and fulfillment/shipping party",
    "Account for the possibility that an order may be canceled after placement",
]


def build_alert_message(deal: Deal, score_result: ScoreResult) -> str:
    """Build a human-review alert message without performing delivery side effects."""

    reasons = score_result.reasons or ["No scoring reasons were provided"]
    reason_lines = "\n".join(f"- {reason}" for reason in reasons)
    review_lines = "\n".join(f"- {item}" for item in HUMAN_REVIEW_CHECKLIST)

    return "\n".join(
        [
            "🚨 Suspicious Amazon Deal Candidate (Human Review Required)",
            "",
            f"Suspicion score: {score_result.score}/100",
            f"Product: {deal.title}",
            f"Category: {deal.category}",
            f"Current price: ${deal.current_price:,.2f}",
            f"90-day average price: ${deal.average_price_90d:,.2f}",
            f"90-day lowest price: ${deal.lowest_price_90d:,.2f}",
            f"Discount vs 90-day average: {score_result.discount_percent_vs_average:.1f}%",
            "",
            "Reasons:",
            reason_lines,
            "",
            f"Product URL: {deal.url}",
            "",
            "Human verification checklist:",
            review_lines,
            "",
            "Safety note: This bot only sends alerts. It does not buy, log in, test carts, click coupons, bypass CAPTCHA, or crawl Amazon.",
        ]
    )


class Notifier:
    """Send alerts to Telegram when configured, otherwise print to console."""

    def __init__(self, telegram_bot_token: str | None, telegram_chat_id: str | None) -> None:
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def build_message(self, deal: Deal, score_result: ScoreResult) -> str:
        """Build the notification text for this deal."""

        return build_alert_message(deal, score_result)

    def send(self, deal: Deal, score_result: ScoreResult) -> bool:
        """Send a notification.

        Returns True when Telegram succeeds or when console fallback is printed.
        Telegram failures are caught and converted into console fallback output so
        the MVP continues to run safely.
        """

        message = build_alert_message(deal, score_result)

        if not self.telegram_bot_token or not self.telegram_chat_id:
            self._print_console_fallback(message, "Telegram is not configured")
            return True

        api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        try:
            requests = importlib.import_module("requests")
            response = requests.post(
                api_url,
                json={"chat_id": self.telegram_chat_id, "text": message},
                timeout=10,
            )
            response.raise_for_status()
            print(f"Telegram alert sent for deal_id={deal.deal_id}")
            return True
        except Exception as error:
            self._print_console_fallback(message, f"Telegram send failed: {error}")
            return True

    @staticmethod
    def _print_console_fallback(message: str, reason: str) -> None:
        print("\n" + "=" * 72)
        print(f"CONSOLE ALERT FALLBACK ({reason})")
        print("=" * 72)
        print(message)
        print("=" * 72 + "\n")
