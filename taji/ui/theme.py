"""Theme engine for Taji 1.1 — simple, compatible stylesheet."""

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
        "DANGER": "#dc2626",
    },
}


def stylesheet(name: str = "dark") -> str:
    p = PALETTES[name]
    return f"""
    QMainWindow, QWidget {{ background-color: {p['BG']}; color: {p['TEXT']};
        font-family: 'Segoe UI', 'Inter', sans-serif; font-size: 13px; }}
    QFrame#Sidebar {{ background-color: {p['SURFACE']}; border-right: 1px solid {p['BORDER']}; }}
    QFrame#TopBar {{ background-color: {p['SURFACE']}; border-bottom: 1px solid {p['BORDER']}; }}
    QFrame#InputCard {{ background-color: {p['SURFACE']}; border: 1px solid {p['BORDER']};
        border-radius: 12px; padding: 12px; }}
    QListWidget#Nav {{ background: transparent; border: none; outline: none; }}
    QListWidget#Nav::item {{ background: transparent; padding: 14px 18px;
        border-radius: 10px; margin: 4px 10px; font-size: 14px; min-height: 44px; }}
    QListWidget#Nav::item:selected {{ background-color: {p['ACCENT']}; color: {p['BG']}; }}
    QListWidget#Nav::item:hover:!selected {{ background-color: {p['SURFACE_ALT']}; }}
    QPushButton {{ background-color: {p['SURFACE_ALT']}; border: 1px solid {p['BORDER']};
        border-radius: 8px; padding: 8px 16px; min-width: 100px; }}
    QPushButton:hover {{ background-color: {p['BORDER']}; }}
    QPushButton#Primary {{ background-color: {p['ACCENT']}; color: {p['BG']};
        border: none; font-weight: 700; }}
    QPushButton#Primary:hover {{ background-color: {p['ACCENT_HOVER']}; }}
    QPushButton#Danger {{ background-color: {p['DANGER']}; color: #fff; border: none; }}
    QPushButton#Danger:hover {{ background-color: #b91c1c; }}
    QLineEdit, QTextEdit {{ background-color: {p['SURFACE_ALT']}; border: 1px solid {p['BORDER']};
        border-radius: 8px; padding: 10px; color: {p['TEXT']}; }}
    QLineEdit:focus, QTextEdit:focus {{ border: 1px solid {p['ACCENT']}; }}
    QComboBox {{ background-color: {p['SURFACE_ALT']}; border: 1px solid {p['BORDER']};
        border-radius: 8px; padding: 6px 10px; min-width: 140px; }}
    QProgressBar {{ border: none; border-radius: 6px; background: {p['SURFACE_ALT']}; height: 8px; }}
    QProgressBar::chunk {{ background-color: {p['ACCENT']}; border-radius: 6px; }}
    QSplitter::handle {{ background-color: {p['BORDER']}; width: 1px; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
    QScrollBar::handle:vertical {{ background: {p['BORDER']}; border-radius: 5px; min-height: 40px; }}
    QScrollBar::handle:vertical:hover {{ background: {p['TEXT_MUTED']}; }}
    QTextBrowser {{ background: transparent; border: none; }}
    QLabel {{ color: {p['TEXT']}; }}
    QGroupBox {{ border: 1px solid {p['BORDER']}; border-radius: 10px;
        margin-top: 12px; padding-top: 14px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px;
        color: {p['TEXT_MUTED']}; }}
    """


def apply_theme(app: QApplication, name: str = "dark") -> None:
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet(name))
