"""Main window for Taji 1.1 (PySide6)."""

from __future__ import annotations

from PySide6.QtCore import QThread, Qt, Signal, QObject
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..llm.client import OllamaClient, OllamaError
from ..research.engine import ResearchEngine
from .chat import ChatView
from .research import SourcesPanel


class _Signals(QObject):
    finished = Signal(object)
    error = Signal(str)
    progress = Signal(str)


class _ChatTask(QObject):
    def __init__(self, client: OllamaClient, text: str) -> None:
        super().__init__()
        self.client = client
        self.text = text
        self.signals = _Signals()

    def run(self) -> None:
        try:
            resp = self.client.chat([{"role": "user", "content": self.text}])
            content = (resp.get("message") or {}).get("content") or ""
            self.signals.finished.emit(content)
        except OllamaError as exc:
            self.signals.error.emit(str(exc))
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))


class _ResearchTask(QObject):
    def __init__(self, engine: ResearchEngine, question: str) -> None:
        super().__init__()
        self.engine = engine
        self.question = question
        self.signals = _Signals()

    def run(self) -> None:
        def progress(msg: str) -> None:
            self.signals.progress.emit(msg)

        try:
            result = self.engine.research(self.question, progress=progress)
            self.signals.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.signals.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(config.WINDOW_TITLE)
        self.resize(*config.WINDOW_SIZE)

        self.client = OllamaClient()
        self.engine = ResearchEngine(self.client)

        self._build_ui()
        self._check_ollama()

    # -- UI -----------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        splitter = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.chat = ChatView()
        left_layout.addWidget(self.chat)

        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Taji...")
        self.input.returnPressed.connect(self._send)

        self.btn_chat = QPushButton("Chat")
        self.btn_chat.clicked.connect(self._send)

        self.btn_research = QPushButton("Deep Research")
        self.btn_research.clicked.connect(self._research)

        input_row.addWidget(self.input)
        input_row.addWidget(self.btn_chat)
        input_row.addWidget(self.btn_research)
        left_layout.addLayout(input_row)

        splitter.addWidget(left)

        self.sources_panel = SourcesPanel()
        splitter.addWidget(self.sources_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter)

        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

    # -- actions ------------------------------------------------------------

    def _check_ollama(self) -> None:
        try:
            ok = self.client.ping()
            self.status_label.setText(
                f"Connected to {config.MODEL_NAME}" if ok else "Ollama/model not reachable"
            )
        except Exception as exc:  # noqa: BLE001
            self.status_label.setText(f"Ollama error: {exc}")

    def _set_busy(self, busy: bool) -> None:
        enabled = not busy
        self.btn_chat.setEnabled(enabled)
        self.btn_research.setEnabled(enabled)
        self.input.setEnabled(enabled)

    def _send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.chat.add_user(text)
        self.chat.begin_assistant()

        self._set_busy(True)
        self.status_label.setText("Thinking...")

        self._thread = QThread()
        self._task = _ChatTask(self.client, text)
        self._task.moveToThread(self._thread)

        self._task.signals.finished.connect(self._on_chat_done)
        self._task.signals.error.connect(self._on_error)
        self._task.signals.finished.connect(self._thread.quit)
        self._task.signals.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.started.connect(self._task.run)
        self._thread.start()

    def _research(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self.chat.add_user(text)
        self.chat.begin_assistant()
        self.sources_panel.clear()

        self._set_busy(True)
        self.status_label.setText("Researching...")

        self._thread = QThread()
        self._task = _ResearchTask(self.engine, text)
        self._task.moveToThread(self._thread)

        self._task.signals.progress.connect(self._on_progress)
        self._task.signals.finished.connect(self._on_research_done)
        self._task.signals.error.connect(self._on_error)
        self._task.signals.finished.connect(self._thread.quit)
        self._task.signals.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.started.connect(self._task.run)
        self._thread.start()

    # -- callbacks ----------------------------------------------------------

    def _on_progress(self, msg: str) -> None:
        self.status_label.setText(msg)
        self.chat.add_system(msg)

    def _on_chat_done(self, content: str) -> None:
        self.chat.append_assistant(content)
        self._set_busy(False)
        self.status_label.setText("Ready")

    def _on_research_done(self, result) -> None:
        self.chat.append_assistant(result.answer)
        if result.sources:
            self.sources_panel.set_sources(result.sources)
            self.chat.add_sources(result.sources)
        self.status_label.setText(f"Ready — {len(result.sources)} sources")
        self._set_busy(False)

    def _on_error(self, msg: str) -> None:
        self.chat.add_system(f"Error: {msg}")
        self._set_busy(False)
        self.status_label.setText("Ready")
