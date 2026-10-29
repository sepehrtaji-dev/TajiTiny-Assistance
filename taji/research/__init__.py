"""Deep-research layer: web search, page fetching, and synthesis."""

from .engine import ResearchEngine, ResearchResult, Source
from .fetch import FetchedPage, fetch_page
from .search import SearchError, SearchResult, search

__all__ = [
    "ResearchEngine",
    "ResearchResult",
    "Source",
    "FetchedPage",
    "fetch_page",
    "SearchError",
    "SearchResult",
    "search",
]