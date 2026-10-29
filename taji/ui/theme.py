"""Theme engine for Taji 1.1."""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

PALETTES = {
    "dark": {
        "BG": "#0b1021",
        "SURFACE": "#111827",
        "SURFACE_ALT": "#1f2937",
        "BORDER": "#374151",
        "TEXT": "#f3f4f6",
        "TEXT_MUTED": "#9ca3af",
        "ACCENT": "#22d3ee",
        "ACCENT_HOVER": "#67e8f9",
        "SUCCESS": "#22c55e",
        "WARNING": "#f59e0b",
        "DANGER": "#ef4444",
    },
    "light": {
        "BG": "#f8fafc",
        "SURFACE": "#ffffff",
        "SURFACE_ALT": "#f1f5f9",
        "BORDER": "#cbd5e1",
        "TEXT": "#0f172a",
        "TEXT_MUTED": "#64748b",
        "ACCENT": "#0891b2",
        "ACCENT_HOVER": "#06b6d4",
        "SUCCESS": "#15803d",
        "WARNING": "#b45309",
        "DANGER": "#dc2626",
    },
}


def _template() -> str:
    return """
    QMainWindow, QWidget { background-color: __BG__; }
    QWidget { color: __TEXT__; font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif; font-size: 13px; }
    QFrame#Sidebar { background-color: __SURFACE__; border-right: 1px solid __BORDER__; }
    QFrame#TopBar { background-color: __SURFACE__; border-bottom: 1px solid __BORDER__; }
    QFrame#InputCard { background-color: __SURFACE__; border: 1px solid __BORDER__; border-radius: 14px; padding: 10px; }
    QListWidget#Nav { background: transparent; border: none; outline: none; }
    QListWidget#Nav::item { background: transparent; padding: 12px 16px; border-radius: 10px; margin: 4px 8px; font-size: 14px; min-height: 40px; }
    QListWidget#Nav::item:selected { background-color: __ACCENT__; color: __BG__; }
    QListWidget#Nav::item:hover:!selected { background-color: __SURFACE_ALT__; }
    QPushButton { background-color: __SURFACE_ALT__; border: 1px solid __BORDER__; border-radius: 8px; padding: 8px 16px; min-width: 90px; }
    QPushButton:hover { background-color: __BORDER__; }
    QPushButton#Primary { background-color: __ACCENT__; color: __BG__; border: none; font-weight: 700; }
    QPushButton#Primary:hover { background-color: __ACCENT_HOVER__; }
    QPushButton#Danger { background-color: __DANGER__; color: #fff; border: none; }
    QPushButton#Danger:hover { background-color: #b91c1c; }
    QLineEdit, QTextEdit { background-color: __SURFACE_ALT__; border: 1px solid __BORDER__; border-radius: 8px; padding: 10px; color: __TEXT__; }
    QLineEdit:focus, QTextEdit:focus { border: 1px solid __ACCENT__; }
    QComboBox { background-color: __SURFACE_ALT__; border: 1px solid __BORDER__; border-radius: 8px; padding: 6px 10px; min-width: 140px; }
    QComboBox::drop-down { border: none; width: 24px; }
    QSpinBox, QDoubleSpinBox { background-color: __SURFACE_ALT__; border: 1px solid __BORDER__; border-radius: 8px; padding: 6px; }
    QProgressBar { border: 1px solid __BORDER__; border-radius: 6px; text-align: center; background: __SURFACE_ALT__; height: 8px; }
    QProgressBar::chunk { background-color: __ACCENT__; border-radius: 6px; }
    QSplitter::handle { background-color: __BORDER__; width: 1px; }
    QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
    QScrollBar::handle:vertical { background: __BORDER__; border-radius: 5px; min-height: 40px; }
    QScrollBar::handle:vertical:hover { background: __TEXT_MUTED__; }
    QTextBrowser { background: transparent; border: none; }
    QLabel { color: __TEXT__; }
    QGroupBox { border: 1px solid __BORDER__; border-radius: 10px; margin-top: 12px; padding-top: 14px; }
    QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: __TEXT_MUTED__; }
    QProgressBar { border: none; }
    """


def stylesheet(name: str = "dark") -> str:
    pal = PALETTES[name]
    css = _template()
    for key, value in pal.items():
        css = css.replace(f"__{key}__", value)
    return css


def apply_theme(app: QApplication, name: str = "dark") -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet(name))
