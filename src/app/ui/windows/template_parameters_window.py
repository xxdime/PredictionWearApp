from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.db.models import TemplateParameter
from app.infrastructure.db.repositories.template_parameter_repo import TemplateParameterRepository
from app.ui.dialogs.parameter_dialog import ParameterDialog


class TemplateParametersWindow(QMainWindow):
    def __init__(self, template_id: int, template_name: str, parent=None) -> None:
        super().__init__(parent)
        self.template_id = template_id
        self.setWindowTitle(f"Параметры: {template_name}")
        self.resize(900, 500)

        self.repo = TemplateParameterRepository()

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Название", "Ед. изм.", "Критическое", "Направление"]
        )
        root.addWidget(self.table, 3)

        right = QVBoxLayout()
        root.addLayout(right, 1)

        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")

        right.addWidget(self.btn_add)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addStretch()

        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_delete.clicked.connect(self.on_delete)

        self.reload()

    def reload(self) -> None:
        self.table.setRowCount(0)
        self._params = list(self.repo.list_by_template(self.template_id))
        for p in self._params:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(p.name))
            self.table.setItem(row, 1, QTableWidgetItem(p.unit))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.critical_value)))
            self.table.setItem(row, 3, QTableWidgetItem(p.degradation_direction))

    def _selected_param(self) -> TemplateParameter | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._params):
            return None
        return self._params[row]

    def on_add(self) -> None:
        dialog = ParameterDialog(self)
        if dialog.exec():
            name, unit, crit, direction = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Параметры", "Название не может быть пустым")
                return
            try:
                self.repo.create(self.template_id, name, unit, crit, direction)
                self.reload()
            except ValueError as e:
                QMessageBox.warning(self, "Параметры", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать параметр:\n{e}")

    def on_edit(self) -> None:
        param = self._selected_param()
        if param is None:
            QMessageBox.warning(self, "Параметры", "Выберите параметр")
            return
        dialog = ParameterDialog(
            self,
            name=param.name,
            unit=param.unit,
            critical_value=param.critical_value,
            direction=param.degradation_direction,
        )
        if dialog.exec():
            name, unit, crit, direction = dialog.get_data()
            if not name:
                QMessageBox.warning(self, "Параметры", "Название не может быть пустым")
                return
            try:
                self.repo.update(param.id, name, unit, crit, direction)
                self.reload()
            except ValueError as e:
                QMessageBox.warning(self, "Параметры", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать параметр:\n{e}")

    def on_delete(self) -> None:
        param = self._selected_param()
        if param is None:
            QMessageBox.warning(self, "Параметры", "Выберите параметр")
            return
        if QMessageBox.question(self, "Удалить", f"Удалить '{param.name}'?") == QMessageBox.Yes:
            self.repo.delete(param.id)
            self.reload()