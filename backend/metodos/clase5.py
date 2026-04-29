import math
import re
from statistics import NormalDist

import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


HEADERS = [
    "Bloque",
    "Muestras acum.",
    "Media f",
    "Varianza f",
    "Volumen",
    "Integral estimada",
    "Error est.",
    "IC +/-",
]

NORMAL_DIST = NormalDist()
DEFAULT_VARIABLES = ["x", "y", "z", "u", "v", "w", "t", "r", "s", "q"]
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
    return re.sub(r"\be\b", "E", str(expr_str).strip())


def _parse_symbolic(expr_str, symbols=None):
    if expr_str is None or not str(expr_str).strip():
        raise ValueError("La expresion no puede estar vacia.")
    return parse_expr(
        _normalize_expression(expr_str),
        transformations=TRANSFORMATIONS,
        local_dict=_base_local_dict(symbols),
        evaluate=True,
    )


def _parse_scalar(value, label):
    try:
        expr = _parse_symbolic(value)
        return float(expr.evalf())
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar {label}='{value}': {exc}") from exc


def _format_number(value, precision):
    return round(float(value), precision)


def _format_message_number(value, precision):
    return f"{float(value):.{min(max(precision, 1), 12)}g}"


def _format_confidence_label(value):
    return f"{value:g}"


def _parse_confidence_level(confidence_level):
    if confidence_level is None or str(confidence_level).strip() == "":
        return 95.0

    try:
        parsed = float(str(confidence_level).strip())
    except Exception as exc:
        raise ValueError(
            f"No se pudo interpretar confidence_level='{confidence_level}' como numero."
        ) from exc

    if not 0 < parsed < 100:
        raise ValueError("El nivel de confianza debe estar entre 0 y 100.")

    return parsed


def _split_bound_pair(text, label):
    cleaned = str(text).strip()
    if not cleaned:
        raise ValueError(f"El limite {label} esta vacio.")

    if "=" in cleaned and cleaned.split("=", 1)[0].strip().isidentifier():
        cleaned = cleaned.split("=", 1)[1].strip()
    elif ":" in cleaned and cleaned.split(":", 1)[0].strip().isidentifier():
        cleaned = cleaned.split(":", 1)[1].strip()

    cleaned = cleaned.strip().strip("[]()")
    if "," in cleaned:
        left, right = cleaned.split(",", 1)
    elif ":" in cleaned:
        left, right = cleaned.split(":", 1)
    else:
        raise ValueError(
            f"Cada limite debe tener dos valores. Ejemplos: 0,1; -1,1 o x:0,pi."
        )

    a = _parse_scalar(left.strip(), f"{label} inferior")
    b = _parse_scalar(right.strip(), f"{label} superior")
    if a == b:
        raise ValueError(f"El limite {label} no puede tener longitud cero.")
    return a, b


def _parse_bounds(bounds_text, dimension_hint=None):
    if not bounds_text or not str(bounds_text).strip():
        raise ValueError("Debes ingresar los limites del dominio.")

    text = str(bounds_text).strip()
    parts = [part.strip() for part in re.split(r";|\n", text) if part.strip()]

    if len(parts) == 1 and dimension_hint and dimension_hint > 1:
        raw_tokens = [token.strip() for token in parts[0].split(",") if token.strip()]
        if len(raw_tokens) == 2 * dimension_hint:
            return [
                (
                    _parse_scalar(raw_tokens[2 * i], f"limite {i + 1} inferior"),
                    _parse_scalar(raw_tokens[2 * i + 1], f"limite {i + 1} superior"),
                )
                for i in range(dimension_hint)
            ]

    return [_split_bound_pair(part, f"dimension {i + 1}") for i, part in enumerate(parts)]


def _parse_variables(variables_text):
    if not variables_text or not str(variables_text).strip():
        return []

    variables = [part.strip() for part in str(variables_text).split(",") if part.strip()]
    if len(set(variables)) != len(variables):
        raise ValueError("Las variables no pueden repetirse.")

    for variable in variables:
        if not re.match(r"^[A-Za-z_]\w*$", variable):
            raise ValueError(f"Variable invalida: '{variable}'.")
    return variables


