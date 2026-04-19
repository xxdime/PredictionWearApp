from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sympy as sp
from scipy.optimize import curve_fit

from app.domain.services.lsq_formula import bounds_from_json, parse_lsq_formula

DEFAULT_FORMULA_BOUND_LOW = -1e6
DEFAULT_FORMULA_BOUND_HIGH = 1e6


@dataclass
class ForecastResult:
    x_train: np.ndarray
    y_train: np.ndarray
    x_grid: np.ndarray
    y_lsq: np.ndarray
    y_centered: np.ndarray
    y_upper: np.ndarray
    y_lower: np.ndarray
    bias: float
    rmse: float
    mape: float | None
    slope: float
    intercept: float
    t_critical_lsq: float | None


class ForecastService:
    def _critical_time(
        self,
        slope: float,
        intercept: float,
        critical_value: float,
        x_min: float,
        degradation_direction: str,
    ) -> float | None:
        if abs(slope) < 1e-12:
            return None

        if degradation_direction == "decrease_to_critical":
            if slope >= 0:
                return None
        elif degradation_direction == "increase_to_critical":
            if slope <= 0:
                return None

        t = float((critical_value - intercept) / slope)
        if t < x_min:
            return None
        return t

    def _critical_time_from_curve(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        critical_value: float,
        degradation_direction: str,
    ) -> float | None:
        diff = y_grid - float(critical_value)
        if np.any(np.isclose(diff, 0.0, atol=1e-9)):
            idx = int(np.where(np.isclose(diff, 0.0, atol=1e-9))[0][0])
            return float(x_grid[idx])

        if degradation_direction == "decrease_to_critical":
            crossing_idx = np.where((diff[:-1] > 0) & (diff[1:] < 0))[0]
        else:
            crossing_idx = np.where((diff[:-1] < 0) & (diff[1:] > 0))[0]

        if len(crossing_idx) == 0:
            return None

        idx = int(crossing_idx[0])
        x1, x2 = float(x_grid[idx]), float(x_grid[idx + 1])
        y1, y2 = float(y_grid[idx]), float(y_grid[idx + 1])
        if abs(y2 - y1) < 1e-12:
            return x1
        return x1 + (critical_value - y1) * (x2 - x1) / (y2 - y1)

    def compute(
        self,
        operating_hours: list[float],
        values: list[float],
        critical_value: float,
        *,
        degradation_direction: str = "decrease_to_critical",
        lsq_model_type: str = "linear",
        lsq_poly_degree: int = 1,
        lsq_model_formula: str = "",
        lsq_param_bounds_json: str | None = None,
        confidence_k: float = 2.0,
        horizon_extra: float = 0.25,
    ) -> ForecastResult:
        if len(operating_hours) < 2:
            raise ValueError("Для прогноза нужно минимум 2 измерения.")
        if len(operating_hours) != len(values):
            raise ValueError("Количество точек времени и значений должно совпадать.")

        pairs = sorted(zip(operating_hours, values, strict=True), key=lambda p: p[0])
        x = np.array([p[0] for p in pairs], dtype=float)
        y = np.array([p[1] for p in pairs], dtype=float)

        x_min, x_max = float(x.min()), float(x.max())
        span = max(1.0, x_max - x_min)

        if lsq_model_type == "formula":
            parsed = parse_lsq_formula(lsq_model_formula)
            x_symbol = sp.Symbol("x")
            param_symbols = [sp.Symbol(name) for name in parsed.parameter_names]
            model_fn = sp.lambdify((x_symbol, *param_symbols), parsed.expression, modules="numpy")

            bounds_map = bounds_from_json(lsq_param_bounds_json)
            lower: list[float] = []
            upper: list[float] = []
            p0: list[float] = []
            for param_name in parsed.parameter_names:
                low, high = bounds_map.get(
                    param_name, (DEFAULT_FORMULA_BOUND_LOW, DEFAULT_FORMULA_BOUND_HIGH)
                )
                lower.append(float(low))
                upper.append(float(high))
                p0.append(float((low + high) / 2.0))

            def wrapped_formula(x_data: np.ndarray, *params: float) -> np.ndarray:
                try:
                    return np.asarray(model_fn(x_data, *params), dtype=float)
                except (TypeError, ValueError) as e:
                    raise ValueError(
                        "Формула МНК должна возвращать числовые значения для заданных параметров."
                    ) from e

            popt, _ = curve_fit(
                wrapped_formula,
                x,
                y,
                p0=p0,
                bounds=(lower, upper),
                maxfev=20000,
            )

            y_train_pred = wrapped_formula(x, *popt)

            # Search for the critical crossing on a wide horizon first so that
            # the display grid is always extended to reach the critical value,
            # mirroring the behaviour of the linear/poly branches.
            right_search = x_max + span * 20.0
            x_search = np.linspace(x_min, right_search, 3000)
            y_search = wrapped_formula(x_search, *popt)
            t_critical_lsq = self._critical_time_from_curve(
                x_search, y_search, critical_value, degradation_direction
            )

            right = x_max + span * horizon_extra
            if t_critical_lsq is not None and t_critical_lsq > right:
                right = t_critical_lsq * 1.05

            x_grid = np.linspace(x_min, right, 300)
            y_lsq = wrapped_formula(x_grid, *popt)
            # Recompute on the final grid for a precise crossing point.
            t_critical_lsq = self._critical_time_from_curve(
                x_grid, y_lsq, critical_value, degradation_direction
            )

            if len(x) >= 2:
                slope = float((y_train_pred[-1] - y_train_pred[-2]) / (x[-1] - x[-2]))
            else:
                slope = 0.0
            intercept = float(y_train_pred[-1] - slope * x[-1])
        elif lsq_model_type == "poly":
            degree = max(1, int(lsq_poly_degree))
            coeffs = np.polyfit(x, y, deg=degree)
            poly = np.poly1d(coeffs)

            slope = float(np.polyder(poly)(x_max))
            intercept = float(poly(x_max) - slope * x_max)

            t_critical_lsq = self._critical_time(
                slope, intercept, critical_value, x_min, degradation_direction
            )
            right = x_max + span * horizon_extra
            if t_critical_lsq is not None and t_critical_lsq > right:
                right = t_critical_lsq * 1.05

            x_grid = np.linspace(x_min, right, 300)
            y_lsq = poly(x_grid)
            y_train_pred = poly(x)
        else:
            slope, intercept = np.polyfit(x, y, deg=1)
            slope = float(slope)
            intercept = float(intercept)

            t_critical_lsq = self._critical_time(
                slope, intercept, critical_value, x_min, degradation_direction
            )
            right = x_max + span * horizon_extra
            if t_critical_lsq is not None and t_critical_lsq > right:
                right = t_critical_lsq * 1.05

            x_grid = np.linspace(x_min, right, 300)
            y_lsq = slope * x_grid + intercept
            y_train_pred = slope * x + intercept

        residuals = y - np.asarray(y_train_pred, dtype=float)
        bias = float(np.mean(residuals))
        rmse = float(np.sqrt(np.mean(np.square(residuals))))

        y_nonzero = np.abs(y) > 1e-12
        if np.any(y_nonzero):
            mape = float(
                np.mean(np.abs((y[y_nonzero] - y_train_pred[y_nonzero]) / y[y_nonzero])) * 100
            )
        else:
            mape = None

        k = max(0.0, float(confidence_k))
        y_centered = np.asarray(y_lsq, dtype=float) - bias
        y_upper = y_centered + k * rmse
        y_lower = y_centered - k * rmse

        return ForecastResult(
            x_train=x,
            y_train=y,
            x_grid=x_grid,
            y_lsq=np.asarray(y_lsq, dtype=float),
            y_centered=np.asarray(y_centered, dtype=float),
            y_upper=np.asarray(y_upper, dtype=float),
            y_lower=np.asarray(y_lower, dtype=float),
            bias=bias,
            rmse=rmse,
            mape=mape,
            slope=slope,
            intercept=intercept,
            t_critical_lsq=t_critical_lsq,
        )
