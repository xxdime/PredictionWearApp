from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.windows.start_window import StartWindow


def run() -> int:
    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
