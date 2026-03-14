from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget


class PartWindow(QMainWindow):
    def __init__(self, part_id: int, part_name: str, parent=None) -> None:
        super().__init__(parent)
        self.part_id = part_id
        self.setWindowTitle(f"Деталь: {part_name}")
        self.resize(1000, 700)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.addWidget(QLabel(f"Окно детали (этап 5): part_id={part_id}"))
        self.setCentralWidget(central)
