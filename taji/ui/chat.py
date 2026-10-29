"""The scrollable chat view (renders conversation as HTML)."""

from __future__ import annotations

import html
from typing import Any, List, Tuple

from PySide6.QtWidgets import QTextBrowser

from .markdown import render_markdown

_STYLESHEET = """
body { font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; font-size: 14px; color: #1f2430; }
.msg { margin-bottom: 14px; }
.msg-user .who { color: #2563eb; font-weight: 600; }
.msg-assistant .who { color: #7c3aed; font-weight: 600; }
.msg-system { color: #6b7280; font-size: 12px; font-style: italic; }
.msg-sources .who { color: #059669; font-weight: 600; }
a { color: #2563eb; text-decoration: none; }
p { margin: 4px 0; }
pre { background-color: #f3f4f6; padding: 8px; border-radius: 6px; font-family: 'Consolas', monospace; font-size: 13px; }
code { background-color: #f3f4f6; padding: 1px 4px; border-radius: 3px; font-family: 'Consolas', monospace; font-size: 13px; }
h1, h2, h3, h4 { margin: 8px 0 4px 0; }
ul, ol { margin: 4px 0; }
"""


class ChatView(QTextBrowser):
    """Maintains a list of messages and re-renders them as styled HTML."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.setFrameShape(QTextBrowser.NoFrame)
        self.document().setDefaultStyleSheet(_STYLESHEET)
        self._messages: List[Tuple[str, Any]] = []

    # -- public API --------------------------------------------------------

    def add_user(self, text: str) -> None:
        self._messages.append(("user", text))
        self._render()

    def add_assistant(self, text: str) -> None:
        self._messages.append(("assistant", text))
        self._render()

    def begin_assistant(self) -> None:
        """Start a streaming assistant message."""
        self._messages.append(("assistant", ""))
        self._render()

    def append_assistant(self, chunk: str) -> None:
        """Append a chunk to the in-progress assistant message."""
        if self._messages and self._messages[-1][0] == "assistant":
            kind, text = self._messages[-1]
            self._messages[-1] = (kind, text + chunk)
            self._render()

    def add_system(self, text: str) -> None:
        """Append a muted status/error line."""
        self._messages.append(("system", text))
        self._render()

    def add_sources(self, sources: List[Any]) -> None:
        """Append a numbered, clickable source list."""
        self._messages.append(("sources", sources))
        self._render()

    def clear_chat(self) -> None:
        self._messages.clear()
        self._render()

    # -- rendering ---------------------------------------------------------

    def _render(self) -> None:
        blocks = "".join(
            self._block(kind, payload) for kind, payload in self._messages
        )
        self.setHtml(blocks)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _block(self, kind: str, payload: Any) -> str:
        if kind == "user":
            return (
                '<div class="msg msg-user"><span class="who">You</span><br>'
                f"{render_markdown(payload)}</div>"
            )
        if kind == "assistant":
            return (
                '<div class="msg msg-assistant">'
                '<span class="who">Taji 1.1</span><br>'
                f"{render_markdown(payload)}</div>"
            )
        if kind == "system":
            return f'<div class="msg msg-system">{html.escape(payload)}</div>'
        if kind == "sources":
            return self._render_sources(payload)
        return ""

    @staticmethod
    def _render_sources(sources: List[Any]) -> str:
        if not sources:
            return (
                '<div class="msg msg-sources"><span class="who">Sources</span>'
                "<br><i>No sources found.</i></div>"
            )
        items = "".join(
            f'<li>[{s.index}] '
            f'<a href="{html.escape(s.url, quote=True)}">'
            f"{html.escape(s.title)}</a></li>"
            for s in sources
        )
        return (
            '<div class="msg msg-sources"><span class="who">Sources</span>'
            f"<br><ol>{items}</ol></div>"
        )
