"""Main window for Taji 1.1 — clean, working layout."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QThread, QObject, Signal, QEvent
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QSplitter, QTextEdit, QLineEdit, QComboBox, QSpinBox,
    QDoubleSpinBox, QGroupBox, QFormLayout, QMessageBox, QProgressBar,
    QSizePolicy, QTextBrowser
)

from .. import config
from ..llm.client import OllamaClient, OllamaError
from ..llm.prompts import CHAT_SYSTEM_PROMPT
from ..research.engine import ResearchEngine
from .chat import ChatView
from .markdown import render_markdown
from .research import SourcesPanel
from .theme import apply_theme


class _ChatWorker(QObject):
    chunk = Signal(str)
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, client: OllamaClient, text: str) -> None:
        super().__init__()
        self.client = client
        self.text = text
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:
        try:
            full = ""
            for chunk in self.client.stream_chat([{"role": "user", "content": self.text}]):
                if self._stop:
                    break
                full += chunk
                self.chunk.emit(chunk)
            self.finished.emit(full)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class _ResearchWorker(QObject):
    progress = Signal(str)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, engine: ResearchEngine, question: str) -> None:
        super().__init__()
        self.engine = engine
        self.question = question

    def run(self) -> None:
        def progress(msg: str) -> None:
            self.progress.emit(msg)

        try:
            result = self.engine.research(self.question, progress=progress)
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{config.APP_NAME} — {config.APP_TAGLINE}")
        self.resize(1280, 800)

        self._theme = "dark"
        self.client = OllamaClient()
        self.engine = ResearchEngine(self.client)
        self._thread: Optional[QThread] = None
        self._worker: Optional[QObject] = None
        self._last_result = None

        self._build_ui()
        apply_theme(QApplication.instance(), self._theme)
        self._check_ollama()

    # -- UI --------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(20, 24, 20, 24)
        s_layout.setSpacing(8)

        logo = QLabel("TAJI")
        logo.setStyleSheet("font-size: 26px; font-weight: 900; color: #22d3ee;")
        s_layout.addWidget(logo)

        ver = QLabel(f"v{config.APP_VERSION}")
        ver.setStyleSheet("font-size: 11px; color: #64748b;")
        s_layout.addWidget(ver)
        s_layout.addSpacing(20)

        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav.setFocusPolicy(Qt.NoFocus)
        # FIX: Hide scrollbars to make the sidebar clean
        self.nav.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.nav_items = [
            ("💬 Chat", "chat"),
            ("🔍 Research", "research"),
            ("📚 Sources", "sources"),
            ("⚙️ Settings", "settings"),
            ("ℹ️ About", "about"),
        ]
        for text, key in self.nav_items:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, key)
            self.nav.addItem(item)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(self._navigate)
        s_layout.addWidget(self.nav)

        s_layout.addStretch()

        self.status_indicator = QLabel("● Checking…")
        self.status_indicator.setStyleSheet("font-size: 12px; color: #ef4444;")
        s_layout.addWidget(self.status_indicator)

        root.addWidget(sidebar)

        # Content
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(0)

        # Top bar
        top = QFrame()
        top.setObjectName("TopBar")
        top.setFixedHeight(56)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setAlignment(Qt.AlignVCenter) # FIX: Center align items vertically

        self.page_title = QLabel("Chat")
        self.page_title.setStyleSheet("font-size: 17px; font-weight: 800;")
        top_layout.addWidget(self.page_title)
        top_layout.addStretch()

        self.model_combo = QComboBox()
        self.model_combo.addItems([config.MODEL_NAME])
        self.model_combo.setFixedWidth(170)
        self.model_combo.setEnabled(False)
        top_layout.addWidget(self.model_combo)
        
        top_layout.addSpacing(10) # Gap between combo and icons

        self.btn_theme = QPushButton("🌙")
        self.btn_theme.setObjectName("IconButton")
        self.btn_theme.setFixedSize(34, 34)
        self.btn_theme.clicked.connect(self._toggle_theme)
        top_layout.addWidget(self.btn_theme)

        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("IconButton")
        self.btn_settings.setFixedSize(34, 34)
        self.btn_settings.clicked.connect(lambda: self._navigate_to("settings"))
        top_layout.addWidget(self.btn_settings)

        c_layout.addWidget(top)

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_chat_page())
        self.stack.addWidget(self._build_research_page())
        self.stack.addWidget(self._build_sources_page())
        self.stack.addWidget(self._build_settings_page())
        self.stack.addWidget(self._build_about_page())
        c_layout.addWidget(self.stack)

        root.addWidget(content)

    def _build_chat_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(20)

        # Chat View Splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        self.chat_view = ChatView()
        self.splitter.addWidget(self.chat_view)

        self.sources_panel = SourcesPanel()
        self.sources_panel.hide() # FIX: Hide until we actually have sources
        self.splitter.addWidget(self.sources_panel)
        
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        layout.addWidget(self.splitter, 1)

        # Sleek Input Bar (Replacing the massive card)
        card = QFrame()
        card.setObjectName("InputCard")
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(8)

        self.user_input = QTextEdit()
        self.user_input.setObjectName("ChatInput")
        self.user_input.setPlaceholderText("Ask Taji anything… (Shift + Enter for newline)")
        self.user_input.setFixedHeight(50)
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_input.installEventFilter(self)
        card_layout.addWidget(self.user_input)

        # Divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #374151; max-height: 1px; margin: 4px 0px;")
        card_layout.addWidget(divider)

        # Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_to_research = QPushButton("🔍 Deep Research")
        self.btn_to_research.setObjectName("GhostButton")
        self.btn_to_research.clicked.connect(lambda: self._navigate_to("research"))
        btn_row.addWidget(self.btn_to_research)

        btn_row.addStretch()

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("Danger")
        self.btn_stop.hide()
        self.btn_stop.clicked.connect(self._stop)
        btn_row.addWidget(self.btn_stop)

        self.btn_send = QPushButton("Send")
        self.btn_send.setObjectName("Primary")
        self.btn_send.clicked.connect(self._send)
        btn_row.addWidget(self.btn_send)

        card_layout.addLayout(btn_row)
        layout.addWidget(card)

        return page

    def _build_research_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(14)

        title = QLabel("Deep Research")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        layout.addWidget(title)

        sub = QLabel("Search the web, fetch sources, and synthesize a grounded answer.")
        sub.setStyleSheet("color: #94a3b8; font-size: 13px;")
        layout.addWidget(sub)

        self.research_input = QLineEdit()
        self.research_input.setPlaceholderText("What should I research?")
        self.research_input.setMinimumHeight(42)
        layout.addWidget(self.research_input)

        row = QHBoxLayout()
        self.btn_start_research = QPushButton("Start Deep Research")
        self.btn_start_research.setObjectName("Primary")
        self.btn_start_research.clicked.connect(self._start_research)
        row.addWidget(self.btn_start_research)
        row.addStretch()
        layout.addLayout(row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.research_status = QLabel("")
        self.research_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.research_status)

        self.research_output = QTextBrowser()
        self.research_output.setReadOnly(True)
        self.research_output.setMinimumHeight(320)
        layout.addWidget(self.research_output)

        src_row = QHBoxLayout()
        self.btn_copy_to_chat = QPushButton("Copy answer to chat")
        self.btn_copy_to_chat.clicked.connect(self._copy_research_to_chat)
        self.btn_copy_to_chat.hide()
        src_row.addStretch()
        src_row.addWidget(self.btn_copy_to_chat)
        layout.addLayout(src_row)

        layout.addStretch()
        return page

    def _build_sources_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(12)

        title = QLabel("Sources")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        layout.addWidget(title)

        self.sources_view = SourcesPanel()
        layout.addWidget(self.sources_view)

        layout.addStretch()
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(18)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 20px; font-weight: 800;")
        layout.addWidget(title)

        form = QGroupBox("Ollama / Model")
        fl = QFormLayout(form)

        self.s_host = QLineEdit(config.OLLAMA_HOST)
        self.s_model = QLineEdit(config.MODEL_NAME)
        self.s_temp = QDoubleSpinBox()
        self.s_temp.setRange(0.0, 2.0)
        self.s_temp.setSingleStep(0.1)
        self.s_temp.setValue(config.DEFAULT_TEMPERATURE)
        self.s_ctx = QSpinBox()
        self.s_ctx.setRange(512, 131072)
        self.s_ctx.setSingleStep(512)
        self.s_ctx.setValue(config.DEFAULT_NUM_CTX)
        self.s_theme = QComboBox()
        self.s_theme.addItems(["Dark", "Light"])
        self.s_theme.setCurrentText("Dark" if self._theme == "dark" else "Light")

        fl.addRow("Host", self.s_host)
        fl.addRow("Model", self.s_model)
        fl.addRow("Temperature", self.s_temp)
        fl.addRow("Context size", self.s_ctx)
        fl.addRow("Theme", self.s_theme)

        layout.addWidget(form)

        btn_save = QPushButton("Save settings")
        btn_save.setObjectName("Primary")
        btn_save.clicked.connect(self._save_settings)
        layout.addWidget(btn_save)

        layout.addStretch()
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(14)

        name = QLabel(config.APP_NAME)
        name.setStyleSheet("font-size: 36px; font-weight: 900; color: #22d3ee;")
        layout.addWidget(name)

        tag = QLabel(config.APP_TAGLINE)
        tag.setStyleSheet("font-size: 15px; color: #94a3b8;")
        layout.addWidget(tag)

        layout.addSpacing(20)

        info = QLabel(
            f"Version: {config.APP_VERSION}<br>"
            f"Model: {config.MODEL_NAME} via Ollama<br>"
            f"Framework: PySide6<br>"
            f"Private local AI research assistant"
        )
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        layout.addStretch()
        return page

    # -- navigation -----------------------------------------------------

    def _navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        keys = [k for _, k in self.nav_items]
        if 0 <= index < len(keys):
            self._update_title(keys[index])

    def _navigate_to(self, name: str) -> None:
        keys = [k for _, k in self.nav_items]
        index = keys.index(name) if name in keys else 0
        self.nav.setCurrentRow(index)
        self.stack.setCurrentIndex(index)
        self._update_title(name)

    def _update_title(self, name: str) -> None:
        titles = {"chat": "Chat", "research": "Deep Research", "sources": "Sources",
                  "settings": "Settings", "about": "About"}
        self.page_title.setText(titles.get(name, name))

    # -- theme ----------------------------------------------------------

    def _toggle_theme(self) -> None:
        self._theme = "light" if self._theme == "dark" else "dark"
        apply_theme(QApplication.instance(), self._theme)
        self.btn_theme.setText("☀️" if self._theme == "dark" else "🌙")
        self.s_theme.setCurrentText(self._theme.capitalize())

    # -- ollama ---------------------------------------------------------

    def _check_ollama(self) -> None:
        try:
            ok = self.client.ping()
            color = "#22c55e" if ok else "#ef4444"
            text = "● Connected" if ok else "● Disconnected"
            self.status_indicator.setText(text)
            self.status_indicator.setStyleSheet(f"font-size: 12px; color: {color};")
        except Exception:  # noqa: BLE001
            self.status_indicator.setText("● Error")
            self.status_indicator.setStyleSheet("font-size: 12px; color: #ef4444;")

    # -- actions --------------------------------------------------------

    def _set_busy(self, busy: bool) -> None:
        self.btn_send.setEnabled(not busy)
        self.btn_start_research.setEnabled(not busy)
        self.user_input.setEnabled(not busy)
        self.research_input.setEnabled(not busy)
        self.btn_stop.setVisible(busy)

    def eventFilter(self, obj, event) -> bool:
        if obj is self.user_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self._send()
                return True
        return super().eventFilter(obj, event)

    def _send(self) -> None:
        text = self.user_input.toPlainText().strip()
        if not text:
            return
        self.user_input.clear()
        self.chat_view.add_user(text)
        self.chat_view.begin_assistant()
        self._set_busy(True)

        self._thread = QThread(self)
        self._worker = _ChatWorker(self.client, text)
        self._worker.moveToThread(self._thread)

        self._worker.chunk.connect(self.chat_view.append_assistant)
        self._worker.finished.connect(self._on_chat_finished)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _stop(self) -> None:
        if isinstance(self._worker, _ChatWorker):
            self._worker.stop()
        self.btn_stop.hide()

    def _on_chat_finished(self, content: str) -> None:
        self.chat_view.finish_assistant()
        self._set_busy(False)

    def _on_error(self, msg: str) -> None:
        self.chat_view.add_system(f"Error: {msg}")
        if hasattr(self.chat_view, "_stream_item"):
            self.chat_view.finish_assistant()
        self._set_busy(False)

    def _start_research(self) -> None:
        text = self.research_input.text().strip()
        if not text:
            return
        self.research_status.setText("Researching…")
        self.progress_bar.show()
        self.btn_start_research.setEnabled(False)
        self.btn_copy_to_chat.hide()
        self.research_output.clear()

        self._thread = QThread(self)
        self._worker = _ResearchWorker(self.engine, text)
        self._worker.moveToThread(self._thread)

        self._worker.progress.connect(self.research_status.setText)
        self._worker.finished.connect(self._on_research_done)
        self._worker.error.connect(self._on_research_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_research_done(self, result) -> None:
        self.progress_bar.hide()
        self.btn_start_research.setEnabled(True)
        self.research_status.setText(f"Done — {len(result.sources)} sources")
        self.research_output.setHtml(render_markdown(result.answer))
        self.btn_copy_to_chat.show()
        self._last_result = result

    def _on_research_error(self, msg: str) -> None:
        self.progress_bar.hide()
        self.btn_start_research.setEnabled(True)
        self.research_status.setText(f"Error: {msg}")

    def _copy_research_to_chat(self) -> None:
        result = self._last_result
        if not result:
            return
        self._navigate_to("chat")
        self.chat_view.add_user(result.question)
        self.chat_view.add_assistant(result.answer)
        
        # Show the sources panel now that we have data
        self.sources_panel.set_sources(result.sources)
        self.sources_panel.show()
        self.chat_view.add_sources(result.sources)

    def _save_settings(self) -> None:
        config.OLLAMA_HOST = self.s_host.text().strip()
        config.MODEL_NAME = self.s_model.text().strip()
        config.DEFAULT_TEMPERATURE = self.s_temp.value()
        config.DEFAULT_NUM_CTX = int(self.s_ctx.value())
        self._theme = "dark" if self.s_theme.currentText() == "Dark" else "light"
        apply_theme(QApplication.instance(), self._theme)
        self.btn_theme.setText("☀️" if self._theme == "dark" else "🌙")
        self.client = OllamaClient()
        self.engine = ResearchEngine(self.client)
        self._check_ollama()
        QMessageBox.information(self, "Settings", "Settings saved.")