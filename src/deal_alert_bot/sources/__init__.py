"""Deal source adapters.

Sources expose deal candidates for human review only. They must not add Amazon
account automation, checkout automation, CAPTCHA bypass, coupon clicking, or
high-volume crawling behavior.
"""

from .base import DealSource
from .mock import MockDealSource, fetch_mock_deals
from .registry import available_source_names, get_enabled_sources, get_source
from .slickdeals import SlickdealsRssSource

__all__ = [
    "DealSource",
    "MockDealSource",
    "SlickdealsRssSource",
    "available_source_names",
    "fetch_mock_deals",
    "get_enabled_sources",
    "get_source",
]
