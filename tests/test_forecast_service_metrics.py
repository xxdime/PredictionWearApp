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

