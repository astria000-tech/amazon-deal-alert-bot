"""Reddit source adapter skeleton with fake-client normalization support."""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from ..models import Deal
from .base import DealSource


class RedditClient(Protocol):
    """Minimal protocol for future Reddit clients and test fakes.

    The production Reddit API client is intentionally not implemented yet.
    Tests inject fake clients that return deterministic post dictionaries, so
    this module never needs to perform network calls during default runs or CI.
    """

    def fetch_posts(self, subreddits: list[str]) -> list[dict[str, Any]]:
        """Return post dictionaries to normalize into Deal models."""


REDDIT_SIGNAL_TERMS = {
    "price mistake",
    "pricing error",
    "glitch",
    "coupon glitch",
    "coupon stack",
    "promo code",
    "amazon",
    "buy 2",
    "subscribe",
}

REDDIT_KEYWORD_TERMS = {
    "monitor",
    "gaming monitor",
    "oled monitor",
    "ssd",
    "nvme",
    "ram",
    "keyboard",
    "mouse",
    "headset",
    "docking station",
    "usb hub",
}


class RedditDealSource(DealSource):
    """Safe Reddit source skeleton for future API integration.

    This adapter prepares Reddit posts as supplemental community deal signals
    only. It does not implement a production Reddit network client, crawl
    Amazon, automate accounts, purchase products, test carts, click coupons, or
    bypass anti-bot systems. A caller may inject a fake client for tests.
    """

    def __init__(
        self,
        client: RedditClient | None = None,
        subreddits: list[str] | None = None,
    ):
        self._client = client
        self._subreddits = [
            subreddit.strip() for subreddit in (subreddits or []) if subreddit.strip()
        ]

    @property
    def name(self) -> str:
        """Return the source registry name."""

        return "reddit"

    def fetch_deals(self) -> list[Deal]:
        """Fetch fake-client posts and normalize them into deal candidates.

        Until a safe, rate-limited Reddit API client is added in a future phase,
        missing clients or subreddit configuration safely produce no deals.
        """

        if self._client is None or not self._subreddits:
            return []

        deals: list[Deal] = []
        for post in self._client.fetch_posts(self._subreddits):
            deal = normalize_reddit_post(post)
            if deal is not None:
                deals.append(deal)
        return deals


def normalize_reddit_post(post: dict[str, Any]) -> Deal | None:
    """Normalize one Reddit post dictionary into a ``Deal`` candidate.

    Reddit posts do not provide reliable historical Amazon pricing, so price
    fields intentionally use invalid sentinels. The scorer treats these values
    as unavailable and relies on extracted community signals and target
    keywords rather than awarding price-drop points.
    """

    title = _clean_string(post.get("title"))
    if title is None:
        return None

    post_id = _clean_string(post.get("id")) or _stable_post_identifier(post)
    selftext = _clean_string(post.get("selftext")) or ""
    url = _read_post_url(post, post_id)
    searchable_text = f"{title} {selftext}"

    return Deal(
        deal_id=f"reddit-{post_id}",
        title=title,
        category="Community deal",
        current_price=-1.0,
        average_price_90d=-1.0,
        lowest_price_90d=-1.0,
        url=url,
        source="reddit",
        keywords=_extract_terms(searchable_text, REDDIT_KEYWORD_TERMS),
        signals=_extract_terms(searchable_text, REDDIT_SIGNAL_TERMS),
    )


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_post_url(post: dict[str, Any], post_id: str) -> str:
    url = _clean_string(post.get("url") or post.get("link"))
    if url is not None:
        return url

    permalink = _clean_string(post.get("permalink"))
    if permalink is not None:
        if permalink.startswith("http://") or permalink.startswith("https://"):
            return permalink
        return f"https://www.reddit.com{permalink}"

    return f"https://www.reddit.com/comments/{post_id}"


def _stable_post_identifier(post: dict[str, Any]) -> str:
    raw_identifier = "|".join(
        _clean_string(post.get(key)) or "" for key in ["title", "url", "permalink"]
    )
    return hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()[:16]


def _extract_terms(text: str, terms: set[str]) -> list[str]:
    lowered_text = text.lower()
    return sorted(term for term in terms if term.lower() in lowered_text)