def _expression_symbols(expr_str):
    symbols = {name: sp.Symbol(name) for name in DEFAULT_VARIABLES}
    try:
        expr = _parse_symbolic(expr_str, symbols)
    except Exception:
        return []

    order = {name: index for index, name in enumerate(DEFAULT_VARIABLES)}
    return [
        str(symbol)
        for symbol in sorted(
            expr.free_symbols,
            key=lambda sym: (order.get(str(sym), len(DEFAULT_VARIABLES)), str(sym)),
        )
    ]


def _resolve_variables(expr_str, variables_text, bounds):
    variables = _parse_variables(variables_text)
    expr_symbols = _expression_symbols(expr_str)

    should_infer = not variables or (
        variables == ["x"] and len(bounds) > 1 and len(expr_symbols) != 1
    )
    if should_infer:
        if len(expr_symbols) == len(bounds):
            variables = expr_symbols
        else:
            variables = DEFAULT_VARIABLES[: len(bounds)]

    if len(variables) != len(bounds):
        raise ValueError(
            "La cantidad de variables debe coincidir con la cantidad de limites. "
            "Ejemplo 2D: variables = x,y y limites = 0,1; 0,1."
        )

    return variables


def _build_integrand(expr_str, variables):
    if not expr_str or not str(expr_str).strip():
        raise ValueError("Debes ingresar una funcion f para integrar.")

    symbols = {name: sp.Symbol(name) for name in variables}
    expr = _parse_symbolic(expr_str, symbols)
    unknown_symbols = [str(symbol) for symbol in expr.free_symbols if str(symbol) not in variables]
    if unknown_symbols:
        raise ValueError(
            "La funcion usa variables que no estan declaradas: "
            + ", ".join(sorted(unknown_symbols))
        )

    ordered_symbols = [symbols[name] for name in variables]
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
    return sp.lambdify(ordered_symbols, expr, modules=modules), expr


def _evaluate_integrand(integrand, samples):
    args = [samples[:, column] for column in range(samples.shape[1])]
    raw_values = integrand(*args)
    values = np.asarray(raw_values)

    if values.shape == ():
        values = np.full(samples.shape[0], values.item())
    else:
        values = np.broadcast_to(values, (samples.shape[0],))

    if np.iscomplexobj(values):
        if np.any(np.abs(np.imag(values)) > 1e-10):
            raise ValueError("La funcion devolvio valores complejos dentro del dominio.")
        values = np.real(values)

    return values.astype(float)


