"""Deal source adapters.

The MVP only exposes mock data. Real integrations can be added later as separate
adapters without Amazon account automation, checkout automation, CAPTCHA bypass,
or high-volume crawling.
"""

from .base import DealSource
from .mock import MockDealSource, fetch_mock_deals
from .registry import available_source_names, get_enabled_sources, get_source

__all__ = [
    "DealSource",
    "MockDealSource",
    "available_source_names",
    "fetch_mock_deals",
    "get_enabled_sources",
    "get_source",
]
