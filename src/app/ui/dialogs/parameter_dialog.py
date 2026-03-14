from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
)


class ParameterDialog(QDialog):
    def __init__(
        self,
        parent=None,
        name: str = "",
        unit: str = "mm",
        critical_value: float = 0.0,
        direction: str = "decrease_to_critical",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Параметр")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        self.unit_edit = QLineEdit(unit)

        self.crit_spin = QDoubleSpinBox()
        self.crit_spin.setDecimals(6)
        self.crit_spin.setRange(-1e9, 1e9)
        self.crit_spin.setValue(float(critical_value))

        self.direction_combo = QComboBox()
        self.direction_combo.addItems(["decrease_to_critical", "increase_to_critical"])
        if direction in ["decrease_to_critical", "increase_to_critical"]:
            self.direction_combo.setCurrentText(direction)

        layout.addRow("Название:", self.name_edit)
        layout.addRow("Ед. изм.:", self.unit_edit)
        layout.addRow("Критическое:", self.crit_spin)
        layout.addRow("Направление:", self.direction_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[str, str, float, str]:
        return (
            self.name_edit.text().strip(),
            self.unit_edit.text().strip(),
            float(self.crit_spin.value()),
            self.direction_combo.currentText(),
        )