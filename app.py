#!/usr/bin/env python3
"""Taji 1.1 application entrypoint."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from taji.ui import MainWindow
from taji.ui.theme import apply_theme


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Taji 1.1")
    apply_theme(app, "dark")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())