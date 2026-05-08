"""Mock deal source for the MVP."""

from __future__ import annotations

from ..models import Deal
from .base import DealSource


class MockDealSource(DealSource):
    """Deterministic mock source used by the MVP and tests."""

    @property
    def name(self) -> str:
        """Return the source registry name."""

        return "mock"

    def fetch_deals(self) -> list[Deal]:
        """Return deterministic mock deals for local MVP runs."""

        return _build_mock_deals()


def fetch_mock_deals() -> list[Deal]:
    """Return deterministic mock deals for local MVP runs.

    This compatibility wrapper keeps existing callers working while the
    application migrates to source adapter instances.
    """

    return MockDealSource().fetch_deals()


def _build_mock_deals() -> list[Deal]:
    return [
        Deal(
            deal_id="mock-oled-monitor-001",
            title='49" OLED Gaming Monitor - Possible Price Mistake',
            category="Computer peripherals",
            current_price=299.99,
            average_price_90d=1199.99,
            lowest_price_90d=899.99,
            url="https://example.com/mock/oled-monitor",
            source="mock",
            keywords=["OLED monitor", "gaming monitor", "monitor"],
            signals=["price mistake", "promo code"],
        ),
        Deal(
            deal_id="mock-nvme-ssd-002",
            title="4TB NVMe SSD with Coupon Stack",
            category="Computer components",
            current_price=89.99,
            average_price_90d=329.99,
            lowest_price_90d=219.99,
            url="https://example.com/mock/nvme-ssd",
            source="mock",
            keywords=["SSD", "NVMe"],
            signals=["coupon stack"],
        ),
        Deal(
            deal_id="mock-ddr5-ram-003",
            title="64GB DDR5 RAM Kit Weekend Promo",
            category="Computer components",
            current_price=119.99,
            average_price_90d=239.99,
            lowest_price_90d=149.99,
            url="https://example.com/mock/ddr5-ram",
            source="mock",
            keywords=["RAM", "DDR5"],
            signals=["promo code"],
        ),
        Deal(
            deal_id="mock-keyboard-004",
            title="Mechanical Keyboard Lightning Deal",
            category="Computer peripherals",
            current_price=59.99,
            average_price_90d=129.99,
            lowest_price_90d=69.99,
            url="https://example.com/mock/mechanical-keyboard",
            source="mock",
            keywords=["keyboard", "mechanical keyboard"],
            signals=[],
        ),
        Deal(
            deal_id="mock-robot-vacuum-005",
            title="Robot Vacuum Glitch Discount",
            category="Appliances",
            current_price=99.99,
            average_price_90d=499.99,
            lowest_price_90d=249.99,
            url="https://example.com/mock/robot-vacuum",
            source="mock",
            keywords=["robot vacuum"],
            signals=["glitch"],
        ),
        Deal(
            deal_id="mock-wireless-mouse-006",
            title="Wireless Mouse Standard Sale",
            category="Computer peripherals",
            current_price=34.99,
            average_price_90d=49.99,
            lowest_price_90d=29.99,
            url="https://example.com/mock/wireless-mouse",
            source="mock",
            keywords=["mouse", "wireless mouse"],
            signals=[],
        ),
    ]
