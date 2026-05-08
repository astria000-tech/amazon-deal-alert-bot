"""Keepa source adapter skeleton with fake-client normalization support."""

from __future__ import annotations

from typing import Any, Protocol

from ..models import Deal
from .base import DealSource


class KeepaClient(Protocol):
    """Minimal protocol for future Keepa clients and test fakes.

    The production Keepa network client is intentionally not implemented yet.
    Tests inject fake clients that return deterministic product dictionaries.
    """

    def fetch_products(self) -> list[dict[str, Any]]:
        """Return product dictionaries to normalize into Deal models."""


class KeepaDealSource(DealSource):
    """Safe Keepa source skeleton for future API integration.

    This adapter does not perform real Keepa or Amazon network calls. A caller
    may inject a fake client for tests; otherwise ``fetch_deals`` fails clearly
    until a real, rate-limited Keepa client is implemented in a future phase.
    """

    def __init__(self, api_key: str | None = None, client: KeepaClient | None = None):
        self._api_key = api_key
        self._client = client

    @property
    def name(self) -> str:
        """Return the source registry name."""

        return "keepa"

    def fetch_deals(self) -> list[Deal]:
        """Fetch fake-client products and normalize them into Deal models.

        Raises:
            RuntimeError: If no API key is configured or no client is injected.
                Error messages intentionally avoid printing secret values.
        """

        if not self._api_key:
            raise RuntimeError(
                "Keepa source is enabled but KEEPA_API_KEY is not configured. "
                "Set it via .env or secrets before enabling this source."
            )

        if self._client is None:
            raise RuntimeError(
                "Keepa source is a skeleton only; no network client is implemented yet. "
                "Inject a fake client in tests or add a safe client in a future phase."
            )

        deals: list[Deal] = []
        for product in self._client.fetch_products():
            deal = normalize_keepa_product(product)
            if deal is not None:
                deals.append(deal)
        return deals


def normalize_keepa_product(product: dict[str, Any]) -> Deal | None:
    """Normalize a fake Keepa product dictionary into a ``Deal``.

    The exact production Keepa response is not wired yet. This function accepts
    fake-client dictionaries with cent-based price fields and skips incomplete
    records safely. Supported price keys are:

    - ``current_price_cents`` or ``current_price``
    - ``average_price_90d_cents`` or ``average_price_90d``
    - ``lowest_price_90d_cents`` or ``lowest_price_90d``

    Non-``*_cents`` values are treated as dollar values.
    """

    title = _clean_string(product.get("title"))
    if title is None:
        return None

    current_price = _read_price(product, "current_price")
    average_price_90d = _read_price(product, "average_price_90d")
    lowest_price_90d = _read_price(product, "lowest_price_90d")
    if current_price is None or average_price_90d is None or lowest_price_90d is None:
        return None

    deal_identifier = _clean_string(product.get("asin")) or _clean_string(product.get("id"))
    if deal_identifier is None:
        return None

    category = _clean_string(product.get("category")) or "Uncategorized"
    url = _clean_string(product.get("url")) or _build_amazon_product_url(deal_identifier)

    return Deal(
        deal_id=f"keepa-{deal_identifier}",
        title=title,
        category=category,
        current_price=current_price,
        average_price_90d=average_price_90d,
        lowest_price_90d=lowest_price_90d,
        url=url,
        source="keepa",
        keywords=_read_string_list(product.get("keywords")),
        signals=_read_string_list(product.get("signals")),
    )


def _read_price(product: dict[str, Any], base_key: str) -> float | None:
    cents_key = f"{base_key}_cents"
    if cents_key in product:
        return _coerce_positive_price(product.get(cents_key), cents=True)
    return _coerce_positive_price(product.get(base_key), cents=False)


def _coerce_positive_price(value: Any, *, cents: bool) -> float | None:
    if value is None:
        return None
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    if price <= 0:
        return None
    if cents:
        price = price / 100
    return round(price, 2)


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _read_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = _clean_string(value)
        return [cleaned] if cleaned is not None else []
    if not isinstance(value, list | tuple | set):
        return []

    strings: list[str] = []
    for item in value:
        cleaned = _clean_string(item)
        if cleaned is not None:
            strings.append(cleaned)
    return strings


def _build_amazon_product_url(deal_identifier: str) -> str:
    return f"https://www.amazon.com/dp/{deal_identifier}"
