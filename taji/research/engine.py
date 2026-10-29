"""Deep research engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .. import config
from ..llm.client import OllamaClient
from ..llm.prompts import RESEARCH_ANSWER_PROMPT
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
        progress = progress or (lambda _msg: None)

        # Do not use LLM to generate queries (causes 3B models to hallucinate random text)
        queries = [question]
        
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

    def _gather_sources(
        self, queries: List[str], progress: ProgressFn
    ) -> List[Source]:
        seen_urls = set()
        sources: List[Source] = []

        for query in queries:
            progress(f"Searching the web for: {query}")
            try:
                results = search(query)
                if not results:
                    progress(f"No results found for '{query}'")
            except Exception as exc:
                progress(f"Search failed: {exc}")
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

    def _synthesize(self, question: str, sources: List[Source]) -> str:
        context = self._build_context(sources)
        
        if not context.strip():
            return "I couldn't find any web sources to answer this question. Please try rephrasing your query."

        resp = self.client.chat(
            [{"role": "user", "content": RESEARCH_ANSWER_PROMPT.format(
                question=question, sources=context
            )}],
            system="You are a factual research assistant. Answer ONLY using the provided sources. Cite them as [1], [2]. If the answer is not in the sources, say 'I couldn't find that in the sources.'",
            temperature=0.1,
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