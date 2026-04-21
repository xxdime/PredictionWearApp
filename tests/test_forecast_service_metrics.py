from __future__ import annotations

import numpy as np
import pytest

from app.domain.services.forecast_service import ForecastService


def test_linear_forecast_uses_bias_rmse_interval() -> None:
    service = ForecastService()
    x = [0.0, 10.0, 20.0, 30.0]
    y = [10.0, 9.0, 8.0, 7.0]

    result = service.compute(
        operating_hours=x,
        values=y,
        critical_value=5.0,
        lsq_model_formula="y = a * x + b",
        lsq_param_bounds_json='{"a":[-1.0,0.0],"b":[0.0,20.0]}',
        confidence_k=2.0,
    )

    assert result.t_critical_lsq is not None
    assert result.t_critical_lsq == pytest.approx(50.0)
    assert result.bias == pytest.approx(0.0, abs=1e-9)
    assert result.rmse == pytest.approx(0.0, abs=1e-9)
    assert result.mape == pytest.approx(0.0, abs=1e-6)
    assert np.allclose(result.y_centered, result.y_lsq)
    assert np.allclose(result.y_upper, result.y_centered)
    assert np.allclose(result.y_lower, result.y_centered)
    # When rmse==0 all three critical times must coincide.
    assert result.t_critical_lower == pytest.approx(50.0)
    assert result.t_critical_upper == pytest.approx(50.0)


def test_formula_forecast_with_bounds() -> None:
    service = ForecastService()
    x = [0.0, 10.0, 20.0, 30.0]
    y = [10.0, 8.0, 6.0, 4.0]

    result = service.compute(
        operating_hours=x,
        values=y,
        critical_value=3.0,
        lsq_model_formula="y = a * x + b",
        lsq_param_bounds_json='{"a":[-1.0,0.0],"b":[0.0,20.0]}',
        confidence_k=1.5,
    )

    assert result.t_critical_lsq is not None
    assert result.t_critical_lsq > 0
    assert result.mape is not None
    assert result.mape < 0.001


def test_formula_forecast_respects_tight_bounds() -> None:
    service = ForecastService()
    x = [0.0, 10.0, 20.0, 30.0]
    y = [10.0, 8.0, 6.0, 4.0]

    result = service.compute(
        operating_hours=x,
        values=y,
        critical_value=3.0,
        lsq_model_formula="y = a * x + b",
        lsq_param_bounds_json='{"a":[-0.1001,-0.0999],"b":[9.999,10.001]}',
        confidence_k=1.5,
    )

    assert -0.1001 <= result.slope <= -0.0999
    assert 9.999 <= result.intercept <= 10.001


def test_power_law_formula_fits_without_bounds() -> None:
    """Power-law formula y=h+k*x**n should converge even without user-specified bounds.

    Previously, p0=(0,0,0) caused x**0=1 everywhere → degenerate Jacobian → optimizer
    overflow and useless fit.  With the fixed p0=1 fallback the fit should be tight.
    """
    import math

    service = ForecastService()
    # Ground truth: h=10, k=-8, n=0.5 (square-root wear curve)
    h_true, k_true, n_true = 10.0, -8.0, 0.5
    x = [0.0, 1.0, 4.0, 9.0, 16.0]
    y = [h_true + k_true * xi**n_true for xi in x]  # [10, 2, -6, -14, -22]

    result = service.compute(
        operating_hours=x,
        values=y,
        critical_value=-5.0,
        lsq_model_formula="y = h + k * x**n",
        # No tight bounds — uses defaults; previously this caused overflow & bad MAPE.
        lsq_param_bounds_json='{"h":[-100,100],"k":[-100,100],"n":[0.01,5.0]}',
        confidence_k=2.0,
    )

    assert result.mape is not None
    assert result.mape < 1.0, f"MAPE too high for power-law fit: {result.mape:.2f}%"
    assert result.t_critical_lsq is not None
    # Exact crossing: h + k*t**n = -5  → t = ((-5-10)/(-8))^2 = 3.515625
    expected_t = ((-5.0 - h_true) / k_true) ** (1.0 / n_true)
    assert result.t_critical_lsq == pytest.approx(expected_t, rel=0.01)
    assert not math.isnan(result.mape)


def test_critical_interval_bounds_ordered() -> None:
    """Lower bound crosses critical sooner, upper bound later."""
    service = ForecastService()
    x = [0.0, 10.0, 20.0, 30.0]
    # Introduce noise so bias/rmse > 0.
    y = [10.0, 8.1, 6.0, 3.9]

    result = service.compute(
        operating_hours=x,
        values=y,
        critical_value=2.0,
        lsq_model_formula="y = a * x + b",
        lsq_param_bounds_json='{"a":[-1.0,0.0],"b":[0.0,20.0]}',
        confidence_k=2.0,
    )

    assert result.t_critical_lsq is not None
    if result.t_critical_lower is not None and result.t_critical_upper is not None:
        t_early = min(result.t_critical_lower, result.t_critical_upper)
        t_late = max(result.t_critical_lower, result.t_critical_upper)
        assert t_early <= result.t_critical_lsq <= t_late

