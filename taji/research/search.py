"""Web search via the DuckDuckGo Lite endpoint (no API key required).

DuckDuckGo Lite returns a small, stable HTML page that is far less likely to
trigger bot protection than the full results page, and it works without any
credentials — important for a private, local tool.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

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


DDG_LITE_URL = "https://lite.duckduckgo.com/lite/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_SESSION = requests.Session()


def search(query: str, max_results: Optional[int] = None) -> List[SearchResult]:
    """Run a web search and return a list of title/url/snippet results."""
    max_results = max_results or config.SEARCH_MAX_RESULTS

    try:
        resp = _SESSION.post(
            DDG_LITE_URL,
            data={"q": query},
            headers=_HEADERS,
            timeout=config.FETCH_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise SearchError(f"search request failed: {exc}") from exc

    if resp.status_code != 200:
        raise SearchError(f"search returned HTTP {resp.status_code}")

    return _parse(resp.text, max_results)


def _parse(html: str, max_results: int) -> List[SearchResult]:
    soup = BeautifulSoup(html, "lxml")
    results: List[SearchResult] = []

    for link in soup.select("a.result-link"):
        title = link.get_text(strip=True)
        url = link.get("href")
        if not title or not url:
            continue

        snippet_el = link.find_next("td", class_="result-snippet")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        results.append(SearchResult(title=title, url=url, snippet=snippet))
        if len(results) >= max_results:
            break

    return results
