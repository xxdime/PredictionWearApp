from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import (
    RBF,
    ConstantKernel,
    Matern,
    RationalQuadratic,
    WhiteKernel,
)


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
    confidence_z: float


class ForecastService:
    def _build_kernel(self, kernel_type: str, span: float):
        base_len = max(1.0, span / 3)

        if kernel_type == "Matern":
            kernel = ConstantKernel(1.0, (1e-3, 1e3)) * Matern(length_scale=base_len, nu=1.5)
        elif kernel_type == "RationalQuadratic":
            kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RationalQuadratic(
                length_scale=base_len, alpha=1.0
            )
        else:
            kernel = ConstantKernel(1.0, (1e-3, 1e3)) * RBF(length_scale=base_len)

        return kernel + WhiteKernel(noise_level=1e-3, noise_level_bounds=(1e-8, 1e1))

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

    def compute(
        self,
        operating_hours: list[float],
        values: list[float],
        critical_value: float,
        *,
        degradation_direction: str = "decrease_to_critical",
        lsq_model_type: str = "linear",
        lsq_poly_degree: int = 1,
        gpr_kernel_type: str = "RBF",
        gpr_alpha: float = 1e-6,
        gpr_confidence_level: float = 0.95,
        horizon_extra: float = 0.25,
    ) -> ForecastResult:
        if len(operating_hours) < 2:
            raise ValueError("Для прогноза нужно минимум 2 измерения.")

        pairs = sorted(zip(operating_hours, values), key=lambda p: p[0])
        x = np.array([p[0] for p in pairs], dtype=float)
        y = np.array([p[1] for p in pairs], dtype=float)

        x_min, x_max = float(x.min()), float(x.max())
        span = max(1.0, x_max - x_min)

        if lsq_model_type == "poly":
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

        kernel = self._build_kernel(gpr_kernel_type, span)
        gpr = GaussianProcessRegressor(
            kernel=kernel,
            alpha=max(1e-12, float(gpr_alpha)),
            normalize_y=True,
            n_restarts_optimizer=2,
            random_state=42,
        )

        x_2d = x.reshape(-1, 1)
        xg_2d = x_grid.reshape(-1, 1)
        gpr.fit(x_2d, y)
        y_gpr_mean, y_gpr_std = gpr.predict(xg_2d, return_std=True)

        confidence = min(0.999, max(0.5, float(gpr_confidence_level)))
        confidence_z = float(norm.ppf(0.5 + confidence / 2.0))

        return ForecastResult(
            x_train=x,
            y_train=y,
            x_grid=x_grid,
            y_lsq=np.asarray(y_lsq, dtype=float),
            y_gpr_mean=np.asarray(y_gpr_mean, dtype=float),
            y_gpr_std=np.asarray(y_gpr_std, dtype=float),
            slope=slope,
            intercept=intercept,
            t_critical_lsq=t_critical_lsq,
            confidence_z=confidence_z,
        )
