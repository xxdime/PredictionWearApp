from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.domain.services.forecast_service import ForecastService
from app.infrastructure.db.models import Measurement, Part, TemplateParameter
from app.infrastructure.db.repositories.measurement_repo import MeasurementRepository
from app.infrastructure.db.repositories.part_repo import PartRepository
from app.infrastructure.db.repositories.template_parameter_repo import TemplateParameterRepository
from app.ui.dialogs.measurement_dialog import MeasurementDialog
from app.ui.widgets.forecast_plot_widget import ForecastPlotWidget


class PartWindow(QMainWindow):
    def __init__(self, part_id: int, part_name: str, parent=None) -> None:
        super().__init__(parent)
        self.part_id = part_id
        self.setWindowTitle(f"Деталь: {part_name}")
        self.resize(1300, 800)

        self.part_repo = PartRepository()
        self.param_repo = TemplateParameterRepository()
        self.measurement_repo = MeasurementRepository()
        self.forecast_service = ForecastService(confidence_level=0.95)

        self._part: Part | None = self.part_repo.get(part_id)
        if self._part is None:
            raise RuntimeError(f"Part id={part_id} not found")

        self._parameters: list[TemplateParameter] = []
        self._measurements: list[Measurement] = []

        central = QWidget(self)
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        top = QHBoxLayout()
        top.addWidget(QLabel("Параметр:"))
        self.parameter_combo = QComboBox()
        self.parameter_combo.currentIndexChanged.connect(self.reload_measurements)
        top.addWidget(self.parameter_combo, 1)
        root.addLayout(top)

        center = QGridLayout()
        root.addLayout(center, 1)

        self.measurement_table = QTableWidget(0, 2)
        self.measurement_table.setHorizontalHeaderLabels(["Часы наработки", "Значение"])
        self.measurement_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.measurement_table.setSelectionMode(QTableWidget.SingleSelection)
        self.measurement_table.setEditTriggers(QTableWidget.NoEditTriggers)
        center.addWidget(self.measurement_table, 0, 0)

        right = QVBoxLayout()
        self.btn_add = QPushButton("Добавить измерение")
        self.btn_edit = QPushButton("Изменить измерение")
        self.btn_delete = QPushButton("Удалить измерение")
        self.btn_refresh_plot = QPushButton("Обновить график")

        self.btn_add.clicked.connect(self.on_add_measurement)
        self.btn_edit.clicked.connect(self.on_edit_measurement)
        self.btn_delete.clicked.connect(self.on_delete_measurement)
        self.btn_refresh_plot.clicked.connect(self.on_refresh_plot)

        right.addWidget(self.btn_add)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addSpacing(20)
        right.addWidget(self.btn_refresh_plot)
        right.addStretch()
        center.addLayout(right, 0, 1)

        self.plot_widget = ForecastPlotWidget()
        center.addWidget(self.plot_widget, 1, 0, 1, 2)

        self.lbl_current_param_forecast = QLabel(
            "Прогноз по выбранному параметру: нажмите 'Обновить график'."
        )
        self.lbl_earliest_forecast = QLabel(
            "Самый ранний критический параметр: будет рассчитан после обновления графика."
        )
        root.addWidget(self.lbl_current_param_forecast)
        root.addWidget(self.lbl_earliest_forecast)

        self.reload_parameters()

    def reload_parameters(self) -> None:
        self.parameter_combo.blockSignals(True)
        self.parameter_combo.clear()

        self._parameters = list(self.param_repo.list_by_template(self._part.template_id))
        for p in self._parameters:
            self.parameter_combo.addItem(f"{p.name} ({p.unit})", userData=p.id)

        self.parameter_combo.blockSignals(False)
        self.reload_measurements()

    def _current_parameter(self) -> TemplateParameter | None:
        idx = self.parameter_combo.currentIndex()
        if idx < 0 or idx >= len(self._parameters):
            return None
        return self._parameters[idx]

    def reload_measurements(self) -> None:
        self.measurement_table.setRowCount(0)

        param = self._current_parameter()
        if param is None:
            self._measurements = []
            self.plot_widget.clear()
            return

        self._measurements = list(
            self.measurement_repo.list_by_part_and_parameter(self.part_id, param.id)
        )

        for m in self._measurements:
            row = self.measurement_table.rowCount()
            self.measurement_table.insertRow(row)
            self.measurement_table.setItem(row, 0, QTableWidgetItem(f"{m.operating_hours:.3f}"))
            self.measurement_table.setItem(row, 1, QTableWidgetItem(f"{m.value:.6f}"))

        self.measurement_table.resizeColumnsToContents()

    def _selected_measurement(self) -> Measurement | None:
        row = self.measurement_table.currentRow()
        if row < 0 or row >= len(self._measurements):
            return None
        return self._measurements[row]

    def on_add_measurement(self) -> None:
        param = self._current_parameter()
        if param is None:
            QMessageBox.warning(
                self, "Измерения", "У шаблона нет параметров. Добавьте их в 'Шаблоны'."
            )
            return

        dialog = MeasurementDialog(self)
        if dialog.exec():
            hours, value = dialog.get_data()
            try:
                self.measurement_repo.create(self.part_id, param.id, hours, value)
                self.reload_measurements()
            except ValueError as e:
                QMessageBox.warning(self, "Измерения", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить измерение:\n{e}")

    def on_edit_measurement(self) -> None:
        m = self._selected_measurement()
        if m is None:
            QMessageBox.warning(self, "Измерения", "Выберите измерение.")
            return

        dialog = MeasurementDialog(self, operating_hours=m.operating_hours, value=m.value)
        if dialog.exec():
            hours, value = dialog.get_data()
            try:
                self.measurement_repo.update(m.id, hours, value)
                self.reload_measurements()
            except ValueError as e:
                QMessageBox.warning(self, "Измерения", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось изменить измерение:\n{e}")

    def on_delete_measurement(self) -> None:
        m = self._selected_measurement()
        if m is None:
            QMessageBox.warning(self, "Измерения", "Выберите измерение.")
            return

        if QMessageBox.question(self, "Удалить", "Удалить выбранное измерение?") == QMessageBox.Yes:
            try:
                self.measurement_repo.delete(m.id)
                self.reload_measurements()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить измерение:\n{e}")

    def _collect_points(self, parameter_id: int) -> tuple[list[float], list[float]]:
        ms = list(self.measurement_repo.list_by_part_and_parameter(self.part_id, parameter_id))
        x = [m.operating_hours for m in ms]
        y = [m.value for m in ms]
        return x, y

    def on_refresh_plot(self) -> None:
        param = self._current_parameter()
        if param is None:
            QMessageBox.information(self, "График", "Нет выбранного параметра.")
            return

        x, y = self._collect_points(param.id)
        if len(x) < 2:
            QMessageBox.warning(self, "Недостаточно данных", "Нужно минимум 2 измерения.")
            self.plot_widget.clear()
            self.lbl_current_param_forecast.setText(
                f"Прогноз по '{param.name}': недостаточно данных."
            )
            return

        try:
            result = self.forecast_service.compute(
                operating_hours=x,
                values=y,
                critical_value=param.critical_value,
            )
            self.plot_widget.draw(result, critical_value=param.critical_value)

            if result.t_critical_lsq is None:
                msg = f"По параметру '{param.name}' время достижения критического значения не определено."
            else:
                msg = (
                    f"По параметру '{param.name}' критическое значение будет достигнуто примерно "
                    f"на {result.t_critical_lsq:.2f} ч наработки (оценка МНК)."
                )
            self.lbl_current_param_forecast.setText(msg)

            earliest_name: str | None = None
            earliest_t: float | None = None

            for p in self._parameters:
                px, py = self._collect_points(p.id)
                if len(px) < 2:
                    continue
                r = self.forecast_service.compute(px, py, p.critical_value)
                if r.t_critical_lsq is None:
                    continue
                if earliest_t is None or r.t_critical_lsq < earliest_t:
                    earliest_t = r.t_critical_lsq
                    earliest_name = p.name

            if earliest_name is None or earliest_t is None:
                self.lbl_earliest_forecast.setText(
                    "Самый ранний критический параметр: недостаточно данных для оценки."
                )
            else:
                self.lbl_earliest_forecast.setText(
                    f"Самый ранний критический параметр: '{earliest_name}', "
                    f"примерно на {earliest_t:.2f} ч наработки."
                )

        except Exception as e:
            QMessageBox.critical(self, "Ошибка прогноза", str(e))
