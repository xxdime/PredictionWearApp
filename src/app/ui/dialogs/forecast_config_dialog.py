from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QSpinBox,
)


class ForecastConfigDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        lsq_model_type: str = "linear",
        lsq_poly_degree: int = 1,
        gpr_kernel_type: str = "RBF",
        gpr_alpha: float = 1e-6,
        gpr_confidence_level: float = 0.95,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки прогноза")

        layout = QFormLayout(self)

        self.lsq_model_combo = QComboBox()
        self.lsq_model_combo.addItems(["linear", "poly"])
        self.lsq_model_combo.setCurrentText(
            lsq_model_type if lsq_model_type in ("linear", "poly") else "linear"
        )

        self.lsq_degree_spin = QSpinBox()
        self.lsq_degree_spin.setRange(1, 8)
        self.lsq_degree_spin.setValue(int(lsq_poly_degree))

        self.gpr_kernel_combo = QComboBox()
        self.gpr_kernel_combo.addItems(["RBF", "Matern", "RationalQuadratic"])
        self.gpr_kernel_combo.setCurrentText(
            gpr_kernel_type if gpr_kernel_type in ("RBF", "Matern", "RationalQuadratic") else "RBF"
        )

        self.gpr_alpha_spin = QDoubleSpinBox()
        self.gpr_alpha_spin.setDecimals(10)
        self.gpr_alpha_spin.setRange(1e-12, 1.0)
        self.gpr_alpha_spin.setSingleStep(1e-6)
        self.gpr_alpha_spin.setValue(float(gpr_alpha))

        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setDecimals(3)
        self.conf_spin.setRange(0.50, 0.999)
        self.conf_spin.setSingleStep(0.01)
        self.conf_spin.setValue(float(gpr_confidence_level))

        layout.addRow("МНК модель:", self.lsq_model_combo)
        layout.addRow("Степень poly:", self.lsq_degree_spin)
        layout.addRow("GPR kernel:", self.gpr_kernel_combo)
        layout.addRow("GPR alpha:", self.gpr_alpha_spin)
        layout.addRow("Доверительный уровень:", self.conf_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[str, int, str, float, float]:
        return (
            self.lsq_model_combo.currentText(),
            int(self.lsq_degree_spin.value()),
            self.gpr_kernel_combo.currentText(),
            float(self.gpr_alpha_spin.value()),
            float(self.conf_spin.value()),
        )
