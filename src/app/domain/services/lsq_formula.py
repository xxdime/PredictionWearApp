from __future__ import annotations

import json
from dataclasses import dataclass

import sympy as sp


@dataclass(frozen=True)
class ParsedLSQFormula:
    expression: sp.Expr
    parameter_names: list[str]


def parse_lsq_formula(formula: str) -> ParsedLSQFormula:
    text = formula.strip()
    if not text:
        raise ValueError("Формула МНК не должна быть пустой.")

    if "=" in text:
        _, right = text.split("=", 1)
        expr_text = right.strip()
    else:
        expr_text = text

    if not expr_text:
        raise ValueError("Правая часть формулы пуста.")

    try:
        expr = sp.sympify(expr_text)
    except Exception as e:  # pragma: no cover - тип ошибки зависит от sympy
        raise ValueError(f"Не удалось разобрать формулу: {e}") from e

    symbol_names = {str(s) for s in expr.free_symbols}
    if "x" not in symbol_names:
        raise ValueError("Формула должна содержать переменную x.")

    parameter_names = sorted(name for name in symbol_names if name != "x")
    if not parameter_names:
        raise ValueError("Формула должна содержать хотя бы один параметр кроме x.")

    return ParsedLSQFormula(expression=expr, parameter_names=parameter_names)


def bounds_to_json(bounds: dict[str, tuple[float, float]]) -> str:
    data = {name: [float(low), float(high)] for name, (low, high) in bounds.items()}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def bounds_from_json(raw: str | None) -> dict[str, tuple[float, float]]:
    if not raw:
        return {}

    try:
        data = json.loads(raw)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}

    parsed: dict[str, tuple[float, float]] = {}
    for key, value in data.items():
        if (
            isinstance(key, str)
            and isinstance(value, list)
            and len(value) == 2
            and all(isinstance(v, (int, float)) for v in value)
        ):
            low = float(value[0])
            high = float(value[1])
            if low <= high:
                parsed[key] = (low, high)
    return parsed
