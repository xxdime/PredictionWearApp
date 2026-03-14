from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.infrastructure.db import Base, engine
from app.ui.windows.start_window import StartWindow


def run() -> int:
    Base.metadata.create_all(bind=engine)

    app = QApplication(sys.argv)
    window = StartWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
