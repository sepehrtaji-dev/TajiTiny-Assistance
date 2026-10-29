"""Deep research engine.

Orchestrates a multi-step "deep research" pass over a question:

1. Expand the question into focused sub-queries (with a fallback to the raw question).
2. Search each query and collect deduplicated sources.
3. Fetch and extract the full text of the top sources.
4. Synthesize a grounded, cited answer using only that source material.

Progress is reported through an optional callback so the UI can stream status.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .. import config
from ..llm.client import OllamaClient
from ..llm.prompts import RESEARCH_ANSWER_PROMPT, SUBQUERY_PROMPT
from .fetch import fetch_page
from .search import search

ProgressFn = Callable[[str], None]


@dataclass
class Source:
    index: int
    title: str
    url: str
    snippet: str = ""
    text: str = ""


@dataclass
class ResearchResult:
    question: str
    answer: str
    sources: List[Source] = field(default_factory=list)
    queries: List[str] = field(default_factory=list)


class ResearchEngine:
    """Coordinates search, fetching, and synthesis for a research question."""

    def __init__(self, client: Optional[OllamaClient] = None) -> None:
        self.client = client or OllamaClient()

    def research(
        self,
        question: str,
        depth: Optional[int] = None,
        progress: Optional[ProgressFn] = None,
    ) -> ResearchResult:
        depth = depth or config.RESEARCH_DEPTH
        progress = progress or (lambda _msg: None)

        queries = self._build_queries(question, depth)
        sources = self._gather_sources(queries, progress)
        self._enrich_sources(sources, progress)

        progress("Synthesizing answer from sources...")
        answer = self._synthesize(question, sources)

        return ResearchResult(
            question=question,
            answer=answer,
            sources=sources,
            queries=queries,
        )

    # -- query expansion ---------------------------------------------------

    def _build_queries(self, question: str, depth: int) -> List[str]:
        queries = [question]
        if depth >= 2:
            sub = self._subqueries(question)
            queries.extend(sub[:3])
        return queries

    def _subqueries(self, question: str) -> List[str]:
        """Ask the model for focused sub-queries; fall back to [] on any failure."""
        try:
            resp = self.client.chat(
                [{"role": "user", "content": SUBQUERY_PROMPT.format(question=question)}],
                temperature=0.2,
            )
            content = (resp.get("message") or {}).get("content") or ""
        except Exception:  # noqa: BLE001 - expansion is best-effort
            return []

        cleaned = []
        for line in content.splitlines():
            line = line.strip().lstrip(" -•*#0123456789.)").strip()
            if len(line) > 3:
                cleaned.append(line)
        return cleaned[:4]

    # -- gathering ---------------------------------------------------------

    def _gather_sources(
        self, queries: List[str], progress: ProgressFn
    ) -> List[Source]:
        seen_urls = set()
        sources: List[Source] = []

        for query in queries:
            progress(f"Searching: {query}")
            try:
                results = search(query)
            except Exception as exc:  # noqa: BLE001 - keep going on partial failure
                progress(f"Search skipped ({exc})")
                continue

            for result in results:
                if result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                sources.append(
                    Source(
                        index=len(sources) + 1,
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                    )
                )
                progress(f"Found source: {result.title}")
                if len(sources) >= config.MAX_SOURCES:
                    break

            if len(sources) >= config.MAX_SOURCES:
                break

        return sources

    def _enrich_sources(
        self, sources: List[Source], progress: ProgressFn
    ) -> None:
        for source in sources:
            progress(f"Reading: {source.title}")
            page = fetch_page(source.url)
            if page.ok:
                source.text = page.text
                source.title = page.title or source.title
            else:
                progress(f"Could not read {source.title} ({page.error})")

    # -- synthesis ---------------------------------------------------------

    def _synthesize(self, question: str, sources: List[Source]) -> str:
        context = self._build_context(sources)
        
        # If no sources were found, fail gracefully instead of asking the model
        if not context.strip():
            return "I couldn't find any web sources to answer this question."

        resp = self.client.chat(
            [{"role": "user", "content": RESEARCH_ANSWER_PROMPT.format(
                question=question, sources=context
            )}],
            # Explicitly use a strict system prompt for research
            system="You are a factual research assistant. Answer ONLY using the provided sources. Cite them as [1], [2]. If the answer is not in the sources, say you don't know.",
            temperature=0.2, # Keep research very grounded
        )
        return (resp.get("message") or {}).get("content") or ""

    def _build_context(self, sources: List[Source]) -> str:
        parts = []
        for source in sources:
            body = source.text or source.snippet
            if not body:
                continue
            parts.append(
                f"[{source.index}] {source.title}\n{source.url}\n{body}"
            )
        return "\n\n".join(parts)
