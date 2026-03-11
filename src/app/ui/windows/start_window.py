from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class StartWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Turbine Wear Forecast")
        self.resize(1000, 700)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Стартовое окно (каркас этапа 1)"))

        self.setCentralWidget(central)
