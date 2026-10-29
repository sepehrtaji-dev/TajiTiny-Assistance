"""A tiny, safe Markdown-to-HTML renderer for the chat view.

It supports the subset the model actually emits — bold, italic, inline code,
fenced code blocks, headings, lists, and markdown links — and always HTML-escapes
plain text so web content can never inject markup into the UI.
"""

from __future__ import annotations

import html
import re

_CODE = re.compile(r"`([^`]+)`")
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def _inline(text: str) -> str:
    """Render inline spans, escaping everything else."""
    tokens: list[str] = []

    def stash(rendered: str) -> str:
        idx = len(tokens)
        tokens.append(rendered)
        return f"\x00{idx}\x00"

    text = _CODE.sub(
        lambda m: stash(f"<code>{html.escape(m.group(1))}</code>"), text
    )
    text = _LINK.sub(
        lambda m: stash(
            f'<a href="{html.escape(m.group(2), quote=True)}">'
            f"{html.escape(m.group(1))}</a>"
        ),
        text,
    )
    text = _BOLD.sub(
        lambda m: stash(f"<b>{html.escape(m.group(1))}</b>"), text
    )
    text = _ITALIC.sub(
        lambda m: stash(f"<i>{html.escape(m.group(1))}</i>"), text
    )

    text = html.escape(text)
    for idx, rendered in enumerate(tokens):
        text = text.replace(f"\x00{idx}\x00", rendered)
    return text


def render_markdown(text: str) -> str:
    """Convert a block of Markdown text into HTML."""
    lines = text.split("\n")
    out: list[str] = []
    in_code = False
    list_tag: str | None = None
    list_items: list[str] = []

    def flush_list() -> None:
        nonlocal list_tag, list_items
        if list_tag:
            items = "".join(f"<li>{i}</li>" for i in list_items)
            out.append(f"<{list_tag}>{items}</{list_tag}>")
            list_tag = None
            list_items = []

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                flush_list()
                out.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            out.append(html.escape(line))
            continue

        if not stripped:
            flush_list()
            continue

        header = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header:
            flush_list()
            level = len(header.group(1))
            out.append(f"<h{level}>{_inline(header.group(2))}</h{level}>")
            continue

        ul = re.match(r"^[-*+]\s+(.*)$", stripped)
        ol = re.match(r"^\d+[.)]\s+(.*)$", stripped)
        if ul or ol:
            tag = "ul" if ul else "ol"
            body = (ul or ol).group(1)
            if list_tag != tag:
                flush_list()
                list_tag = tag
            list_items.append(_inline(body))
            continue

        flush_list()
        out.append(f"<p>{_inline(stripped)}</p>")

    if in_code:
        out.append("</code></pre>")
    flush_list()

    return "\n".join(out)
