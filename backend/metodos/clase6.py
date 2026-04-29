import math
import re

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


RK4_HEADERS_BASE = ["n", "Xn", "Yn", "k1", "k2", "k3", "k4", "Yn+1"]
EULER_HEADERS_BASE = ["n", "Xn", "Yn", "f(Xn,Yn)", "Yn+1"]
TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _nth_root(index, radicand):
    return sp.Pow(radicand, sp.Integer(1) / index)


def _base_local_dict(symbols=None):
    local_dict = {
        "E": sp.E,
        "e": sp.E,
        "pi": sp.pi,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "asin": sp.asin,
        "acos": sp.acos,
        "atan": sp.atan,
        "exp": sp.exp,
        "log": sp.log,
        "ln": sp.log,
        "sqrt": sp.sqrt,
        "nroot": _nth_root,
        "abs": sp.Abs,
    }
    if symbols:
        local_dict.update(symbols)
    return local_dict


def _normalize_expression(expr_str):
    text = str(expr_str).strip()
    text = re.sub(r"\be\b", "E", text)
    return text


def _parse_symbolic(expr_str, symbols):
    if expr_str is None or not str(expr_str).strip():
        raise ValueError("La expresion no puede estar vacia.")

    return parse_expr(
        _normalize_expression(expr_str),
        transformations=TRANSFORMATIONS,
        local_dict=_base_local_dict(symbols),
        evaluate=True,
    )


def _build_ode_function(f_expr_str):
    if not f_expr_str or not str(f_expr_str).strip():
        raise ValueError("Debes ingresar f(x,y) para la ecuacion y' = f(x,y).")

    x, y = sp.symbols("x y")
    expr = _parse_symbolic(f_expr_str, {"x": x, "y": y})
    unknown_symbols = [str(symbol) for symbol in expr.free_symbols if symbol not in (x, y)]
    if unknown_symbols:
        raise ValueError(
            "La funcion de la EDO solo puede usar x e y. Simbolos no reconocidos: "
            + ", ".join(sorted(unknown_symbols))
        )

    modules = [
        "numpy",
        {
            "asin": np.arcsin,
            "acos": np.arccos,
            "atan": np.arctan,
            "E": np.e,
            "pi": np.pi,
            "abs": np.abs,
        },
    ]
    raw_fn = sp.lambdify((x, y), expr, modules=modules)

    def fn(x_value, y_value):
        try:
            result = raw_fn(float(x_value), float(y_value))
            if isinstance(result, complex):
                if abs(result.imag) < 1e-10:
                    result = result.real
                else:
                    raise ValueError("resultado complejo")

            result = float(result)
            if not math.isfinite(result):
                raise ValueError("resultado no finito")
            return result
        except Exception as exc:
            raise ValueError(
                f"No se pudo evaluar f(x,y) en x={x_value}, y={y_value}: {exc}"
            ) from exc

    return fn


def _build_exact_solution(exact_expr_str):
    if exact_expr_str is None or not str(exact_expr_str).strip():
        return None

    x = sp.Symbol("x")
    expr = _parse_symbolic(exact_expr_str, {"x": x})
    unknown_symbols = [str(symbol) for symbol in expr.free_symbols if symbol != x]
    if unknown_symbols:
        raise ValueError(
            "La solucion exacta solo puede depender de x. Simbolos no reconocidos: "
            + ", ".join(sorted(unknown_symbols))
        )

    modules = [
        "numpy",
        {
            "asin": np.arcsin,
            "acos": np.arccos,
            "atan": np.arctan,
            "E": np.e,
            "pi": np.pi,
            "abs": np.abs,
        },
    ]
    raw_fn = sp.lambdify(x, expr, modules=modules)

    def exact_fn(x_value):
        try:
            result = raw_fn(float(x_value))
            if isinstance(result, complex):
                if abs(result.imag) < 1e-10:
                    result = result.real
                else:
                    raise ValueError("resultado complejo")

            result = float(result)
            if not math.isfinite(result):
                raise ValueError("resultado no finito")
            return result
        except Exception as exc:
            raise ValueError(
                f"No se pudo evaluar la solucion exacta en x={x_value}: {exc}"
            ) from exc

    return exact_fn


def _validate_ode_params(y0, h, n):
    if y0 is None:
        raise ValueError("Debes ingresar y0.")
    if h is None:
        raise ValueError("Debes ingresar h (tamano de paso).")
    if n is None:
        raise ValueError("Debes ingresar n (cantidad de pasos).")

    h = float(h)
    n = int(n)
    if h == 0:
        raise ValueError("h no puede ser cero.")
    if n < 1:
        raise ValueError("n debe ser mayor o igual a 1.")

    return float(y0), h, n


