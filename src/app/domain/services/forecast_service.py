from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel, WhiteKernel


@dataclass
class ForecastResult:
    x_train: np.ndarray
    y_train: np.ndarray
    x_grid: np.ndarray
    y_lsq: np.ndarray
    y_gpr_mean: np.ndarray
    y_gpr_std: np.ndarray
    slope: float
    intercept: float
    t_critical_lsq: float | None


class ForecastService:
    def __init__(self, confidence_level: float = 0.95) -> None:
        self.confidence_level = confidence_level

    def compute(
        self,
        operating_hours: list[float],
        values: list[float],
        critical_value: float,
        horizon_extra: float = 0.25,
    ) -> ForecastResult:
        if len(operating_hours) < 2:
            raise ValueError("Для прогноза нужно минимум 2 измерения.")

        pairs = sorted(zip(operating_hours, values), key=lambda p: p[0])
        x = np.array([p[0] for p in pairs], dtype=float)
        y = np.array([p[1] for p in pairs], dtype=float)

        slope, intercept = np.polyfit(x, y, deg=1)
        y_lsq_train = slope * x + intercept

        t_critical_lsq: float | None
        if abs(slope) < 1e-12:
            t_critical_lsq = None
        else:
            t_critical_lsq = float((critical_value - intercept) / slope)
            if t_critical_lsq < x.min():
                t_critical_lsq = None

        x_min, x_max = float(x.min()), float(x.max())
        span = max(1.0, x_max - x_min)
        right = x_max + span * horizon_extra

        if t_critical_lsq is not None and t_critical_lsq > right:
            right = t_critical_lsq * 1.05

        x_grid = np.linspace(x_min, right, 300)
        y_lsq = slope * x_grid + intercept

        kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(
            length_scale=max(1.0, span / 3)
        ) + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-8, 1e1))
        gpr = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            normalize_y=True,
            n_restarts_optimizer=3,
            random_state=42,
        )

        x_2d = x.reshape(-1, 1)
        xg_2d = x_grid.reshape(-1, 1)
        gpr.fit(x_2d, y)
        y_gpr_mean, y_gpr_std = gpr.predict(xg_2d, return_std=True)

        return ForecastResult(
            x_train=x,
            y_train=y,
            x_grid=x_grid,
            y_lsq=y_lsq,
            y_gpr_mean=y_gpr_mean,
            y_gpr_std=y_gpr_std,
            slope=float(slope),
            intercept=float(intercept),
            t_critical_lsq=t_critical_lsq,
        )
