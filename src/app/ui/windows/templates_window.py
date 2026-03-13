from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMainWindow,
)

from app.infrastructure.db.models import Template
from app.infrastructure.db.repositories.template_repo import TemplateRepository
from app.ui.dialogs.template_dialog import TemplateDialog
from app.ui.windows.template_parameters_window import TemplateParametersWindow


class TemplatesWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.parameters_window = None
        self.setWindowTitle("Шаблоны")
        self.resize(900, 600)

        self.repo = TemplateRepository()

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        self.list_widget = QListWidget()
        root.addWidget(self.list_widget, 2)

        right = QVBoxLayout()
        root.addLayout(right, 1)

        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_params = QPushButton("Параметры")

        right.addWidget(self.btn_add)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addWidget(self.btn_params)
        right.addStretch()

        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_params.clicked.connect(self.on_params)

        self.reload()

    def reload(self) -> None:
        self.list_widget.clear()
        self._templates = list(self.repo.list())
        for t in self._templates:
            self.list_widget.addItem(f"{t.name}")

    def _selected_template(self) -> Template | None:
        idx = self.list_widget.currentRow()
        if idx < 0 or idx >= len(self._templates):
            return None
        return self._templates[idx]

    def on_add(self) -> None:
        dialog = TemplateDialog(self)
        if dialog.exec():
            name, desc = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Шаблоны", "Название не может быть пустым")
                return
            try:
                self.repo.create(name, desc)
                self.reload()
            except ValueError as e:
                QMessageBox.warning(self, "Шаблоны", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать шаблон:\n{e}")

    def on_edit(self) -> None:
        tmpl = self._selected_template()
        if tmpl is None:
            QMessageBox.warning(self, "Шаблоны", "Выберите шаблон")
            return
        dialog = TemplateDialog(self, name=tmpl.name, description=tmpl.description)
        if dialog.exec():
            name, desc = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Шаблоны", "Название не может быть пустым")
                return
            try:
                self.repo.update(tmpl.id, name, desc)
                self.reload()
            except ValueError as e:
                QMessageBox.warning(self, "Шаблоны", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось изменить шаблон:\n{e}")

    def on_delete(self) -> None:
        tmpl = self._selected_template()
        if tmpl is None:
            QMessageBox.warning(self, "Шаблоны", "Выберите шаблон")
            return
        if QMessageBox.question(
            self, "Удалить", f"Удалить шаблон '{tmpl.name}'?"
        ) == QMessageBox.Yes:
            self.repo.delete(tmpl.id)
            self.reload()

    def on_params(self) -> None:
        tmpl = self._selected_template()
        if tmpl is None:
            QMessageBox.warning(self, "Шаблоны", "Выберите шаблон")
            return
        self.parameters_window = TemplateParametersWindow(tmpl.id, tmpl.name, self)
        self.parameters_window.show()
        self.parameters_window.raise_()
        self.parameters_window.activateWindow()