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
from app.infrastructure.db.repositories.forecast_config_repo import ForecastConfigRepository
from app.infrastructure.db.repositories.template_parameter_repo import TemplateParameterRepository
from app.ui.dialogs.forecast_config_dialog import ForecastConfigDialog
from app.ui.dialogs.parameter_dialog import ParameterDialog


class TemplateParametersWindow(QMainWindow):
    def __init__(self, template_id: int, template_name: str, parent=None) -> None:
        super().__init__(parent)
        self.template_id = template_id
        self.setWindowTitle(f"Параметры: {template_name}")
        self.resize(900, 500)

        self.repo = TemplateParameterRepository()
        self.forecast_cfg_repo = ForecastConfigRepository()

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QHBoxLayout(central)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм.", "Критическое"])
        root.addWidget(self.table, 3)

        right = QVBoxLayout()
        root.addLayout(right, 1)

        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_forecast_cfg = QPushButton("Настройки прогноза")

        right.addWidget(self.btn_add)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addSpacing(12)
        right.addWidget(self.btn_forecast_cfg)
        right.addStretch()

        self.btn_add.clicked.connect(self.on_add)
        self.btn_edit.clicked.connect(self.on_edit)
        self.btn_delete.clicked.connect(self.on_delete)
        self.btn_forecast_cfg.clicked.connect(self.on_forecast_config)

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

    def _selected_param(self) -> TemplateParameter | None:
        row = self.table.currentRow()
        if row < 0 or row >= len(self._params):
            return None
        return self._params[row]

    def on_add(self) -> None:
        dialog = ParameterDialog(self)
        if dialog.exec():
            name, unit, crit = dialog.get_data()
            self.repo.create(self.template_id, name, unit, crit)
            self.reload()

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
        )
        if dialog.exec():
            name, unit, crit = dialog.get_data()
            self.repo.update(param.id, name, unit, crit)
            self.reload()

    def on_delete(self) -> None:
        param = self._selected_param()
        if param is None:
            QMessageBox.warning(self, "Параметры", "Выберите параметр")
            return
        if QMessageBox.question(self, "Удалить", f"Удалить '{param.name}'?") == QMessageBox.Yes:
            self.repo.delete(param.id)
            self.reload()

    def on_forecast_config(self) -> None:
        param = self._selected_param()
        if param is None:
            QMessageBox.warning(self, "Настройки прогноза", "Выберите параметр.")
            return

        cfg = self.forecast_cfg_repo.get_or_create_default(self.template_id, param.id)

        dialog = ForecastConfigDialog(
            self,
            lsq_model_formula=cfg.lsq_model_formula,
            lsq_param_bounds_json=cfg.lsq_param_bounds_json,
            confidence_k=cfg.confidence_k,
        )
        if dialog.exec():
            (
                lsq_model_formula,
                lsq_param_bounds_json,
                confidence_k,
            ) = dialog.get_data()
            self.forecast_cfg_repo.upsert(
                self.template_id,
                param.id,
                lsq_model_formula=lsq_model_formula,
                lsq_param_bounds_json=lsq_param_bounds_json,
                confidence_k=confidence_k,
            )
            QMessageBox.information(self, "Настройки прогноза", "Сохранено.")