def _round(value, precision):
    return round(float(value), precision)


def _format_message_number(value, precision):
    return f"{float(value):.{min(max(precision, 1), 12)}g}"


def _append_exact_columns(row, exact_fn, x_next, y_next, precision):
    if exact_fn is None:
        return row

    y_exact = exact_fn(x_next)
    error = abs(y_exact - y_next)
    row.extend([_round(y_exact, precision), _round(error, precision)])
    return row


def _build_message(method_name, x0, y0, h, n, y_final, exact_fn, x_final, precision):
    lines = [
        f"{method_name} completado exitosamente.",
        "",
        "Datos:",
        f"  x0 = {_format_message_number(x0, precision)}",
        f"  y0 = {_format_message_number(y0, precision)}",
        f"  h = {_format_message_number(h, precision)}",
        f"  n = {n}",
        f"  x final = {_format_message_number(x_final, precision)}",
        f"  y aproximada = {_format_message_number(y_final, precision)}",
    ]

    if exact_fn is not None:
        y_exact = exact_fn(x_final)
        error = abs(y_exact - y_final)
        lines.extend(
            [
                f"  y exacta = {_format_message_number(y_exact, precision)}",
                f"  error absoluto = {_format_message_number(error, precision)}",
            ]
        )

    return "\n".join(lines)


def euler_edo(
    funcion,
    x0,
    f_expr_str=None,
    y0=None,
    h=None,
    n=None,
    exact_expr_str=None,
    max_iter=100,
    tol=1e-6,
    precision=8,
):
    y0, h, n = _validate_ode_params(y0, h, n)
    f = _build_ode_function(f_expr_str)
    exact_fn = _build_exact_solution(exact_expr_str)

    x = float(x0)
    y = y0
    iteraciones = []

    for i in range(n):
        slope = f(x, y)
        x_next = x + h
        y_next = y + h * slope

        row = [
            i,
            _round(x, precision),
            _round(y, precision),
            _round(slope, precision),
            _round(y_next, precision),
        ]
        iteraciones.append(_append_exact_columns(row, exact_fn, x_next, y_next, precision))

        x = x_next
        y = y_next

    headers = EULER_HEADERS_BASE + (["Exacta", "Error"] if exact_fn else [])
    message = _build_message("Metodo de Euler", x0, y0, h, n, y, exact_fn, x, precision)
    return iteraciones, message, None, None, headers


def runge_kutta_4_edo(
    funcion,
    x0,
    f_expr_str=None,
    y0=None,
    h=None,
    n=None,
    exact_expr_str=None,
    max_iter=100,
    tol=1e-6,
    precision=8,
):
    y0, h, n = _validate_ode_params(y0, h, n)
    f = _build_ode_function(f_expr_str)
    exact_fn = _build_exact_solution(exact_expr_str)

    x = float(x0)
    y = y0
    iteraciones = []

    for i in range(n):
        k1 = h * f(x, y)
        k2 = h * f(x + h / 2, y + k1 / 2)
        k3 = h * f(x + h / 2, y + k2 / 2)
        k4 = h * f(x + h, y + k3)
        x_next = x + h
        y_next = y + (k1 + 2 * k2 + 2 * k3 + k4) / 6

        row = [
            i,
            _round(x, precision),
            _round(y, precision),
            _round(k1, precision),
            _round(k2, precision),
            _round(k3, precision),
            _round(k4, precision),
            _round(y_next, precision),
        ]
        iteraciones.append(_append_exact_columns(row, exact_fn, x_next, y_next, precision))

        x = x_next
        y = y_next

    headers = RK4_HEADERS_BASE + (["Exacta", "Error"] if exact_fn else [])
    message = _build_message("Runge-Kutta de orden 4", x0, y0, h, n, y, exact_fn, x, precision)
    return iteraciones, message, None, None, headers


METODOS = {
    "euler_edo": {
        "nombre": "Euler para Ecuaciones Diferenciales",
        "clase": "Clase 6: Ecuaciones Diferenciales",
        "requiere": ["f_expr", "x0", "y0", "h", "n"],
        "opcionales": ["exact_expr"],
        "headers": EULER_HEADERS_BASE,
        "resolver": euler_edo,
        "root_col": None,
        "uses_raw_expression": True,
    },
    "rk4_edo": {
        "nombre": "Runge-Kutta 4 para Ecuaciones Diferenciales",
        "clase": "Clase 6: Ecuaciones Diferenciales",
        "requiere": ["f_expr", "x0", "y0", "h", "n"],
        "opcionales": ["exact_expr"],
        "headers": RK4_HEADERS_BASE,
        "resolver": runge_kutta_4_edo,
        "root_col": None,
        "uses_raw_expression": True,
    },
}
