from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

from app.domain.services.lsq_formula import bounds_from_json, bounds_to_json, parse_lsq_formula


class ForecastConfigDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        lsq_model_formula: str = "",
        lsq_param_bounds_json: str = "{}",
        confidence_k: float = 2.0,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки прогноза")

        layout = QFormLayout(self)

        self.formula_edit = QLineEdit()
        self.formula_edit.setPlaceholderText("y = a * x + b")
        self.formula_edit.setText(lsq_model_formula)

        self.bounds_table = QTableWidget(0, 3)
        self.bounds_table.setHorizontalHeaderLabels(["Параметр", "Мин", "Макс"])
        self._initial_bounds = bounds_from_json(lsq_param_bounds_json)

        self.k_spin = QDoubleSpinBox()
        self.k_spin.setDecimals(3)
        self.k_spin.setRange(0.0, 10.0)
        self.k_spin.setSingleStep(0.1)
        self.k_spin.setValue(float(confidence_k))

        layout.addRow("Формула МНК:", self.formula_edit)
        layout.addRow("Границы параметров:", self.bounds_table)
        layout.addRow("Коэффициент k (RMSE):", self.k_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.formula_edit.editingFinished.connect(self._rebuild_bounds_table)
        self._rebuild_bounds_table()

    def _rebuild_bounds_table(self) -> None:
        formula = self.formula_edit.text().strip()
        if not formula:
            self.bounds_table.setRowCount(0)
            return

        try:
            parsed = parse_lsq_formula(formula)
        except ValueError:
            self.bounds_table.setRowCount(0)
            return

        current_bounds = self._collect_bounds_from_table()
        self.bounds_table.setRowCount(0)
        for name in parsed.parameter_names:
            low, high = current_bounds.get(name, self._initial_bounds.get(name, (-1e6, 1e6)))
            row = self.bounds_table.rowCount()
            self.bounds_table.insertRow(row)
            self.bounds_table.setItem(row, 0, QTableWidgetItem(name))
            self.bounds_table.setItem(row, 1, QTableWidgetItem(str(low)))
            self.bounds_table.setItem(row, 2, QTableWidgetItem(str(high)))

        self.bounds_table.resizeColumnsToContents()

    def _collect_bounds_from_table(self) -> dict[str, tuple[float, float]]:
        bounds: dict[str, tuple[float, float]] = {}
        for row in range(self.bounds_table.rowCount()):
            name_item = self.bounds_table.item(row, 0)
            low_item = self.bounds_table.item(row, 1)
            high_item = self.bounds_table.item(row, 2)
            if name_item is None or low_item is None or high_item is None:
                continue
            try:
                low = float(low_item.text())
                high = float(high_item.text())
            except ValueError:
                continue
            if low <= high:
                bounds[name_item.text()] = (low, high)
        return bounds

    def accept(self) -> None:
        try:
            parsed = parse_lsq_formula(self.formula_edit.text())
        except ValueError as e:
            QMessageBox.warning(self, "Формула МНК", str(e))
            return

        bounds = self._collect_bounds_from_table()
        missing = [name for name in parsed.parameter_names if name not in bounds]
        if missing:
            QMessageBox.warning(
                self,
                "Границы параметров",
                f"Не заданы корректные границы для параметров: {', '.join(missing)}",
            )
            return
        super().accept()

    def get_data(self) -> tuple[str, str, float]:
        bounds_json = bounds_to_json(self._collect_bounds_from_table())
        return (
            self.formula_edit.text().strip(),
            bounds_json,
            float(self.k_spin.value()),
        )
