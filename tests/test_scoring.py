"""Tests for mock-only suspicious deal scoring."""

from __future__ import annotations

from deal_alert_bot.models import Deal, ScoreResult
from deal_alert_bot.scoring import calculate_score


def make_deal(**overrides: object) -> Deal:
    data = {
        "deal_id": "test-deal",
        "title": "Generic household item",
        "category": "Computer peripherals",
        "current_price": 95.0,
        "average_price_90d": 100.0,
        "lowest_price_90d": 90.0,
        "url": "https://example.com/mock/test-deal",
        "source": "mock",
        "keywords": [],
        "signals": [],
    }
    data.update(overrides)
    return Deal(**data)  # type: ignore[arg-type]


def test_deal_discounted_at_least_80_percent_gets_high_score() -> None:
    deal = make_deal(
        current_price=19.99,
        average_price_90d=100.0,
        lowest_price_90d=50.0,
        title="OLED monitor possible price mistake",
        keywords=["monitor"],
        signals=["price mistake"],
    )

    result = calculate_score(deal)

    assert result.score >= 80
    assert result.discount_percent_vs_average >= 80
    assert any("below the 90-day average" in reason for reason in result.reasons)


def test_low_discount_deal_scores_below_default_threshold() -> None:
    deal = make_deal(
        current_price=95.0,
        average_price_90d=100.0,
        lowest_price_90d=80.0,
        title="Wireless mouse standard sale",
        keywords=["mouse"],
    )

    result = calculate_score(deal)

    assert result.score < 70
    assert result.discount_percent_vs_average == 5.0


def test_interest_keywords_increase_score_and_reasons() -> None:
    base_deal = make_deal(title="Generic accessory", keywords=[])
    keyword_deal = make_deal(
        title="Monitor SSD RAM keyboard mouse headset bundle",
        keywords=["monitor", "SSD", "RAM", "keyboard", "mouse", "headset"],
    )

    base_result = calculate_score(base_deal)
    keyword_result = calculate_score(keyword_deal)

    assert keyword_result.score > base_result.score
    assert any("matched target keyword(s)" in reason for reason in keyword_result.reasons)
    assert any("monitor" in reason for reason in keyword_result.reasons)
    assert any("ssd" in reason for reason in keyword_result.reasons)


def test_suspicious_signals_increase_score_and_reasons() -> None:
    base_deal = make_deal(title="Generic accessory", signals=[])
    signal_deal = make_deal(
        title="Price mistake pricing error glitch coupon stack promo code bundle",
        signals=["price mistake", "pricing error", "glitch", "coupon stack", "promo code"],
    )

    base_result = calculate_score(base_deal)
    signal_result = calculate_score(signal_deal)

    assert signal_result.score > base_result.score
    assert any("matched suspicious signal(s)" in reason for reason in signal_result.reasons)
    for signal in ["price mistake", "pricing error", "glitch", "coupon stack", "promo code"]:
        assert any(signal in reason for reason in signal_result.reasons)


def test_score_result_contains_score_and_reasons() -> None:
    deal = make_deal(
        current_price=40.0,
        average_price_90d=100.0,
        lowest_price_90d=50.0,
        keywords=["keyboard"],
        signals=["promo code"],
    )

    result = calculate_score(deal)

    assert isinstance(result, ScoreResult)
    assert isinstance(result.score, int)
    assert result.score > 0
    assert isinstance(result.reasons, list)
    assert result.reasons
    assert all(isinstance(reason, str) for reason in result.reasons)


def test_unavailable_price_history_does_not_award_price_drop_points() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=49.99,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Monitor price mistake glitch coupon stack promo code",
        keywords=["monitor"],
        signals=["price mistake", "glitch", "coupon stack", "promo code"],
    )

    result = calculate_score(deal)

    assert result.discount_percent_vs_average == 0.0
    assert result.score == 100
    assert any("average price is unavailable" in reason for reason in result.reasons)
    assert not any("below the 90-day average" in reason for reason in result.reasons)
    assert not any("below the 90-day lowest price" in reason for reason in result.reasons)


def test_slickdeals_price_mistake_clears_threshold_30_without_price_history() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=19.99,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Amazon price mistake SSD",
        keywords=["ssd"],
        signals=["price mistake", "amazon"],
    )

    result = calculate_score(deal)

    assert result.score >= 30
    assert any("price mistake (+50)" in reason for reason in result.reasons)
    assert any("slickdeals source baseline: +5" in reason for reason in result.reasons)


def test_slickdeals_glitch_gets_meaningful_score_without_price_history() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=-1.0,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Checkout page shows glitch for headset",
        keywords=["headset"],
        signals=["glitch"],
    )

    result = calculate_score(deal)

    assert result.score >= 50
    assert any("glitch (+40)" in reason for reason in result.reasons)


def test_slickdeals_coupon_stack_and_amazon_are_scored() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=25.0,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Amazon coupon stack promo code keyboard",
        keywords=["keyboard"],
        signals=["coupon stack", "amazon", "promo code"],
    )

    result = calculate_score(deal)

    assert result.score >= 70
    assert any("coupon stack (+35)" in reason for reason in result.reasons)
    assert any("amazon (+10)" in reason for reason in result.reasons)


def test_slickdeals_interest_keywords_are_weighted_by_category() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=99.99,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Monitor SSD RAM upgrade bundle",
        keywords=["monitor", "SSD", "RAM"],
        signals=[],
    )

    result = calculate_score(deal)

    assert result.score == 50
    assert any("monitor (+15)" in reason for reason in result.reasons)
    assert any("ssd (+15)" in reason for reason in result.reasons)
    assert any("ram (+15)" in reason for reason in result.reasons)


def test_generic_slickdeals_item_does_not_score_too_high() -> None:
    deal = make_deal(
        source="slickdeals",
        current_price=12.99,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="Generic kitchen accessory sale",
        keywords=[],
        signals=[],
    )

    result = calculate_score(deal)

    assert result.score == 5


def test_duplicate_slickdeals_signals_and_keywords_are_scored_once() -> None:
    duplicate_deal = make_deal(
        source="slickdeals",
        current_price=10.0,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="PRICE MISTAKE price mistake monitor MONITOR",
        keywords=["monitor", "MONITOR"],
        signals=["price mistake", "PRICE MISTAKE"],
    )
    single_deal = make_deal(
        source="slickdeals",
        current_price=10.0,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        title="price mistake monitor",
        keywords=["monitor"],
        signals=["price mistake"],
    )

    assert calculate_score(duplicate_deal).score == calculate_score(single_deal).score
