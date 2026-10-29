"""The scrollable chat view (renders conversation as HTML bubbles)."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any, List, Tuple

from PySide6.QtWidgets import QTextBrowser

from .markdown import render_markdown

_STYLESHEET = """
body { font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif; font-size: 14px; color: #e2e8f0; }
.msg { display: flex; margin: 12px 0; animation: fadeIn 0.25s ease-out; }
.msg-user { flex-direction: row-reverse; }
.msg-assistant { flex-direction: row; }
.avatar { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; margin: 0 10px; flex-shrink: 0; }
.msg-user .avatar { background: #22d3ee; color: #0b1021; }
.msg-assistant .avatar { background: #818cf8; color: #0b1021; }
.bubble { padding: 12px 16px; border-radius: 18px; max-width: 72%; line-height: 1.6; white-space: pre-wrap; }
.msg-user .bubble { border-bottom-right-radius: 4px; background: #1e40af; color: #ffffff; }
.msg-assistant .bubble { border-bottom-left-radius: 4px; background: #312e81; color: #e2e8f0; }
.who { font-size: 11px; font-weight: 800; opacity: 0.8; margin-bottom: 6px; display: block; letter-spacing: 0.05em; }
.msg-user .who { color: #93c5fd; }
.msg-assistant .who { color: #c7d2fe; }
.time { font-size: 10px; opacity: 0.5; margin-top: 8px; display: block; }
.msg-system { justify-content: center; color: #64748b; font-size: 12px; font-style: italic; padding: 10px; text-align: center; }
.msg-sources { background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px; margin: 14px 0; }
.msg-sources .who { color: #22d3ee; font-weight: 800; display: block; margin-bottom: 10px; letter-spacing: 0.05em; }
.msg-sources a { color: #67e8f9; text-decoration: underline; }
.msg-sources ol { margin: 0; padding-left: 20px; }
pre { background: #0f172a; padding: 14px; border-radius: 10px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; overflow-x: auto; border: 1px solid #334155; margin: 8px 0; }
code { background: #1e293b; padding: 2px 6px; border-radius: 5px; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; color: #22d3ee; }
a { color: #38bdf8; text-decoration: none; }
ul, ol { margin: 6px 0; padding-left: 22px; }
h1, h2, h3 { color: #22d3ee; margin: 10px 0 6px 0; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
"""


class ChatView(QTextBrowser):
    """Maintains a list of messages and re-renders them as styled HTML bubbles."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.setFrameShape(QTextBrowser.NoFrame)
        self.document().setDefaultStyleSheet(_STYLESHEET)
        self._messages: List[Tuple[str, Any, str | None]] = []

    # -- public API --------------------------------------------------------

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().strftime("%H:%M")

    def add_user(self, text: str) -> None:
        self._messages.append(("user", text, self._timestamp()))
        self._render()

    def add_assistant(self, text: str) -> None:
        self._messages.append(("assistant", text, self._timestamp()))
        self._render()

    def begin_assistant(self) -> None:
        """Start a streaming assistant message."""
        self._messages.append(("assistant", "", self._timestamp()))
        self._render()

    def append_assistant(self, chunk: str) -> None:
        """Append a chunk to the in-progress assistant message."""
        if self._messages and self._messages[-1][0] == "assistant":
            kind, text, stamp = self._messages[-1]
            self._messages[-1] = (kind, text + chunk, stamp)
            self._render()

    def add_system(self, text: str) -> None:
        """Append a muted status/error line."""
        self._messages.append(("system", text, None))
        self._render()

    def add_sources(self, sources: List[Any]) -> None:
        """Append a numbered, clickable source list."""
        self._messages.append(("sources", sources, None))
        self._render()

    def clear_chat(self) -> None:
        self._messages.clear()
        self._render()

    # -- rendering ---------------------------------------------------------

    def _render(self) -> None:
        blocks = "".join(self._block(k, p, s) for k, p, s in self._messages)
        self.setHtml(blocks)
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _block(self, kind: str, payload: Any, stamp: str | None) -> str:
        time_html = f'<span class="time">{stamp}</span>' if stamp else ""
        if kind == "user":
            return (
                '<div class="msg msg-user">'
                '<div class="avatar">U</div>'
                '<div class="bubble">'
                f"{render_markdown(payload)}{time_html}"
                '</div></div>'
            )
        if kind == "assistant":
            return (
                '<div class="msg msg-assistant">'
                '<div class="avatar">T</div>'
                '<div class="bubble">'
                f"{render_markdown(payload)}{time_html}"
                '</div></div>'
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
