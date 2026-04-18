from __future__ import annotations

from app.domain.services.lsq_formula import bounds_from_json, bounds_to_json, parse_lsq_formula


def test_parse_lsq_formula_extracts_parameters() -> None:
    parsed = parse_lsq_formula("y = a * x + b")
    assert parsed.parameter_names == ["a", "b"]


def test_bounds_json_roundtrip() -> None:
    bounds = {"a": (-2.0, 2.0), "b": (0.0, 10.0)}
    raw = bounds_to_json(bounds)
    parsed = bounds_from_json(raw)
    assert parsed == bounds
