#!/usr/bin/env python3
"""Taji 1.1 application entrypoint."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from taji.ui import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
