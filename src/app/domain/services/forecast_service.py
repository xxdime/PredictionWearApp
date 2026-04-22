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
    t_critical_lower: float | None
    t_critical_upper: float | None


class ForecastService:
    def _critical_time_from_curve(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        critical_value: float,
    ) -> float | None:
        # Drop non-finite points (can arise from power-law blow-up on wide search grids).
        finite_mask = np.isfinite(y_grid)
        if not np.all(finite_mask):
            x_grid = x_grid[finite_mask]
            y_grid = y_grid[finite_mask]
            if len(x_grid) < 2:
                return None

        diff = y_grid - float(critical_value)
        if np.any(np.isclose(diff, 0.0, atol=1e-9)):
            idx = int(np.where(np.isclose(diff, 0.0, atol=1e-9))[0][0])
            return float(x_grid[idx])

        # Use sign-change detection: overflow-safe (avoids diff[i]*diff[i+1] multiplication).
        s = np.sign(diff)
        crossing_idx = np.where((s[:-1] != 0) & (s[1:] != 0) & (s[:-1] != s[1:]))[0]

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
            mid = (low + high) / 2.0
            if low > 0 and high > 0:
                # Both bounds are strictly positive: use geometric mean so that wide
                # ranges like n=[1,100] start at sqrt(100)=10 rather than 50.5.
                # This prevents x**50 style overflow in the Jacobian during fitting.
                p0.append(float(np.sqrt(low * high)))
            elif abs(mid) < 1e-6:
                # Midpoint is near zero — a degenerate starting point for many nonlinear
                # models (e.g. x**n with n=0 collapses to a constant).  Pick the closest
                # non-zero candidate that still lies inside the bounds.
                candidate = 1.0 if high >= 1.0 else (-1.0 if low <= -1.0 else mid)
                p0.append(float(candidate))
            else:
                p0.append(float(mid))

        def wrapped_formula(x_data: np.ndarray, *params: float) -> np.ndarray:
            try:
                with np.errstate(over="ignore", invalid="ignore"):
                    result = np.asarray(model_fn(x_data, *params), dtype=float)
                # Replace inf/nan with a large finite penalty so the optimizer can
                # compute a gradient and step back toward a feasible region.
                result = np.nan_to_num(result, nan=1e100, posinf=1e100, neginf=-1e100)
                return result
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

        if len(x) >= 2:
            slope = float((y_train_pred[-1] - y_train_pred[-2]) / (x[-1] - x[-2]))
        else:
            slope = 0.0
        intercept = float(y_train_pred[-1] - slope * x[-1])

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

        # Search on a wide horizon to find critical crossings for all three bands.
        right_search = x_max + span * 20.0
        x_search = np.linspace(x_min, right_search, 3000)
        y_search = wrapped_formula(x_search, *popt)
        y_centered_search = y_search - bias
        y_upper_search = y_centered_search + k * rmse
        y_lower_search = y_centered_search - k * rmse

        t_critical_lsq = self._critical_time_from_curve(
            x_search, y_centered_search, critical_value
        )
        t_critical_upper = self._critical_time_from_curve(
            x_search, y_upper_search, critical_value
        )
        t_critical_lower = self._critical_time_from_curve(
            x_search, y_lower_search, critical_value
        )

        # Extend the display grid to include all crossings.
        right = x_max + span * horizon_extra
        for t in (t_critical_lsq, t_critical_upper, t_critical_lower):
            if t is not None and t > right:
                right = t * 1.05

        x_grid = np.linspace(x_min, right, 300)
        y_lsq = wrapped_formula(x_grid, *popt)
        y_centered = np.asarray(y_lsq, dtype=float) - bias
        y_upper = y_centered + k * rmse
        y_lower = y_centered - k * rmse

        # Recompute crossings on the final display grid for precision.
        t_critical_lsq = self._critical_time_from_curve(
            x_grid, y_centered, critical_value
        )
        t_critical_upper = self._critical_time_from_curve(
            x_grid, y_upper, critical_value
        )
        t_critical_lower = self._critical_time_from_curve(
            x_grid, y_lower, critical_value
        )

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
            t_critical_lower=t_critical_lower,
            t_critical_upper=t_critical_upper,
        )

