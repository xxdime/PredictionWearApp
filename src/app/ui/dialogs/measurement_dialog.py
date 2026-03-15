from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout


class MeasurementDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        operating_hours: float = 0.0,
        value: float = 0.0,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Измерение")

        layout = QFormLayout(self)

        self.hours_spin = QDoubleSpinBox()
        self.hours_spin.setDecimals(3)
        self.hours_spin.setRange(0.0, 1e12)
        self.hours_spin.setValue(float(operating_hours))

        self.value_spin = QDoubleSpinBox()
        self.value_spin.setDecimals(6)
        self.value_spin.setRange(-1e12, 1e12)
        self.value_spin.setValue(float(value))

        layout.addRow("Часы наработки:", self.hours_spin)
        layout.addRow("Значение:", self.value_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[float, float]:
        return float(self.hours_spin.value()), float(self.value_spin.value())
