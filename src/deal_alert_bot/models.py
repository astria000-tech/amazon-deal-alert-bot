"""Domain models for suspicious deal alerting."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Deal:
    """A deal candidate from a safe, non-automated source.

    The MVP only creates these from mock data. Future adapters should populate
    this model without adding purchasing, login, cart, coupon, CAPTCHA bypass, or
    high-volume crawling behavior.
    """

    deal_id: str
    title: str
    category: str
    current_price: float
    average_price_90d: float
    lowest_price_90d: float
    url: str
    source: str
    keywords: list[str] = field(default_factory=list)
    signals: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ScoreResult:
    """Scoring output for a deal candidate."""

    score: int
    reasons: list[str]
    discount_percent_vs_average: float
