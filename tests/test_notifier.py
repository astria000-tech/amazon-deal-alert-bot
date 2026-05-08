"""Tests for Telegram and console notification behavior."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

from deal_alert_bot.models import Deal, ScoreResult
from deal_alert_bot.notifier import Notifier, build_alert_message


def make_deal() -> Deal:
    return Deal(
        deal_id="notifier-test-deal",
        title="Mock OLED Gaming Monitor Price Mistake",
        category="Computer peripherals",
        current_price=299.99,
        average_price_90d=1199.99,
        lowest_price_90d=899.99,
        url="https://example.com/mock/notifier-test-deal",
        source="mock",
        keywords=["OLED monitor", "gaming monitor"],
        signals=["price mistake"],
    )


def make_score_result() -> ScoreResult:
    return ScoreResult(
        score=95,
        reasons=[
            "current price is 75.0% below the 90-day average",
            "current price is below the 90-day lowest price",
            "matched suspicious signal(s): price mistake",
        ],
        discount_percent_vs_average=75.0,
    )


def test_build_alert_message_includes_deal_score_prices_and_url() -> None:
    deal = make_deal()
    score_result = make_score_result()

    message = build_alert_message(deal, score_result)

    assert "Mock OLED Gaming Monitor Price Mistake" in message
    assert "95/100" in message
    assert "$299.99" in message
    assert "$1,199.99" in message
    assert "$899.99" in message
    assert "75.0%" in message
    assert "https://example.com/mock/notifier-test-deal" in message
    assert "Computer peripherals" in message


@pytest.mark.parametrize(
    "reason",
    [
        "current price is 75.0% below the 90-day average",
        "current price is below the 90-day lowest price",
        "matched suspicious signal(s): price mistake",
    ],
)
def test_build_alert_message_includes_scoring_reasons(reason: str) -> None:
    message = build_alert_message(make_deal(), make_score_result())

    assert reason in message


def test_build_alert_message_includes_human_review_checklist() -> None:
    message = build_alert_message(make_deal(), make_score_result())

    assert "Verify the final price directly on the Amazon page" in message
    assert "Verify option- and quantity-specific pricing directly" in message
    assert "Verify whether coupons or promotions are applied" in message
    assert "Confirm the seller and fulfillment/shipping party" in message
    assert "order may be canceled" in message


def test_console_fallback_is_used_when_telegram_token_is_missing(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    post_was_called = False

    def fake_post(*args: Any, **kwargs: Any) -> None:
        nonlocal post_was_called
        post_was_called = True

    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(post=fake_post))
    notifier = Notifier(telegram_bot_token=None, telegram_chat_id="12345")

    assert notifier.send(make_deal(), make_score_result()) is True

    output = capsys.readouterr().out
    assert "CONSOLE ALERT FALLBACK (Telegram is not configured)" in output
    assert "Mock OLED Gaming Monitor Price Mistake" in output
    assert post_was_called is False


def test_telegram_send_failure_falls_back_without_raising(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_post(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("mock telegram outage")

    monkeypatch.setitem(sys.modules, "requests", SimpleNamespace(post=fake_post))
    notifier = Notifier(telegram_bot_token="mock-token", telegram_chat_id="12345")

    assert notifier.send(make_deal(), make_score_result()) is True

    output = capsys.readouterr().out
    assert "CONSOLE ALERT FALLBACK (Telegram send failed: mock telegram outage)" in output
    assert "Mock OLED Gaming Monitor Price Mistake" in output
