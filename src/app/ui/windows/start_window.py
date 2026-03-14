from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.db.models import Part
from app.infrastructure.db.repositories.part_repo import PartRepository
from app.ui.dialogs.part_dialog import PartDialog
from app.ui.windows.part_window import PartWindow
from app.ui.windows.templates_window import TemplatesWindow


class StartWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Turbine Wear Forecast")
        self.resize(1100, 700)

        self.templates_window: TemplatesWindow | None = None
        self.part_window: PartWindow | None = None

        self.part_repo = PartRepository()

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        left = QVBoxLayout()
        root.addLayout(left, 3)

        left.addWidget(QLabel("Список деталей"))
        self.parts_list = QListWidget()
        self.parts_list.itemDoubleClicked.connect(self.open_selected_part)
        left.addWidget(self.parts_list)

        right = QVBoxLayout()
        root.addLayout(right, 1)

        self.btn_add = QPushButton("Добавить деталь")
        self.btn_edit = QPushButton("Изменить деталь")
        self.btn_delete = QPushButton("Удалить деталь")
        self.btn_templates = QPushButton("Шаблоны")
        self.btn_archive = QPushButton("Архивировать (этап 8)")

        right.addWidget(self.btn_add)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addWidget(self.btn_templates)
        right.addWidget(self.btn_archive)
        right.addStretch()

        self.btn_add.clicked.connect(self.on_add_part)
        self.btn_edit.clicked.connect(self.on_edit_part)
        self.btn_delete.clicked.connect(self.on_delete_part)
        self.btn_templates.clicked.connect(self.open_templates)
        self.btn_archive.clicked.connect(self.on_archive_stub)

        self.reload_parts()

    def reload_parts(self) -> None:
        self.parts_list.clear()
        self._parts = list(self.part_repo.list())
        for p in self._parts:
            serial = f" | SN: {p.serial_number}" if p.serial_number else ""
            self.parts_list.addItem(f"{p.name}{serial}")

    def _selected_part(self) -> Part | None:
        idx = self.parts_list.currentRow()
        if idx < 0 or idx >= len(self._parts):
            return None
        return self._parts[idx]

    def on_add_part(self) -> None:
        dialog = PartDialog(self)
        if not dialog.has_templates():
            QMessageBox.warning(
                self,
                "Детали",
                "Сначала создайте хотя бы один шаблон в разделе 'Шаблоны'.",
            )
            return

        if dialog.exec():
            template_id, name, serial, place, notes = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Детали", "Название детали не может быть пустым.")
                return
            try:
                self.part_repo.create(template_id, name, serial, place, notes)
                self.reload_parts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать деталь:\n{e}")

    def on_edit_part(self) -> None:
        part = self._selected_part()
        if part is None:
            QMessageBox.warning(self, "Детали", "Выберите деталь.")
            return

        dialog = PartDialog(
            self,
            selected_template_id=part.template_id,
            name=part.name,
            serial_number=part.serial_number,
            installation_place=part.installation_place,
            notes=part.notes,
        )
        if dialog.exec():
            template_id, name, serial, place, notes = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Детали", "Название детали не может быть пустым.")
                return
            try:
                self.part_repo.update(part.id, template_id, name, serial, place, notes)
                self.reload_parts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось изменить деталь:\n{e}")

    def on_delete_part(self) -> None:
        part = self._selected_part()
        if part is None:
            QMessageBox.warning(self, "Детали", "Выберите деталь.")
            return

        if (
            QMessageBox.question(self, "Удалить", f"Удалить деталь '{part.name}'?")
            == QMessageBox.Yes
        ):
            try:
                self.part_repo.delete(part.id)
                self.reload_parts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить деталь:\n{e}")

    def open_selected_part(self) -> None:
        part = self._selected_part()
        if part is None:
            return
        self.part_window = PartWindow(part.id, part.name, self)
        self.part_window.show()
        self.part_window.raise_()
        self.part_window.activateWindow()

    def open_templates(self) -> None:
        if self.templates_window is None:
            self.templates_window = TemplatesWindow(self)
        self.templates_window.show()
        self.templates_window.raise_()
        self.templates_window.activateWindow()

    def on_archive_stub(self) -> None:
        QMessageBox.information(self, "Архив", "Функция будет реализована на этапе 8.")

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.open_selected_part()
            return
        super().keyPressEvent(event)
