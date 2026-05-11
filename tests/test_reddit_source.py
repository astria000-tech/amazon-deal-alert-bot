"""Tests for the Reddit source skeleton."""

from __future__ import annotations

from typing import Any

from deal_alert_bot.models import Deal
from deal_alert_bot.sources.reddit import RedditDealSource, normalize_reddit_post


class FakeRedditClient:
    """Deterministic Reddit client double that never performs network calls."""

    def __init__(self, posts: list[dict[str, Any]]):
        self.posts = posts
        self.called_subreddits: list[list[str]] = []

    def fetch_posts(self, subreddits: list[str]) -> list[dict[str, Any]]:
        self.called_subreddits.append(list(subreddits))
        return self.posts


def fake_post() -> dict[str, str]:
    return {
        "id": "abc123",
        "title": "Amazon price mistake glitch on gaming monitor OLED monitor SSD RAM keyboard mouse",
        "selftext": "Pricing error with coupon glitch, coupon stack, promo code, buy 2, subscribe, NVMe, headset, docking station, and USB hub. Human review only.",
        "url": "https://reddit.example/r/priceglitch/comments/abc123/deal",
        "permalink": "/r/priceglitch/comments/abc123/deal/",
    }


def test_reddit_source_name_is_reddit() -> None:
    source = RedditDealSource(client=FakeRedditClient([]), subreddits=["priceglitch"])

    assert source.name == "reddit"


def test_fake_client_posts_are_converted_to_deals_without_network() -> None:
    client = FakeRedditClient([fake_post()])
    source = RedditDealSource(
        client=client,
        subreddits=["priceglitch", "buildapcsales", "dealsonamazon"],
    )

    deals = source.fetch_deals()

    assert client.called_subreddits == [["priceglitch", "buildapcsales", "dealsonamazon"]]
    assert len(deals) == 1
    assert isinstance(deals[0], Deal)
    assert deals[0].deal_id == "reddit-abc123"
    assert deals[0].source == "reddit"
    assert deals[0].category == "Community deal"
    assert deals[0].url == "https://reddit.example/r/priceglitch/comments/abc123/deal"
    assert deals[0].current_price == -1.0
    assert deals[0].average_price_90d == -1.0
    assert deals[0].lowest_price_90d == -1.0


def test_missing_client_or_subreddits_returns_empty_without_network() -> None:
    client = FakeRedditClient([fake_post()])

    assert RedditDealSource(client=None, subreddits=["priceglitch"]).fetch_deals() == []
    assert RedditDealSource(client=client, subreddits=[]).fetch_deals() == []
    assert client.called_subreddits == []


def test_posts_without_title_are_skipped() -> None:
    client = FakeRedditClient(
        [
            {**fake_post(), "title": ""},
            {**fake_post(), "title": None},
            fake_post(),
        ]
    )
    source = RedditDealSource(client=client, subreddits=["priceglitch"])

    deals = source.fetch_deals()

    assert len(deals) == 1
    assert deals[0].title == fake_post()["title"]


def test_suspicious_signals_are_extracted_from_title_and_selftext() -> None:
    deal = normalize_reddit_post(fake_post())

    assert deal is not None
    for signal in [
        "amazon",
        "price mistake",
        "pricing error",
        "glitch",
        "coupon glitch",
        "coupon stack",
        "promo code",
        "buy 2",
        "subscribe",
    ]:
        assert signal in deal.signals


def test_target_keywords_are_extracted_from_title_and_selftext() -> None:
    deal = normalize_reddit_post(fake_post())

    assert deal is not None
    for keyword in [
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
    ]:
        assert keyword in deal.keywords


def test_permalink_is_used_as_url_fallback() -> None:
    post = {**fake_post(), "url": "", "permalink": "/r/dealsonamazon/comments/abc123/deal/"}

    deal = normalize_reddit_post(post)

    assert deal is not None
    assert deal.url == "https://www.reddit.com/r/dealsonamazon/comments/abc123/deal/"
