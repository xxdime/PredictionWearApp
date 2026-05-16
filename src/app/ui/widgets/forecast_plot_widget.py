from __future__ import annotations

import numpy as np
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
            result.y_centered,
            pen=pg.mkPen(style=pg.QtCore.Qt.DashLine),
            name="Центр (МНК - Bias)",
        )

        ci_brush = pg.mkBrush(100, 149, 237, 60)
        ci_u = pg.PlotDataItem(result.x_grid, result.y_upper, pen=None)
        ci_l = pg.PlotDataItem(result.x_grid, result.y_lower, pen=None)
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

        # X mark where the centered line crosses the critical value.
        if result.t_critical_lsq is not None:
            self.plot.plot(
                [result.t_critical_lsq],
                [critical_value],
                pen=None,
                symbol="x",
                symbolSize=14,
                symbolPen=pg.mkPen("r", width=2),
                name="Крит. точка (центр)",
            )

        # Dashed vertical lines for the confidence interval of the critical time.
        if result.t_critical_lower is not None:
            line_lower = pg.InfiniteLine(
                pos=result.t_critical_lower,
                angle=90,
                pen=pg.mkPen("m", width=1, style=pg.QtCore.Qt.DashLine),
                labelOpts={"position": 0.85, "color": "m"},
            )
            self.plot.addItem(line_lower)

        if result.t_critical_upper is not None:
            line_upper = pg.InfiniteLine(
                pos=result.t_critical_upper,
                angle=90,
                pen=pg.mkPen("g", width=1, style=pg.QtCore.Qt.DashLine),
                labelOpts={"position": 0.85, "color": "g"},
            )
            self.plot.addItem(line_upper)

        self._apply_critical_range(result, critical_value)

    def _apply_critical_range(self, result: ForecastResult, critical_value: float) -> None:
        if not np.isfinite(critical_value):
            return

        data = np.concatenate(
            (
                result.y_train,
                result.y_lsq,
                result.y_centered,
                result.y_upper,
                result.y_lower,
            )
        )
        finite = data[np.isfinite(data)]
        if finite.size == 0:
            return

        data_min = float(finite.min())
        data_max = float(finite.max())
        overall_min = min(data_min, float(critical_value))
        overall_max = max(data_max, float(critical_value))

        start = float(result.y_centered[0])
        end = float(result.y_centered[-1])
        is_increasing = end >= start if np.isfinite(start) and np.isfinite(end) else result.slope >= 0

        if is_increasing:
            y_min, y_max = overall_min, float(critical_value)
        else:
            y_min, y_max = float(critical_value), overall_max

        if y_max <= y_min:
            y_min, y_max = overall_min, overall_max

        if y_max - y_min < 1e-9:
            y_max = y_min + 1.0

        self.plot.setYRange(y_min, y_max, padding=0.05)
        self.plot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=False)
