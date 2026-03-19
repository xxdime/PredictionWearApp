from __future__ import annotations

import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.domain.services.forecast_service import ForecastResult


class ForecastPlotWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        self.plot = pg.PlotWidget()
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.addLegend()
        layout.addWidget(self.plot)

    def clear(self) -> None:
        self.plot.clear()
        self.plot.addLegend()

    def draw(
        self, result: ForecastResult, critical_value: float, confidence_z: float = 1.96
    ) -> None:
        self.clear()

        self.plot.plot(
            result.x_train,
            result.y_train,
            pen=None,
            symbol="o",
            symbolSize=8,
            name="Измерения",
        )

        self.plot.plot(
            result.x_grid,
            result.y_lsq,
            pen=pg.mkPen(width=2),
            name="МНК (линейная)",
        )

        self.plot.plot(
            result.x_grid,
            result.y_gpr_mean,
            pen=pg.mkPen(style=pg.QtCore.Qt.DashLine),
            name="GPR mean",
        )

        upper = result.y_gpr_mean + confidence_z * result.y_gpr_std
        lower = result.y_gpr_mean - confidence_z * result.y_gpr_std

        ci_brush = pg.mkBrush(100, 149, 237, 60)
        ci_curve_upper = pg.PlotDataItem(result.x_grid, upper, pen=None)
        ci_curve_lower = pg.PlotDataItem(result.x_grid, lower, pen=None)
        fill = pg.FillBetweenItem(ci_curve_upper, ci_curve_lower, brush=ci_brush)
        self.plot.addItem(ci_curve_upper)
        self.plot.addItem(ci_curve_lower)
        self.plot.addItem(fill)

        crit_line = pg.InfiniteLine(
            pos=critical_value,
            angle=0,
            pen=pg.mkPen("r", width=2),
            label="Критическое",
            labelOpts={"position": 0.9, "color": "r"},
        )
        self.plot.addItem(crit_line)

        if result.t_critical_lsq is not None:
            self.plot.plot(
                [result.t_critical_lsq],
                [critical_value],
                pen=None,
                symbol="x",
                symbolSize=12,
                name="Точка достижения критического",
            )