def monte_carlo_integral(
    funcion,
    f_expr_str=None,
    variables=None,
    bounds=None,
    n=None,
    seed=None,
    confidence_level=95,
    max_iter=100,
    tol=1e-6,
    precision=8,
):
    if n is None:
        raise ValueError("Debes ingresar n como cantidad de muestras.")

    n_samples = int(n)
    if n_samples < 2:
        raise ValueError("n debe ser mayor o igual a 2 para estimar dispersion.")
    if n_samples > 1_000_000:
        raise ValueError("n no puede superar 1.000.000 muestras en esta version.")

    confidence_percent = _parse_confidence_level(confidence_level)
    confidence_label = _format_confidence_label(confidence_percent)
    confidence_probability = confidence_percent / 100
    z_value = NORMAL_DIST.inv_cdf((1 + confidence_probability) / 2)

    dimension_hint = len(_parse_variables(variables)) or None
    parsed_bounds = _parse_bounds(bounds, dimension_hint)
    variable_names = _resolve_variables(f_expr_str, variables, parsed_bounds)
    integrand, _ = _build_integrand(f_expr_str, variable_names)

    lower = np.array([min(a, b) for a, b in parsed_bounds], dtype=float)
    upper = np.array([max(a, b) for a, b in parsed_bounds], dtype=float)
    signed_widths = np.array([b - a for a, b in parsed_bounds], dtype=float)
    absolute_widths = upper - lower
    signed_volume = float(np.prod(signed_widths))
    absolute_volume = float(np.prod(absolute_widths))

    parsed_seed = None
    if seed is not None and str(seed).strip():
        parsed_seed = int(str(seed).strip())

    rng = np.random.default_rng(parsed_seed)
    samples = lower + rng.random((n_samples, len(variable_names))) * absolute_widths
    values = _evaluate_integrand(integrand, samples)

    finite_mask = np.isfinite(values)
    if not np.all(finite_mask):
        invalid_count = int(np.size(values) - np.count_nonzero(finite_mask))
        raise ValueError(
            f"La funcion genero {invalid_count} valores no finitos dentro del dominio."
        )

    cumulative_sum = np.cumsum(values)
    cumulative_sq_sum = np.cumsum(values * values)
    block_count = min(10, n_samples)
    endpoints = sorted(set(np.linspace(1, n_samples, block_count, dtype=int).tolist()))

    iteraciones = []
    for block_index, endpoint in enumerate(endpoints, start=1):
        total = float(cumulative_sum[endpoint - 1])
        total_sq = float(cumulative_sq_sum[endpoint - 1])
        mean = total / endpoint
        if endpoint > 1:
            sample_var = max((total_sq - (total * total) / endpoint) / (endpoint - 1), 0.0)
            standard_error = absolute_volume * math.sqrt(sample_var / endpoint)
        else:
            sample_var = 0.0
            standard_error = 0.0

        estimate = signed_volume * mean
        ci_margin = z_value * standard_error
        iteraciones.append(
            [
                block_index,
                endpoint,
                _format_number(mean, precision),
                _format_number(sample_var, precision),
                _format_number(signed_volume, precision),
                _format_number(estimate, precision),
                _format_number(standard_error, precision),
                _format_number(ci_margin, precision),
            ]
        )

    mean = float(np.mean(values))
    sample_var = float(np.var(values, ddof=1))
    sample_std = float(np.std(values, ddof=1))
    estimate = signed_volume * mean
    standard_error = absolute_volume * sample_std / math.sqrt(n_samples)
    estimator_variance = standard_error * standard_error
    ci_margin = z_value * standard_error
    lower_ci = estimate - ci_margin
    upper_ci = estimate + ci_margin

    bounds_summary = "; ".join(
        f"{name} in [{_format_message_number(a, precision)}, {_format_message_number(b, precision)}]"
        for name, (a, b) in zip(variable_names, parsed_bounds)
    )

    lineas = [
        "Monte Carlo completado exitosamente.",
        "",
        "Datos:",
        f"  dimension = {len(variable_names)}",
        f"  variables = {', '.join(variable_names)}",
        f"  limites = {bounds_summary}",
        f"  muestras = {n_samples}",
        f"  volumen = {_format_message_number(signed_volume, precision)}",
        f"  media muestral = {_format_message_number(mean, precision)}",
        f"  varianza muestral f = {_format_message_number(sample_var, precision)}",
        f"  desvio muestral f = {_format_message_number(sample_std, precision)}",
        f"  varianza del estimador = {_format_message_number(estimator_variance, precision)}",
        f"  error estandar = {_format_message_number(standard_error, precision)}",
        f"  nivel confianza = {confidence_label}%",
        f"  z confianza = {_format_message_number(z_value, precision)}",
        f"  IC {confidence_label}% = [{_format_message_number(lower_ci, precision)}, {_format_message_number(upper_ci, precision)}]",
        f"  Integral aproximada = {_format_message_number(estimate, precision)}",
    ]

    if parsed_seed is not None:
        lineas.insert(7, f"  semilla = {parsed_seed}")

    headers = HEADERS[:-1] + [f"IC {confidence_label}% +/-"]

    return iteraciones, "\n".join(lineas), None, None, headers


METODOS = {
    "monte_carlo_integral": {
        "nombre": "Monte Carlo para Integrales",
        "clase": "Clase 5: Monte Carlo",
        "requiere": ["f_expr", "variables", "bounds", "n"],
        "opcionales": ["seed", "confidence_level"],
        "headers": HEADERS,
        "resolver": monte_carlo_integral,
        "root_col": None,
        "uses_raw_expression": True,
    },
}
