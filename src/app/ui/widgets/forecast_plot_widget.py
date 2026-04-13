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
        layout.addWidget(self.plot)

    def clear(self) -> None:
        self.plot.clear()

    def draw(self, result: ForecastResult, critical_value: float) -> None:
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
            name="МНК",
        )

        self.plot.plot(
            result.x_grid,
            result.y_gpr_mean,
            pen=pg.mkPen(style=pg.QtCore.Qt.DashLine),
            name="GPR mean",
        )

        upper = result.y_gpr_mean + result.confidence_z * result.y_gpr_std
        lower = result.y_gpr_mean - result.confidence_z * result.y_gpr_std

        ci_brush = pg.mkBrush(100, 149, 237, 60)
        ci_u = pg.PlotDataItem(result.x_grid, upper, pen=None)
        ci_l = pg.PlotDataItem(result.x_grid, lower, pen=None)
        fill = pg.FillBetweenItem(ci_u, ci_l, brush=ci_brush)
        self.plot.addItem(ci_u)
        self.plot.addItem(ci_l)
        self.plot.addItem(fill)

        crit_line = pg.InfiniteLine(
            pos=critical_value,
            angle=0,
            pen=pg.mkPen("r", width=2),
        )
        self.plot.addItem(crit_line)

        if result.t_critical_lsq is not None:
            self.plot.plot(
                [result.t_critical_lsq],
                [critical_value],
                pen=None,
                symbol="x",
                symbolSize=12,
                name="Крит. точка",
            )
