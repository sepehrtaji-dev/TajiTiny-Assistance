"""Fetch a web page and extract readable text for research context."""

from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

from .. import config


@dataclass
class FetchedPage:
    url: str
    title: str = ""
    text: str = ""
    error: str = ""

    @property
    def ok(self) -> bool:
        return not self.error and bool(self.text)


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

_BOILERPLATE_TAGS = [
    "script", "style", "noscript", "svg", "iframe",
    "header", "footer", "nav", "aside", "form", "button",
]


def fetch_page(url: str, max_chars: int | None = None) -> FetchedPage:
    """Fetch a URL and return its title plus extracted text (truncated)."""
    max_chars = max_chars or config.MAX_SOURCE_CHARS

    try:
        resp = requests.get(
            url,
            headers=_HEADERS,
            timeout=config.FETCH_TIMEOUT,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        return FetchedPage(url=url, error=f"request failed: {exc}")

    if resp.status_code >= 400:
        return FetchedPage(url=url, error=f"HTTP {resp.status_code}")

    content_type = (resp.headers.get("Content-Type") or "").lower()
    if "html" not in content_type and "text" not in content_type:
        return FetchedPage(url=url, error=f"non-text content ({content_type})")

    return FetchedPage(
        url=resp.url,
        title=extract_title(resp.text),
        text=extract_text(resp.text)[:max_chars],
    )


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else ""


def extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(_BOILERPLATE_TAGS):
        tag.decompose()

    container = soup.find("article") or soup.find("main") or soup.body or soup
    text = container.get_text("\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()