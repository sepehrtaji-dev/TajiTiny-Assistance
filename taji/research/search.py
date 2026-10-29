"""Web search via the ddgs package."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Optional

from ddgs import DDGS

from .. import config


class SearchError(RuntimeError):
    """Raised when a search cannot be completed."""


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def search(query: str, max_results: Optional[int] = None) -> List[SearchResult]:
    """Run a web search and return a list of title/url/snippet results."""
    max_results = max_results or config.SEARCH_MAX_RESULTS

    try:
        with DDGS() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        raise SearchError(f"search request failed: {exc}") from exc

    results = []
    for r in raw_results:
        results.append(
            SearchResult(
                title=r.get("title", "No Title"),
                url=r.get("href", ""),
                snippet=r.get("body", "")
            )
        )
    return results