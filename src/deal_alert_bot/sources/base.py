"""Base interfaces for safe deal source adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Deal


class DealSource(ABC):
    """Common interface for non-automated deal source adapters.

    Source adapters only return deal candidates for human review. They must not
    purchase products, automate Amazon login, test carts, click coupons, bypass
    CAPTCHA, or perform high-volume crawling.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the stable configuration name for this source."""

    @abstractmethod
    def fetch_deals(self) -> list[Deal]:
        """Fetch deal candidates and normalize them into Deal models."""
