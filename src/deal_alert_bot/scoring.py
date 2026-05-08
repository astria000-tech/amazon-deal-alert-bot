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

KEYWORD_SCORE_POINTS = {
    "monitor": 15,
    "gaming monitor": 15,
    "oled monitor": 15,
    "ssd": 15,
    "nvme": 15,
    "ram": 15,
    "ddr4": 15,
    "ddr5": 15,
    "keyboard": 10,
    "mechanical keyboard": 10,
    "mouse": 10,
    "wireless mouse": 10,
    "headset": 10,
    "docking station": 10,
    "usb hub": 10,
    "robot vacuum": 5,
    "air purifier": 5,
    "coffee machine": 5,
    "tv": 5,
    "soundbar": 5,
}

SIGNAL_SCORE_POINTS = {
    "price mistake": 50,
    "pricing error": 50,
    "glitch": 40,
    "coupon glitch": 40,
    "coupon stack": 35,
    "promo code": 20,
    "buy 2": 15,
    "subscribe": 10,
    "amazon": 10,
}

HIGH_SIGNAL_TERMS = set(SIGNAL_SCORE_POINTS)
SLICKDEALS_SOURCE_BASE_POINTS = 5


def _normalized_terms(deal: Deal) -> set[str]:
    return {term.lower() for term in [deal.title, *deal.keywords, *deal.signals]}


def _matched_scored_terms(searchable_text: str, points_by_term: dict[str, int]) -> list[str]:
    """Return case-normalized scored terms, suppressing nested duplicate phrases."""

    raw_matches = [term for term in points_by_term if term in searchable_text]
    suppressed: set[str] = set()
    for term in raw_matches:
        if any(term != other and term in other for other in raw_matches):
            suppressed.add(term)
    return sorted(term for term in raw_matches if term not in suppressed)


def calculate_score(deal: Deal) -> ScoreResult:
    """Calculate a suspicious-deal score and human-readable reasons."""

    score = 0
    reasons: list[str] = []

    discount_percent = 0.0
    has_current_price = deal.current_price > 0
    has_average_price = deal.average_price_90d > 0

    if has_current_price and has_average_price:
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
    else:
        reasons.append("current or 90-day average price is unavailable or invalid")

    if has_current_price and deal.lowest_price_90d > 0:
        if deal.current_price < deal.lowest_price_90d:
            score += 20
            reasons.append("current price is below the 90-day lowest price")
    else:
        reasons.append("90-day lowest price is unavailable or invalid")

    if deal.source.lower() == "slickdeals":
        score += SLICKDEALS_SOURCE_BASE_POINTS
        reasons.append(
            f"slickdeals source baseline: +{SLICKDEALS_SOURCE_BASE_POINTS}"
        )

    searchable_text = " ".join(_normalized_terms(deal))
    matched_keywords = _matched_scored_terms(searchable_text, KEYWORD_SCORE_POINTS)
    if matched_keywords:
        keyword_points = sum(KEYWORD_SCORE_POINTS[keyword] for keyword in matched_keywords)
        score += keyword_points
        reasons.append(
            "matched target keyword(s): "
            + ", ".join(
                f"{keyword} (+{KEYWORD_SCORE_POINTS[keyword]})"
                for keyword in matched_keywords
            )
        )

    matched_signals = _matched_scored_terms(searchable_text, SIGNAL_SCORE_POINTS)
    if matched_signals:
        signal_points = sum(SIGNAL_SCORE_POINTS[signal] for signal in matched_signals)
        score += signal_points
        reasons.append(
            "matched suspicious signal(s): "
            + ", ".join(
                f"{signal} (+{SIGNAL_SCORE_POINTS[signal]})"
                for signal in matched_signals
            )
        )

    return ScoreResult(
        score=min(score, 100),
        reasons=reasons,
        discount_percent_vs_average=discount_percent,
    )
