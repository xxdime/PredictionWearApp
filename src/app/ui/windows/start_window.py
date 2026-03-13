from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.ui.windows.templates_window import TemplatesWindow


class StartWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Turbine Wear Forecast")
        self.resize(1000, 700)

        self.templates_window: TemplatesWindow | None = None

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel("Стартовое окно (каркас этапа 3)"))

        self.btn_templates = QPushButton("Шаблоны")
        self.btn_templates.clicked.connect(self.open_templates)
        layout.addWidget(self.btn_templates)

        self.setCentralWidget(central)

    def open_templates(self) -> None:
        if self.templates_window is None:
            self.templates_window = TemplatesWindow()
        self.templates_window.show()
        self.templates_window.raise_()
        self.templates_window.activateWindow()