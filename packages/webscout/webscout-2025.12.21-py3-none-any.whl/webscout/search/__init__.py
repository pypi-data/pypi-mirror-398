"""Webscout search module - unified search interfaces."""

from .base import BaseSearch, BaseSearchEngine
from .bing_main import BingSearch
from .duckduckgo_main import DuckDuckGoSearch

# Import new search engines
from .engines.brave import Brave
from .engines.mojeek import Mojeek
from .engines.wikipedia import Wikipedia
from .engines.yandex import Yandex

# Import result models
from .results import (
    BooksResult,
    ImagesResult,
    NewsResult,
    TextResult,
    VideosResult,
)
from .yahoo_main import YahooSearch
from .yep_main import YepSearch

__all__ = [
    # Base classes
    "BaseSearch",
    "BaseSearchEngine",

    # Main search interfaces
    "DuckDuckGoSearch",
    "YepSearch",
    "BingSearch",
    "YahooSearch",

    # Individual engines
    "Brave",
    "Mojeek",
    "Yandex",
    "Wikipedia",

    # Result models
    "TextResult",
    "ImagesResult",
    "VideosResult",
    "NewsResult",
    "BooksResult",
]
