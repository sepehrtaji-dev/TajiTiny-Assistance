"""Chat message bubbles built from real widgets — no HTML/CSS quirks."""

from __future__ import annotations

from datetime import datetime
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget,
)

from .markdown import render_markdown


class MessageBubble(QFrame):
    """A single chat bubble (user or assistant)."""

    def __init__(self, role: str, text: str, stamp: str, parent=None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        avatar = QLabel("U" if role == "user" else "T")
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setFixedSize(34, 34)
        avatar.setStyleSheet(
            f"background-color: {'#22d3ee' if role == 'user' else '#818cf8'};"
            f"color: #0b1021; font-weight: 900; font-size: 13px; border-radius: 17px;"
        )

        body = QVBoxLayout()
        body.setSpacing(2)

        who = QLabel("You" if role == "user" else "Taji 1.1")
        who.setStyleSheet(
            f"color: {'#93c5fd' if role == 'user' else '#c7d2fe'}; font-size: 11px;"
            f"font-weight: 800; letter-spacing: 0.05em;"
        )

        msg = QLabel(render_markdown(text))
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        msg.setStyleSheet(
            f"color: {('#ffffff' if role == 'user' else '#e2e8f0')}; font-size: 14px;"
            f"background-color: {('#1e40af' if role == 'user' else '#312e81')};"
            f"padding: 12px 16px; border-radius: 18px;"
        )
        if role == "user":
            msg.setStyleSheet(msg.styleSheet() + "border-bottom-right-radius: 4px;")
        else:
            msg.setStyleSheet(msg.styleSheet() + "border-bottom-left-radius: 4px;")

        time = QLabel(stamp)
        time.setStyleSheet("color: #64748b; font-size: 10px;")

        body.addWidget(who)
        body.addWidget(msg)
        body.addWidget(time)
        body.addStretch()

        if role == "user":
            layout.addStretch()
            layout.addLayout(body, stretch=1)
            layout.addWidget(avatar)
        else:
            layout.addWidget(avatar)
            layout.addLayout(body, stretch=1)
            layout.addStretch()

        msg.setMaximumWidth(860)


class ChatView(QListWidget):
    """Scrollable list of message bubbles."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ChatView")
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSpacing(4)

    def _add(self, role: str, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M")
        bubble = MessageBubble(role, text, stamp)
        item = QListWidgetItem(self)
        item.setSizeHint(bubble.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, bubble)
        self.scrollToBottom()

    def add_user(self, text: str) -> None:
        self._add("user", text)

    def add_assistant(self, text: str) -> None:
        self._add("assistant", text)

    def begin_assistant(self) -> None:
        """Create an empty assistant bubble ready for streaming."""
        stamp = datetime.now().strftime("%H:%M")
        bubble = MessageBubble("assistant", "", stamp)
        item = QListWidgetItem(self)
        item.setSizeHint(bubble.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, bubble)
        self._stream_item = item
        self.scrollToBottom()

    def append_assistant(self, chunk: str) -> None:
        """Append text to the last assistant bubble."""
        if not hasattr(self, "_stream_item"):
            return
            
        widget = self.itemWidget(self._stream_item)
        if widget is None:
            return
            
        # FIX: Access the nested layout properly instead of trying to get a widget
        layout = widget.layout()
        if layout is None:
            return
            
        body_item = layout.itemAt(1)
        if body_item is None or body_item.layout() is None:
            return
            
        body_layout = body_item.layout()
        msg_item = body_layout.itemAt(1)
        if msg_item is None or msg_item.widget() is None:
            return
            
        msg_label = msg_item.widget()
        
        # Accumulate text and re-render markdown
        self._raw_assistant_text = getattr(self, "_raw_assistant_text", "") + chunk
        msg_label.setText(render_markdown(self._raw_assistant_text))
        
        # Force layout update
        widget.adjustSize()
        self._stream_item.setSizeHint(widget.sizeHint())
        self.scrollToBottom()

    def finish_assistant(self) -> None:
        if hasattr(self, "_stream_item"):
            del self._stream_item
        self._raw_assistant_text = ""

    def add_system(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M")
        label = QLabel(text)
        label.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic; padding: 8px;")
        label.setAlignment(Qt.AlignCenter)
        item = QListWidgetItem(self)
        item.setSizeHint(label.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, label)
        self.scrollToBottom()

    def add_sources(self, sources: List[object]) -> None:
        from .research import SourcesPanel
        panel = SourcesPanel()
        panel.set_sources(sources)
        item = QListWidgetItem(self)
        item.setSizeHint(panel.sizeHint())
        self.addItem(item)
        self.setItemWidget(item, panel)
        self.scrollToBottom()

    def clear_chat(self) -> None:
        self.clear()
        if hasattr(self, "_stream_item"):
            del self._stream_item
        self._raw_assistant_text = ""