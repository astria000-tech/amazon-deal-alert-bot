"""Tests for the Keepa source skeleton and fake-client normalization."""

from __future__ import annotations

from typing import Any

import pytest

from deal_alert_bot.models import Deal
from deal_alert_bot.sources.keepa import KeepaDealSource, normalize_keepa_product


class FakeKeepaClient:
    """Deterministic fake client that never performs network calls."""

    def __init__(self, products: list[dict[str, Any]]):
        self.products = products
        self.called = False

    def fetch_products(self) -> list[dict[str, Any]]:
        self.called = True
        return self.products


def fake_keepa_product() -> dict[str, Any]:
    return {
        "asin": "B0FAKE1234",
        "title": "Fake OLED Monitor Deal",
        "category": "Computer peripherals",
        "current_price_cents": 29999,
        "average_price_90d_cents": 79999,
        "lowest_price_90d_cents": 49999,
        "url": "https://example.com/keepa/fake-oled-monitor",
        "keywords": ["OLED monitor", "gaming monitor"],
        "signals": ["price drop"],
    }


def test_keepa_deal_source_name_is_keepa() -> None:
    source = KeepaDealSource(api_key="fake-test-key", client=FakeKeepaClient([]))

    assert source.name == "keepa"


def test_fake_client_products_are_converted_to_deals() -> None:
    fake_client = FakeKeepaClient([fake_keepa_product()])
    source = KeepaDealSource(api_key="fake-test-key", client=fake_client)

    deals = source.fetch_deals()

    assert fake_client.called is True
    assert len(deals) == 1
    assert isinstance(deals[0], Deal)
    assert deals[0].deal_id == "keepa-B0FAKE1234"
    assert deals[0].source == "keepa"


@pytest.mark.parametrize(
    "product",
    [
        {**fake_keepa_product(), "title": ""},
        {**fake_keepa_product(), "title": None},
        {**fake_keepa_product(), "current_price_cents": None},
        {**fake_keepa_product(), "average_price_90d_cents": 0},
        {**fake_keepa_product(), "lowest_price_90d_cents": "not-a-price"},
    ],
)
def test_products_without_required_title_or_prices_are_skipped(
    product: dict[str, Any],
) -> None:
    fake_client = FakeKeepaClient([product])
    source = KeepaDealSource(api_key="fake-test-key", client=fake_client)

    assert source.fetch_deals() == []


def test_missing_api_key_fails_without_secret_exposure() -> None:
    source = KeepaDealSource(api_key=None, client=FakeKeepaClient([fake_keepa_product()]))

    with pytest.raises(RuntimeError) as exc_info:
        source.fetch_deals()

    message = str(exc_info.value)
    assert "KEEPA_API_KEY" in message
    assert "fake-test-key" not in message


def test_keepa_source_without_client_never_performs_network_call() -> None:
    source = KeepaDealSource(api_key="fake-test-key")

    with pytest.raises(RuntimeError, match="no network client is implemented"):
        source.fetch_deals()


def test_normalize_keepa_product_populates_deal_fields() -> None:
    deal = normalize_keepa_product(fake_keepa_product())

    assert deal == Deal(
        deal_id="keepa-B0FAKE1234",
        title="Fake OLED Monitor Deal",
        category="Computer peripherals",
        current_price=299.99,
        average_price_90d=799.99,
        lowest_price_90d=499.99,
        url="https://example.com/keepa/fake-oled-monitor",
        source="keepa",
        keywords=["OLED monitor", "gaming monitor"],
        signals=["price drop"],
    )


def test_normalize_keepa_product_accepts_id_and_dollar_price_fields() -> None:
    deal = normalize_keepa_product(
        {
            "id": "fake-internal-id",
            "title": "Fake NVMe SSD",
            "category": "Computer components",
            "current_price": "89.99",
            "average_price_90d": 219.99,
            "lowest_price_90d": 129.99,
            "keywords": "NVMe",
        }
    )

    assert deal is not None
    assert deal.deal_id == "keepa-fake-internal-id"
    assert deal.current_price == 89.99
    assert deal.average_price_90d == 219.99
    assert deal.lowest_price_90d == 129.99
    assert deal.url == "https://www.amazon.com/dp/fake-internal-id"
    assert deal.source == "keepa"
    assert deal.keywords == ["NVMe"]
