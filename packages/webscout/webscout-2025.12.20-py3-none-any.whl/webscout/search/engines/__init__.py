"""Static imports for all search engine modules."""

from __future__ import annotations

from .brave import Brave
from .mojeek import Mojeek
from .wikipedia import Wikipedia
from .yandex import Yandex
from .bing import BingBase, BingTextSearch, BingImagesSearch, BingNewsSearch, BingSuggestionsSearch
from .duckduckgo import (
    DuckDuckGoBase,
    DuckDuckGoTextSearch,
    DuckDuckGoImages,
    DuckDuckGoVideos,
    DuckDuckGoNews,
    DuckDuckGoAnswers,
    DuckDuckGoSuggestions,
    DuckDuckGoMaps,
    DuckDuckGoTranslate,
    DuckDuckGoWeather,
)
from .yep import YepBase, YepTextSearch, YepImages, YepSuggestions
from .yahoo import (
    YahooSearchEngine,
    YahooText,
    YahooImages,
    YahooVideos,
    YahooNews,
    YahooSuggestions,
)
from ..base import BaseSearchEngine

# Engine categories mapping
ENGINES = {
    "text": {
        "brave": Brave,
        "mojeek": Mojeek,
        "yandex": Yandex,
        "bing": BingTextSearch,
        "duckduckgo": DuckDuckGoTextSearch,
        "yep": YepTextSearch,
        "yahoo": YahooText,
    },
    "images": {
        "bing": BingImagesSearch,
        "duckduckgo": DuckDuckGoImages,
        "yep": YepImages,
        "yahoo": YahooImages,
    },
    "videos": {
        "duckduckgo": DuckDuckGoVideos,
        "yahoo": YahooVideos,
    },
    "news": {
        "bing": BingNewsSearch,
        "duckduckgo": DuckDuckGoNews,
        "yahoo": YahooNews,
    },
    "suggestions": {
        "bing": BingSuggestionsSearch,
        "duckduckgo": DuckDuckGoSuggestions,
        "yep": YepSuggestions,
        "yahoo": YahooSuggestions,
    },
    "answers": {
        "duckduckgo": DuckDuckGoAnswers,
    },
    "maps": {
        "duckduckgo": DuckDuckGoMaps,
    },
    "translate": {
        "duckduckgo": DuckDuckGoTranslate,
    },
    "weather": {
        "duckduckgo": DuckDuckGoWeather,
    },
}

__all__ = [
    "Brave",
    "Mojeek",
    "Wikipedia",
    "Yandex",
    "BingBase",
    "BingTextSearch",
    "BingImagesSearch",
    "BingNewsSearch",
    "BingSuggestionsSearch",
    "DuckDuckGoBase",
    "DuckDuckGoTextSearch",
    "DuckDuckGoImages",
    "DuckDuckGoVideos",
    "DuckDuckGoNews",
    "DuckDuckGoAnswers",
    "DuckDuckGoSuggestions",
    "DuckDuckGoMaps",
    "DuckDuckGoTranslate",
    "DuckDuckGoWeather",
    "YepBase",
    "YepTextSearch",
    "YepImages",
    "YepSuggestions",
    "YahooSearchEngine",
    "YahooText",
    "YahooImages",
    "YahooVideos",
    "YahooNews",
    "YahooSuggestions",
    "BaseSearchEngine",
    "ENGINES",
]
