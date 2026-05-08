"""Suspicious error-deal scoring rules."""

from __future__ import annotations

from .models import Deal, ScoreResult

INTEREST_KEYWORDS = {
    "monitor",
    "gaming monitor",
    "oled monitor",
    "ssd",
    "nvme",
    "ram",
    "ddr4",
    "ddr5",
    "keyboard",
    "mechanical keyboard",
    "mouse",
    "wireless mouse",
    "headset",
    "docking station",
    "usb hub",
    "robot vacuum",
    "air purifier",
    "coffee machine",
    "tv",
    "soundbar",
}

HIGH_SIGNAL_TERMS = {
    "price mistake",
    "glitch",
    "coupon stack",
    "promo code",
}


def _normalized_terms(deal: Deal) -> set[str]:
    title = deal.title.lower()
    return {term.lower() for term in [*deal.keywords, *deal.signals, title]}


def calculate_score(deal: Deal) -> ScoreResult:
    """Calculate a suspicious-deal score and human-readable reasons."""

    score = 0
    reasons: list[str] = []

    if deal.average_price_90d <= 0:
        reasons.append("90-day average price is unavailable or invalid")
        return ScoreResult(score=0, reasons=reasons, discount_percent_vs_average=0.0)

    discount_percent = (
        (deal.average_price_90d - deal.current_price) / deal.average_price_90d
    ) * 100

    if discount_percent >= 80:
        score += 60
        reasons.append(
            f"current price is {discount_percent:.1f}% below the 90-day average"
        )
    elif discount_percent >= 70:
        score += 45
        reasons.append(
            f"current price is {discount_percent:.1f}% below the 90-day average"
        )
    elif discount_percent >= 50:
        score += 25
        reasons.append(
            f"current price is {discount_percent:.1f}% below the 90-day average"
        )
    elif discount_percent > 0:
        score += 10
        reasons.append(
            f"current price is {discount_percent:.1f}% below the 90-day average"
        )
    else:
        reasons.append("current price is not below the 90-day average")

    if deal.current_price < deal.lowest_price_90d:
        score += 20
        reasons.append("current price is below the 90-day lowest price")

    searchable_text = " ".join(_normalized_terms(deal))
    matched_keywords = sorted(
        keyword for keyword in INTEREST_KEYWORDS if keyword in searchable_text
    )
    if matched_keywords:
        keyword_points = min(20, len(matched_keywords) * 5)
        score += keyword_points
        reasons.append(
            "matched target keyword(s): " + ", ".join(matched_keywords)
        )

    matched_signals = sorted(
        signal for signal in HIGH_SIGNAL_TERMS if signal in searchable_text
    )
    if matched_signals:
        signal_points = min(25, len(matched_signals) * 10)
        score += signal_points
        reasons.append("matched suspicious signal(s): " + ", ".join(matched_signals))

    return ScoreResult(
        score=min(score, 100),
        reasons=reasons,
        discount_percent_vs_average=discount_percent,
    )
