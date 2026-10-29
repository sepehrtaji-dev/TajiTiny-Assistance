"""Side panel listing the sources gathered by the last research run."""

from __future__ import annotations

from typing import Any, List

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class SourcesPanel(QWidget):
    """A titled list of clickable sources (opens in the default browser)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("Sources")
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        self._list = QListWidget()
        self._list.itemClicked.connect(self._open)
        layout.addWidget(self._list)

        self._urls: dict = {}

    def set_sources(self, sources: List[Any]) -> None:
        self._list.clear()
        self._urls.clear()
        for source in sources:
            item = QListWidgetItem(f"[{source.index}] {source.title}")
            item.setToolTip(source.url)
            self._list.addItem(item)
            self._urls[id(item)] = source.url

    def clear(self) -> None:
        self._list.clear()
        self._urls.clear()

    def _open(self, item: QListWidgetItem) -> None:
        url = self._urls.get(id(item))
        if url:
            QDesktopServices.openUrl(QUrl(url))
