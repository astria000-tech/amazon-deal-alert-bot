"""Telegram and console notification delivery."""

from __future__ import annotations

import importlib

from .models import Deal, ScoreResult


class Notifier:
    """Send alerts to Telegram when configured, otherwise print to console."""

    def __init__(self, telegram_bot_token: str | None, telegram_chat_id: str | None) -> None:
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def build_message(self, deal: Deal, score_result: ScoreResult) -> str:
        reasons = "\n".join(f"- {reason}" for reason in score_result.reasons)
        return "\n".join(
            [
                "🚨 Suspicious Amazon Deal Candidate",
                "",
                f"Title: {deal.title}",
                f"Category: {deal.category}",
                f"Source: {deal.source}",
                f"Current price: ${deal.current_price:,.2f}",
                f"90-day average: ${deal.average_price_90d:,.2f}",
                f"90-day lowest: ${deal.lowest_price_90d:,.2f}",
                f"Score: {score_result.score}/100",
                "Reasons:",
                reasons,
                f"URL: {deal.url}",
            ]
        )

    def send(self, deal: Deal, score_result: ScoreResult) -> bool:
        """Send a notification.

        Returns True when Telegram succeeds or when console fallback is printed.
        Telegram failures are caught and converted into console fallback output so
        the MVP continues to run safely.
        """

        message = self.build_message(deal, score_result)

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
