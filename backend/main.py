from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import numpy as np
import sympy as sp
import math
import re
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

from metodos import REGISTRY

app = FastAPI(title="Métodos Numéricos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class SolveRequest(BaseModel):
    method: str
    f_expr: Optional[str] = ""
    g_expr: Optional[str] = ""
    x_data: Optional[str] = ""
    y_data: Optional[str] = ""
    variables: Optional[str] = ""
    bounds: Optional[str] = ""
    seed: Optional[str] = None
    confidence_level: Optional[str] = None
    a: Optional[str] = None
    b: Optional[str] = None
    e: Optional[str] = None
    x0: Optional[str] = None
    y0: Optional[str] = None
    h: Optional[str] = None
    n: Optional[str] = None
    exact_expr: Optional[str] = ""
    max_iter: int = 100
    tol: float = 1e-6
    precision: int = 8


class CalculusRequest(BaseModel):
    operation: str = Field(..., description="derivar, integrar o edo")
    expression: str = ""
    variable: str = "x"
    dependent_variable: str = "y"
    order: int = Field(1, ge=1, le=6)
    definite: bool = False
    a: Optional[str] = None
    b: Optional[str] = None
    eval_at: Optional[str] = None
    integral_mode: str = "simple"
    double_variables: List[str] = Field(default_factory=lambda: ["x", "y"])
    double_lower_bounds: List[str] = Field(default_factory=list)
    double_upper_bounds: List[str] = Field(default_factory=list)
    ode_mode: str = "linear"
    p_expression: Optional[str] = None
    q_expression: Optional[str] = None
    m_expression: Optional[str] = None
    n_expression: Optional[str] = None
    ode_equation: Optional[str] = None
    initial_condition: Optional[str] = None
    interval_expression: Optional[str] = None
    initial_x: Optional[str] = None
    initial_y: Optional[str] = None


class PolynomialRequest(BaseModel):
    operation: str = Field("expand", description="expand, factor, collect, simplify o all")
    expression: str = Field(..., min_length=1)
    variable: str = "x"
    exact: bool = True


def eval_math_expr(expr_str: str) -> float:
    """Safely evaluates a single math expression to a float."""
    expr = _parse_symbolic_expression(expr_str)
    try:
        val = expr.evalf()
        return float(val)
    except Exception as e:
        raise ValueError(f"Could not evaluate '{expr_str}': {str(e)}")


_PARSER_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _normalize_expression(expr_str: str) -> str:
    text = expr_str.strip()
    text = text.replace("π", "pi")
    text = re.sub(r'\be\b', 'E', text)
    text = re.sub(r'\bx(\d+)\b', r'x**\1', text)
    return text


def _nth_root(index: Any, radicand: Any) -> sp.Expr:
    return sp.Pow(radicand, sp.Integer(1) / index)


def _normalize_variable_names(variables: Any) -> List[str]:
    raw_names = [variables] if isinstance(variables, str) else list(variables or ["x"])
    normalized: List[str] = []

    for name in raw_names:
        candidate = str(name).strip()
        if not re.match(r"^[A-Za-z_]\w*$", candidate):
            raise ValueError(f"Variable inválida '{candidate}'")
        normalized.append(candidate)

    if len(set(normalized)) != len(normalized):
        raise ValueError("Las variables de integración no pueden repetirse.")

    return normalized


def _build_symbolic_locals(variable_names: List[str]) -> Dict[str, Any]:
    local_dict: Dict[str, Any] = {
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
    local_dict.update({name: sp.Symbol(name) for name in variable_names})
    return local_dict


def _parse_symbolic_expression(expr_str: str, variables: Any = "x") -> sp.Expr:
    normalized = _normalize_expression(expr_str)
    variable_names = _normalize_variable_names(variables)
    local_dict = _build_symbolic_locals(variable_names)
    try:
        return parse_expr(normalized, transformations=_PARSER_TRANSFORMATIONS, local_dict=local_dict, evaluate=True)
    except Exception as exc:
        raise ValueError(f"Error parsing expression '{expr_str}': {exc}") from exc


def parse_scalar_value(value: Optional[str], field_name: str) -> Optional[float]:
    """Parse a scalar input that may contain expressions like pi, pi/2 or 2*e."""
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    try:
        return eval_math_expr(text)
    except Exception as exc:
        raise ValueError(f"No se pudo interpretar {field_name}='{text}': {exc}") from exc

# ---------------------------------------------------------------------------
# Safe math expression evaluator using SymPy
# ---------------------------------------------------------------------------
def parse_function(expr_str: Optional[str]):
    """
    Parses a string into a callable function using SymPy.
    Supports basic functions (sin, cos, exp, log, sqrt, etc.).
    """
    if not expr_str:
        return None
    
    try:
        x = sp.Symbol('x')
        expr = _parse_symbolic_expression(expr_str)
        
        # Create a fast callable function using lambdify (uses numpy backend)
        # Adding some fallback functions just in case numpy doesn't cover something exactly
        modules = ["numpy", {"asin": np.arcsin, "acos": np.arccos, "atan": np.arctan, "E": np.e, "pi": np.pi, "abs": np.abs}]
        fn = sp.lambdify(x, expr, modules=modules)
        
        # Wrap it to return float and handle exceptions gracefully
        def safe_fn(val):
            try:
                with np.errstate(all="ignore"):
                    raw_res = fn(val)
                # Handle potential complex numbers returned by sympy/numpy
                if isinstance(raw_res, complex):
                    if abs(raw_res.imag) < 1e-10:
                        raw_res = raw_res.real
                    else:
                        raise ValueError("Complex result")
                
                res = float(raw_res)
                if not math.isfinite(res):
                    raise ValueError("Not finite")
                return res
            except Exception as exc:
                raise ValueError(f"Could not evaluate at x={val}: {str(exc)}")
        safe_fn._sympy_expr = expr
        safe_fn._sympy_symbol = x
        return safe_fn
    except Exception as e:
        raise ValueError(f"Error parsing expression '{expr_str}': {str(e)}")

# ---------------------------------------------------------------------------
# Plot data helper
# ---------------------------------------------------------------------------
def generate_plot_data(fn, center: float = 0, span: float = 50, n: int = 2000):
    """Generate (x, y) arrays for plotting, skipping NaN/Inf values."""
    x_vals = np.linspace(center - span, center + span, n)
    y_vals = []
    x_clean = []
    for xi in x_vals:
        try:
            yi = float(fn(xi))
            if np.isfinite(yi):
                x_clean.append(float(xi))
                y_vals.append(yi)
        except Exception:
            pass
    return x_clean, y_vals


# ---------------------------------------------------------------------------
# Symbolic calculus helpers
# ---------------------------------------------------------------------------
def _step(title: str, detail: str, math_expr: str) -> Dict[str, str]:
    return {"title": title, "detail": detail, "math": math_expr}


def _d_operator(x: sp.Symbol) -> str:
    return rf"\frac{{d}}{{d{sp.latex(x)}}}"


def _integral_operator(expr: sp.Expr, x: sp.Symbol) -> str:
    return rf"\int {sp.latex(expr)}\,d{sp.latex(x)}"


def _iterated_integral_operator(expr: sp.Expr, specs: List[Dict[str, Any]]) -> str:
    operators = "".join(
        rf"\int_{{{sp.latex(spec['lower'])}}}^{{{sp.latex(spec['upper'])}}}"
        for spec in reversed(specs)
    )
    differentials = "".join(rf"\,d{sp.latex(spec['symbol'])}" for spec in specs)
    return rf"{operators} {sp.latex(expr)}{differentials}"


def _iterated_integral_name(total: int) -> str:
    if total == 2:
        return "doble"
    if total == 3:
        return "triple"
    return "iterada"


def _is_constant(expr: sp.Expr, x: sp.Symbol) -> bool:
    return not expr.has(x)


def _format_plain(expr: sp.Expr) -> str:
    text = str(sp.sstr(sp.simplify(expr)))
    return re.sub(r"(?<=\d)\*(?=[A-Za-z_])", "", text)


def _format_symbolic(expr: sp.Expr) -> str:
    text = str(sp.sstr(expr))
    return re.sub(r"(?<=\d)\*(?=[A-Za-z_])", "", text)


def _format_numeric(value: sp.Expr) -> Optional[float]:
    try:
        numeric = float(sp.N(value))
    except Exception:
        return None
    return numeric if math.isfinite(numeric) else None


def _extract_inline_calculus_command(operation: str, expression: str) -> tuple[str, str]:
    text = expression.strip()
    lower_text = text.lower()
    commands = {
        "derivar": "derivar",
        "derivada": "derivar",
        "integrar": "integrar",
        "integral": "integrar",
        "edo": "edo",
        "ode": "edo",
        "ecuacion diferencial": "edo",
    }

    for command, normalized_operation in commands.items():
        prefix = f"{command} "
        if lower_text.startswith(prefix):
            return normalized_operation, text[len(prefix):].strip()

    return operation, text


def _describe_derivative_rule(expr: sp.Expr, x: sp.Symbol) -> str:
    if _is_constant(expr, x):
        return "Derivada de una constante."

    if expr == x:
        return "Derivada de la variable respecto de sí misma."

    if isinstance(expr, sp.Pow) and expr.base == x and _is_constant(expr.exp, x):
        return "Regla de la potencia: el exponente baja multiplicando y luego se resta 1 al exponente."

    coeff, rest = expr.as_coeff_Mul()
    if coeff != 1 and rest.has(x):
        return f"El factor constante {sp.sstr(coeff)} se conserva y se deriva el resto."

    if isinstance(expr, sp.Mul):
        return "Regla del producto para factores que dependen de la variable."

    if expr.func in (sp.sin, sp.cos, sp.tan, sp.exp, sp.log, sp.sqrt):
        arg = expr.args[0]
        if arg == x:
            return f"Regla directa para {expr.func.__name__}({sp.sstr(x)})."
        return "Regla de la cadena: se deriva la función externa y luego la interna."

    if isinstance(expr, sp.Pow) and expr.base.has(x):
        return "Regla de la cadena aplicada a una potencia con base variable."

    return "Simplificación simbólica de la derivada."


def _describe_integral_rule(expr: sp.Expr, x: sp.Symbol) -> str:
    if _is_constant(expr, x):
        return "Integral de una constante: se multiplica por la variable."

    if expr == x:
        return "Regla de la potencia con exponente 1."

    if isinstance(expr, sp.Pow) and expr.base == x and _is_constant(expr.exp, x):
        if sp.simplify(expr.exp + 1) == 0:
            return "Caso especial de la potencia -1: su integral es logaritmo natural."
        return "Regla de la potencia: se suma 1 al exponente y se divide por el nuevo exponente."

    coeff, rest = expr.as_coeff_Mul()
    if coeff != 1 and rest.has(x):
        return f"El factor constante {sp.sstr(coeff)} sale fuera de la integral."

    if expr.func in (sp.sin, sp.cos, sp.exp):
        return f"Regla directa para integrar {expr.func.__name__}({sp.sstr(x)})."

    return "Resolución simbólica de la integral."


def _derivative_steps(expr: sp.Expr, x: sp.Symbol, order: int) -> tuple[List[Dict[str, str]], sp.Expr]:
    steps = [
        _step(
            "Expresión original",
            "Se toma la función ingresada como punto de partida.",
            sp.latex(expr),
        )
    ]

    current = expr
    for index in range(order):
        result = sp.simplify(sp.diff(current, x))
        deriv_label = "Derivada" if order == 1 else f"Derivada de orden {index + 1}"

        if isinstance(current, sp.Add):
            steps.append(
                _step(
                    f"{deriv_label}: linealidad",
                    "Se deriva término a término porque la derivada de una suma es la suma de las derivadas.",
                    rf"{_d_operator(x)}\left({sp.latex(current)}\right) = {sp.latex(result)}",
                )
            )
            for term in current.args:
                term_result = sp.simplify(sp.diff(term, x))
                steps.append(
                    _step(
                        f"Término {sp.latex(term)}",
                        _describe_derivative_rule(term, x),
                        rf"{_d_operator(x)}\left({sp.latex(term)}\right) = {sp.latex(term_result)}",
                    )
                )
        else:
            steps.append(
                _step(
                    deriv_label,
                    _describe_derivative_rule(current, x),
                    rf"{_d_operator(x)}\left({sp.latex(current)}\right) = {sp.latex(result)}",
                )
            )

        current = result

    steps.append(
        _step(
            "Resultado final",
            "Se simplifica la expresión obtenida.",
            sp.latex(current),
        )
    )
    return steps, current


def _integral_steps(
    expr: sp.Expr,
    x: sp.Symbol,
    definite: bool = False,
    a_expr: Optional[sp.Expr] = None,
    b_expr: Optional[sp.Expr] = None,
) -> tuple[List[Dict[str, str]], sp.Expr]:
    antiderivative = sp.simplify(sp.integrate(expr, x))
    if antiderivative.has(sp.Integral):
        raise ValueError("No se pudo resolver la integral simbólicamente con SymPy.")

    steps = [
        _step(
            "Expresión original",
            "Se toma la función ingresada como integrando.",
            sp.latex(expr),
        )
    ]

    if isinstance(expr, sp.Add):
        steps.append(
            _step(
                "Linealidad",
                "Se integra término a término porque la integral de una suma es la suma de las integrales.",
                rf"{_integral_operator(expr, x)} = {sp.latex(antiderivative)} + C",
            )
        )
        for term in expr.args:
            term_result = sp.simplify(sp.integrate(term, x))
            steps.append(
                _step(
                    f"Término {sp.latex(term)}",
                    _describe_integral_rule(term, x),
                    rf"{_integral_operator(term, x)} = {sp.latex(term_result)}",
                )
            )
    else:
        steps.append(
            _step(
                "Antiderivada",
                _describe_integral_rule(expr, x),
                rf"{_integral_operator(expr, x)} = {sp.latex(antiderivative)} + C",
            )
        )

    if definite:
        if a_expr is None or b_expr is None:
            raise ValueError("Para una integral definida se necesitan los límites a y b.")
        result = sp.simplify(antiderivative.subs(x, b_expr) - antiderivative.subs(x, a_expr))
        steps.append(
            _step(
                "Evaluación en los límites",
                "Se aplica el teorema fundamental del cálculo: F(b) - F(a).",
                rf"\left[{sp.latex(antiderivative)}\right]_{{{sp.latex(a_expr)}}}^{{{sp.latex(b_expr)}}} = {sp.latex(result)}",
            )
        )
    else:
        result = antiderivative

    steps.append(
        _step(
            "Resultado final",
            "Se simplifica la expresión obtenida.",
            sp.latex(result) if definite else rf"{sp.latex(result)} + C",
        )
    )
    return steps, result


def _iterated_integral_position(index: int, total: int) -> str:
    if total == 3:
        return ("interna", "intermedia", "externa")[index]
    if index == 0:
        return "interna"
    if index == total - 1:
        return "externa"
    return f"intermedia {index}"


def _validate_iterated_bounds(specs: List[Dict[str, Any]]) -> None:
    for index, spec in enumerate(specs):
        current_symbol = spec["symbol"]
        allowed_symbols = {item["symbol"] for item in specs[index + 1:]}
        allowed_names = ", ".join(sp.sstr(symbol) for symbol in specs[index + 1:])

        for bound_name, bound_expr in (("inferior", spec["lower"]), ("superior", spec["upper"])):
            if current_symbol in bound_expr.free_symbols:
                raise ValueError(
                    f"El límite {bound_name} de {spec['variable']} no puede depender de la misma variable."
                )

            invalid_symbols = bound_expr.free_symbols - allowed_symbols
            if invalid_symbols:
                invalid_names = ", ".join(sorted(sp.sstr(symbol) for symbol in invalid_symbols))
                if allowed_names:
                    raise ValueError(
                        f"El límite {bound_name} de {spec['variable']} solo puede depender de {allowed_names}; "
                        f"se encontró {invalid_names}."
                    )
                raise ValueError(
                    f"El límite {bound_name} de {spec['variable']} debe ser constante; se encontró {invalid_names}."
                )


def _iterated_integral_steps(
    expr: sp.Expr,
    specs: List[Dict[str, Any]],
) -> tuple[List[Dict[str, str]], sp.Expr]:
    integral_name = _iterated_integral_name(len(specs))
    steps = [
        _step(
            f"Integral {integral_name} original",
            "Se plantea la integral iterada en el orden indicado, de adentro hacia afuera.",
            _iterated_integral_operator(expr, specs),
        )
    ]

    current = expr
    total = len(specs)
    for index, spec in enumerate(specs):
        x = spec["symbol"]
        a_expr = spec["lower"]
        b_expr = spec["upper"]
        position = _iterated_integral_position(index, total)
        antiderivative = sp.simplify(sp.integrate(current, x))

        if antiderivative.has(sp.Integral):
            raise ValueError(
                f"No se pudo resolver simbólicamente la integración respecto de {spec['variable']}."
            )

        steps.append(
            _step(
                f"Paso {index + 1}: integral {position}",
                (
                    f"Se integra respecto de {spec['variable']} y las demás variables se tratan como constantes."
                ),
                rf"\int {sp.latex(current)}\,d{sp.latex(x)} = {sp.latex(antiderivative)}",
            )
        )

        evaluated = sp.simplify(antiderivative.subs(x, b_expr) - antiderivative.subs(x, a_expr))
        steps.append(
            _step(
                f"Paso {index + 1}: evaluar límites de {spec['variable']}",
                "Se reemplazan el límite superior e inferior y se calcula F(b) - F(a).",
                rf"\left[{sp.latex(antiderivative)}\right]_{{{sp.latex(a_expr)}}}^{{{sp.latex(b_expr)}}} = {sp.latex(evaluated)}",
            )
        )

        current = evaluated
        remaining_specs = specs[index + 1:]
        if remaining_specs:
            steps.append(
                _step(
                    f"Integrando restante tras {spec['variable']}",
                    "El resultado obtenido se usa como nuevo integrando para la siguiente integral.",
                    _iterated_integral_operator(current, remaining_specs),
                )
            )

    steps.append(
        _step(
            "Resultado final",
            f"Se simplifica el valor final de la integral {integral_name}.",
            sp.latex(sp.simplify(current)),
        )
    )
    return steps, sp.simplify(current)


def _derivative_display_latex(expr: sp.Expr, x: sp.Symbol, order: int, result: sp.Expr) -> str:
    derivative_operator = (
        rf"\frac{{d^{{{order}}}}}{{d{sp.latex(x)}^{{{order}}}}}"
        if order > 1
        else rf"\frac{{d}}{{d{sp.latex(x)}}}"
    )
    return rf"{derivative_operator}\left({sp.latex(expr)}\right) = {sp.latex(result)}"


def _single_integral_display_latex(
    expr: sp.Expr,
    x: sp.Symbol,
    result: sp.Expr,
    definite: bool = False,
    a_expr: Optional[sp.Expr] = None,
    b_expr: Optional[sp.Expr] = None,
) -> str:
    if definite and a_expr is not None and b_expr is not None:
        return rf"\int_{{{sp.latex(a_expr)}}}^{{{sp.latex(b_expr)}}} {sp.latex(expr)}\,d{sp.latex(x)} = {sp.latex(result)}"
    return rf"\int {sp.latex(expr)}\,d{sp.latex(x)} = {sp.latex(result)} + C"


def _required_expression(value: Optional[str], label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Ingresa {label}.")
    return text


def _parse_initial_value(
    value: Optional[str],
    symbol_name: str,
    variables: Any,
    field_label: str,
) -> Optional[sp.Expr]:
    text = str(value or "").strip()
    if not text:
        return None

    if "=" in text:
        left, right = text.split("=", 1)
        if left.strip() == symbol_name:
            text = right.strip()

    parsed = _parse_symbolic_expression(text, variables)
    if parsed.free_symbols:
        raise ValueError(f"{field_label} debe ser un valor numerico, por ejemplo 0, 1/2 o pi.")
    return parsed


def _parse_initial_pair(
    initial_x: Optional[str],
    initial_y: Optional[str],
    x_name: str,
    y_name: str,
    variables: Any,
) -> tuple[Optional[sp.Expr], Optional[sp.Expr]]:
    x_text = str(initial_x or "").strip()
    y_text = str(initial_y or "").strip()
    if bool(x_text) != bool(y_text):
        raise ValueError("Para calcular C ingresa los dos valores del punto inicial: x0 e y0.")
    if not x_text:
        return None, None

    x0 = _parse_initial_value(initial_x, x_name, variables, "x0")
    y0 = _parse_initial_value(initial_y, y_name, variables, "y0")
    return x0, y0


def _normalize_ode_equation_text(equation_text: str, x_name: str, y_name: str) -> str:
    text = equation_text.strip()
    text = text.replace("’", "'").replace("′", "'").replace("≤", "<=")
    text = re.sub(rf"d\s*{re.escape(y_name)}\s*/\s*d\s*{re.escape(x_name)}", "D", text, flags=re.IGNORECASE)
    text = re.sub(
        rf"\b{re.escape(y_name)}\s*(?:\(\s*{re.escape(x_name)}\s*\))?\s*'",
        "D",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(rf"\b{re.escape(x_name.upper())}\b", x_name, text)
    text = re.sub(rf"\b{re.escape(y_name.upper())}\b", y_name, text)
    return text


def _parse_linear_ode_equation(
    equation_text: str,
    x_name: str,
    y_name: str,
) -> tuple[sp.Expr, sp.Expr, str]:
    normalized = _normalize_ode_equation_text(equation_text, x_name, y_name)
    if not normalized:
        raise ValueError("Ingresa la ecuacion diferencial.")

    if "=" in normalized:
        left_text, right_text = normalized.split("=", 1)
    else:
        left_text, right_text = "D", normalized

    variables = [x_name, y_name, "D"]
    x = sp.Symbol(x_name)
    y = sp.Symbol(y_name)
    derivative = sp.Symbol("D")
    left_expr = _parse_symbolic_expression(left_text, variables)
    right_expr = _parse_symbolic_expression(right_text, variables)
    equation_expr = sp.expand(left_expr - right_expr)
    derivative_coeff = sp.simplify(equation_expr.coeff(derivative))

    if derivative_coeff == 0:
        raise ValueError("No se encontro dy/dx ni y' en la ecuacion.")
    if y in derivative_coeff.free_symbols:
        raise ValueError("La calculadora lineal espera que el coeficiente de y' no dependa de y.")

    rest = sp.simplify((equation_expr - derivative_coeff * derivative) / derivative_coeff)
    if derivative in rest.free_symbols:
        raise ValueError("La ecuacion debe ser de primer orden y lineal en y'.")

    p_expr = sp.simplify(rest.coeff(y))
    remainder = sp.simplify(rest - p_expr * y)
    q_expr = sp.simplify(-remainder)

    if y in p_expr.free_symbols or y in q_expr.free_symbols or derivative in (p_expr.free_symbols | q_expr.free_symbols):
        raise ValueError("La ecuacion no esta en una forma lineal compatible: y' + P(x)y = Q(x).")

    invalid_symbols = (p_expr.free_symbols | q_expr.free_symbols) - {x}
    if invalid_symbols:
        invalid_names = ", ".join(sorted(sp.sstr(symbol) for symbol in invalid_symbols))
        raise ValueError(f"P(x) y Q(x) solo pueden depender de {x_name}; se encontro {invalid_names}.")

    standard_latex = (
        rf"\frac{{d{sp.latex(y)}}}{{d{sp.latex(x)}}}"
        rf" + \left({sp.latex(p_expr)}\right){sp.latex(y)} = {sp.latex(q_expr)}"
    )
    return p_expr, q_expr, standard_latex


def _parse_first_order_derivative_equation(
    equation_text: str,
    x_name: str,
    y_name: str,
) -> tuple[sp.Expr, str]:
    normalized = _normalize_ode_equation_text(equation_text, x_name, y_name)
    if not normalized:
        raise ValueError("Ingresa la ecuacion diferencial.")

    if "=" in normalized:
        left_text, right_text = normalized.split("=", 1)
    else:
        left_text, right_text = "D", normalized

    variables = [x_name, y_name, "D"]
    x = sp.Symbol(x_name)
    y = sp.Symbol(y_name)
    derivative = sp.Symbol("D")
    left_expr = _parse_symbolic_expression(left_text, variables)
    right_expr = _parse_symbolic_expression(right_text, variables)
    equation_expr = sp.expand(left_expr - right_expr)
    derivative_coeff = sp.simplify(equation_expr.coeff(derivative))

    if derivative_coeff == 0:
        raise ValueError("No se encontro dy/dx ni y' en la ecuacion.")

    rest = sp.simplify((equation_expr - derivative_coeff * derivative) / derivative_coeff)
    if derivative in rest.free_symbols:
        raise ValueError("La ecuacion debe ser de primer orden y despejable en y'.")

    rhs = sp.simplify(-rest)
    derivative_latex = rf"\frac{{d{sp.latex(y)}}}{{d{sp.latex(x)}}}"
    return rhs, rf"{derivative_latex} = {sp.latex(rhs)}"


def _parse_initial_condition_text(
    condition_text: Optional[str],
    x_name: str,
    y_name: str,
) -> tuple[Optional[sp.Expr], Optional[sp.Expr]]:
    text = str(condition_text or "").strip()
    if not text:
        return None, None

    text = text.replace("Y", y_name).replace("X", x_name)
    match = re.match(
        rf"^\s*{re.escape(y_name)}\s*\(\s*(.*?)\s*\)\s*=\s*(.*?)\s*$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        raise ValueError("La condicion inicial debe tener la forma y(0)=1.")

    x0 = _parse_initial_value(match.group(1), x_name, x_name, "x0")
    y0 = _parse_initial_value(match.group(2), y_name, [x_name, y_name], "y0")
    return x0, y0


def _parse_interval_expression(
    interval_text: Optional[str],
    x_name: str,
) -> Optional[Dict[str, str]]:
    text = str(interval_text or "").strip()
    if not text:
        return None

    normalized = text.replace("≤", "<=")
    match = re.match(rf"^\s*(.*?)\s*<=\s*{re.escape(x_name)}\s*<=\s*(.*?)\s*$", normalized, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"El intervalo debe tener la forma 0 <= {x_name} <= pi/2.")

    lower = _parse_initial_value(match.group(1), x_name, x_name, "limite inferior")
    upper = _parse_initial_value(match.group(2), x_name, x_name, "limite superior")
    if lower is None or upper is None:
        return None

    return {
        "lower": _format_plain(lower),
        "upper": _format_plain(upper),
        "lower_latex": sp.latex(lower),
        "upper_latex": sp.latex(upper),
        "interval_latex": rf"{sp.latex(lower)} \le {sp.latex(sp.Symbol(x_name))} \le {sp.latex(upper)}",
    }


def _ode_lhs_latex(y: sp.Symbol, x: sp.Symbol) -> str:
    return rf"{sp.latex(y)}\left({sp.latex(x)}\right)"


def _format_ode_solution_latex(solutions: List[sp.Expr], y: sp.Symbol, x: sp.Symbol) -> str:
    if not solutions:
        return ""
    lhs = _ode_lhs_latex(y, x)
    branches = [rf"{lhs} = {sp.latex(solution)}" for solution in solutions]
    return r"\quad \text{o} \quad".join(branches)


def _format_ode_solution_plain(solutions: List[sp.Expr], y: sp.Symbol, x: sp.Symbol) -> str:
    if not solutions:
        return ""
    return " ; ".join(
        f"{sp.sstr(y)}({sp.sstr(x)}) = {_format_plain(solution)}"
        for solution in solutions
    )


def _unique_solutions(solutions: List[sp.Expr]) -> List[sp.Expr]:
    unique: List[sp.Expr] = []
    seen = set()
    for solution in solutions:
        simplified = sp.simplify(solution)
        key = sp.sstr(simplified)
        if key not in seen:
            seen.add(key)
            unique.append(simplified)
    return unique


def _filter_solutions_by_initial_point(
    solutions: List[sp.Expr],
    x: sp.Symbol,
    y0: sp.Expr,
    x0: sp.Expr,
) -> List[sp.Expr]:
    filtered: List[sp.Expr] = []
    for solution in solutions:
        try:
            difference = sp.simplify(solution.subs(x, x0) - y0)
            if difference == 0:
                filtered.append(solution)
                continue

            numeric = complex(sp.N(difference))
            if abs(numeric) < 1e-9:
                filtered.append(solution)
        except Exception:
            pass

    return filtered or solutions


def _solve_potential_for_y(
    potential: sp.Expr,
    constant_expr: sp.Expr,
    x: sp.Symbol,
    y: sp.Symbol,
    x0: Optional[sp.Expr] = None,
    y0: Optional[sp.Expr] = None,
) -> List[sp.Expr]:
    try:
        solutions = _unique_solutions(sp.solve(sp.Eq(potential, constant_expr), y))
    except Exception:
        return []

    if x0 is not None and y0 is not None:
        solutions = _filter_solutions_by_initial_point(solutions, x, y0, x0)

    return solutions


def _linear_ode_solution(
    p_expr: sp.Expr,
    q_expr: sp.Expr,
    x: sp.Symbol,
    y: sp.Symbol,
    x0: Optional[sp.Expr],
    y0: Optional[sp.Expr],
    interval_info: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    c = sp.Symbol("C")
    integral_p = sp.simplify(sp.integrate(p_expr, x))
    if integral_p.has(sp.Integral):
        raise ValueError("No se pudo integrar P(x) simbolicamente.")

    integrating_factor = sp.simplify(sp.exp(integral_p))
    weighted_q = sp.simplify(integrating_factor * q_expr)
    integral_weighted_q = sp.simplify(sp.integrate(weighted_q, x))
    if integral_weighted_q.has(sp.Integral):
        raise ValueError("No se pudo integrar el producto mu(x) Q(x) simbolicamente.")

    general_expr = sp.simplify((integral_weighted_q + c) / integrating_factor)
    general_latex = rf"{_ode_lhs_latex(y, x)} = {sp.latex(general_expr)}"
    general_plain = f"{sp.sstr(y)}({sp.sstr(x)}) = {_format_plain(general_expr)}"
    derivative_latex = rf"\frac{{d{sp.latex(y)}}}{{d{sp.latex(x)}}}"
    equation_latex = (
        rf"{derivative_latex} = {sp.latex(q_expr)}"
        if sp.simplify(p_expr) == 0
        else rf"{derivative_latex} + \left({sp.latex(p_expr)}\right){sp.latex(y)} = {sp.latex(q_expr)}"
    )

    steps = [
        _step(
            "EDO lineal",
            "Se plantea la ecuacion en la forma y' + P(x)y = Q(x).",
            equation_latex,
        ),
        _step(
            "Identificacion de P(x) y Q(x)",
            "Se compara con la forma estandar y' + P(x)y = Q(x).",
            rf"P\left({sp.latex(x)}\right) = {sp.latex(p_expr)},\quad Q\left({sp.latex(x)}\right) = {sp.latex(q_expr)}",
        ),
        _step(
            "Factor integrante",
            "Se calcula mu(x) = exp(integral de P(x) dx).",
            rf"\mu\left({sp.latex(x)}\right) = e^{{\int {sp.latex(p_expr)}\,d{sp.latex(x)}}} = {sp.latex(integrating_factor)}",
        ),
        _step(
            "Producto exacto",
            "Al multiplicar por mu(x), el lado izquierdo queda como la derivada de mu(x)y.",
            rf"\frac{{d}}{{d{sp.latex(x)}}}\left({sp.latex(integrating_factor)}{sp.latex(y)}\right) = {sp.latex(weighted_q)}",
        ),
        _step(
            "Integracion",
            "Se integra ambos lados y se despeja y(x).",
            rf"{sp.latex(integrating_factor)}{sp.latex(y)} = \int {sp.latex(weighted_q)}\,d{sp.latex(x)} + C = {sp.latex(integral_weighted_q)} + C",
        ),
        _step(
            "Solucion general",
            "Se despeja la funcion desconocida.",
            general_latex,
        ),
    ]

    c_value = None
    particular_expr = None
    particular_latex = None
    particular_plain = None
    display_latex = general_latex
    result_plain = general_plain
    result_latex = general_latex
    message = f"Solucion general: {general_plain}"

    if x0 is not None and y0 is not None:
        mu_at_x0 = sp.simplify(integrating_factor.subs(x, x0))
        integral_at_x0 = sp.simplify(integral_weighted_q.subs(x, x0))
        c_value = sp.simplify(y0 * mu_at_x0 - integral_at_x0)
        particular_expr = sp.simplify(general_expr.subs(c, c_value))
        particular_latex = rf"{_ode_lhs_latex(y, x)} = {sp.latex(particular_expr)}"
        particular_plain = f"{sp.sstr(y)}({sp.sstr(x)}) = {_format_plain(particular_expr)}"
        display_latex = particular_latex
        result_plain = particular_plain
        result_latex = particular_latex
        message = f"C = {_format_plain(c_value)}\nSolucion particular: {particular_plain}"
        steps.append(
            _step(
                "Condicion inicial",
                "Se reemplaza el punto inicial para calcular la constante C.",
                rf"{sp.latex(y0)} = \left. {sp.latex(general_expr)} \right|_{{{sp.latex(x)}={sp.latex(x0)}}} \Rightarrow C = {sp.latex(c_value)}",
            )
        )
        steps.append(
            _step(
                "Solucion particular",
                "Se reemplaza C en la solucion general.",
                particular_latex,
            )
        )

    return {
        "steps": steps,
        "display_latex": display_latex,
        "result": result_plain,
        "result_latex": result_latex,
        "message": message,
        "ode_solution": {
            "mode": "linear",
            "equation_latex": equation_latex,
            "p": _format_plain(p_expr),
            "p_latex": sp.latex(p_expr),
            "q": _format_plain(q_expr),
            "q_latex": sp.latex(q_expr),
            "general": general_plain,
            "general_latex": general_latex,
            "particular": particular_plain,
            "particular_latex": particular_latex,
            "constant_value": _format_plain(c_value) if c_value is not None else None,
            "constant_latex": sp.latex(c_value) if c_value is not None else None,
            "initial_point_latex": (
                rf"\left({sp.latex(x0)}, {sp.latex(y0)}\right)"
                if x0 is not None and y0 is not None
                else None
            ),
            "integrating_factor_latex": sp.latex(integrating_factor),
            "implicit_latex": None,
            "exactness_latex": None,
            "interval": interval_info,
        },
    }


def _separable_ode_solution(
    rhs_expr: sp.Expr,
    equation_latex: str,
    x: sp.Symbol,
    y: sp.Symbol,
    x0: Optional[sp.Expr],
    y0: Optional[sp.Expr],
    interval_info: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    separated = sp.separatevars(rhs_expr, symbols=[x, y], dict=True, force=True)
    if not separated:
        raise ValueError("No se pudo separar como f(x) g(y).")

    coeff = sp.simplify(separated.get("coeff", sp.Integer(1)))
    x_factor = sp.simplify(coeff * separated.get(x, sp.Integer(1)))
    y_factor = sp.simplify(separated.get(y, sp.Integer(1)))

    if x in y_factor.free_symbols or y in x_factor.free_symbols:
        raise ValueError("La ecuacion no quedo separada en una parte de x y otra de y.")
    if sp.simplify(y_factor) == 0:
        raise ValueError("La parte dependiente de y no puede ser cero para separar variables.")

    left_integrand = sp.simplify(1 / y_factor)
    left_integral = sp.simplify(sp.integrate(left_integrand, y))
    right_integral = sp.simplify(sp.integrate(x_factor, x))
    if left_integral.has(sp.Integral) or right_integral.has(sp.Integral):
        raise ValueError("No se pudieron resolver simbolicamente las integrales de la separacion.")

    c = sp.Symbol("C")
    implicit_general = sp.Eq(left_integral, right_integral + c)
    implicit_general_latex = rf"{sp.latex(left_integral)} = {sp.latex(right_integral)} + C"
    general_solutions = _solve_potential_for_y(left_integral - right_integral, c, x, y)
    general_latex = _format_ode_solution_latex(general_solutions, y, x)
    general_plain = _format_ode_solution_plain(general_solutions, y, x)

    steps = [
        _step(
            "EDO separable",
            "Se interpreta la ecuacion como y' = f(x) g(y).",
            equation_latex,
        ),
        _step(
            "Separacion",
            "Se identifican los factores que dependen solo de x y solo de y.",
            rf"\frac{{d{sp.latex(y)}}}{{d{sp.latex(x)}}} = \left({sp.latex(x_factor)}\right)\left({sp.latex(y_factor)}\right)",
        ),
        _step(
            "Variables separadas",
            "Se pasa la parte de y al lado izquierdo y la parte de x al derecho.",
            rf"\frac{{1}}{{{sp.latex(y_factor)}}}\,d{sp.latex(y)} = {sp.latex(x_factor)}\,d{sp.latex(x)}",
        ),
        _step(
            "Integracion",
            "Se integran ambos lados.",
            rf"\int {sp.latex(left_integrand)}\,d{sp.latex(y)} = \int {sp.latex(x_factor)}\,d{sp.latex(x)} + C",
        ),
        _step(
            "Solucion implicita general",
            "La constante de integracion queda del lado derecho.",
            implicit_general_latex,
        ),
    ]

    c_value = None
    particular_solutions: List[sp.Expr] = []
    particular_latex = None
    particular_plain = None
    implicit_latex = implicit_general_latex
    display_latex = general_latex or implicit_general_latex
    result_latex = display_latex
    result_plain = general_plain or f"{_format_plain(left_integral)} = {_format_plain(right_integral)} + C"
    message = f"Solucion general: {result_plain}"

    if x0 is not None and y0 is not None:
        c_value = sp.simplify(left_integral.subs(y, y0) - right_integral.subs(x, x0))
        implicit_latex = rf"{sp.latex(left_integral)} = {sp.latex(right_integral)} + {sp.latex(c_value)}"
        particular_solutions = _solve_potential_for_y(
            left_integral - right_integral,
            c_value,
            x,
            y,
            x0,
            y0,
        )
        particular_latex = _format_ode_solution_latex(particular_solutions, y, x)
        particular_plain = _format_ode_solution_plain(particular_solutions, y, x)
        display_latex = particular_latex or implicit_latex
        result_latex = display_latex
        result_plain = particular_plain or f"{_format_plain(left_integral)} = {_format_plain(right_integral + c_value)}"
        message = f"C = {_format_plain(c_value)}\nSolucion: {result_plain}"
        steps.append(
            _step(
                "Condicion inicial",
                "Se reemplaza el punto inicial para calcular la constante C.",
                rf"C = {sp.latex(left_integral.subs(y, y0))} - {sp.latex(right_integral.subs(x, x0))} = {sp.latex(c_value)}",
            )
        )
        steps.append(
            _step(
                "Solucion con C calculada",
                "Se reemplaza C y, si es posible, se despeja y(x).",
                display_latex,
            )
        )

    return {
        "steps": steps,
        "display_latex": display_latex,
        "result": result_plain,
        "result_latex": result_latex,
        "message": message,
        "ode_solution": {
            "mode": "separable",
            "equation_latex": equation_latex,
            "general": general_plain or f"{_format_plain(left_integral)} = {_format_plain(right_integral)} + C",
            "general_latex": general_latex or implicit_general_latex,
            "particular": particular_plain,
            "particular_latex": particular_latex,
            "constant_value": _format_plain(c_value) if c_value is not None else None,
            "constant_latex": sp.latex(c_value) if c_value is not None else None,
            "initial_point_latex": (
                rf"\left({sp.latex(x0)}, {sp.latex(y0)}\right)"
                if x0 is not None and y0 is not None
                else None
            ),
            "integrating_factor_latex": None,
            "implicit_latex": implicit_latex,
            "exactness_latex": None,
            "x_factor": _format_plain(x_factor),
            "x_factor_latex": sp.latex(x_factor),
            "y_factor": _format_plain(y_factor),
            "y_factor_latex": sp.latex(y_factor),
            "interval": interval_info,
        },
    }


def _exact_ode_equation_latex(m_expr: sp.Expr, n_expr: sp.Expr, x: sp.Symbol, y: sp.Symbol) -> str:
    return rf"\left({sp.latex(m_expr)}\right)\,d{sp.latex(x)} + \left({sp.latex(n_expr)}\right)\,d{sp.latex(y)} = 0"


def _try_integrating_factor(
    m_expr: sp.Expr,
    n_expr: sp.Expr,
    x: sp.Symbol,
    y: sp.Symbol,
    exactness_difference: sp.Expr,
) -> Optional[Dict[str, Any]]:
    candidates: List[tuple[str, sp.Symbol, sp.Expr]] = []
    if n_expr != 0:
        candidates.append(("x", x, sp.simplify(exactness_difference / n_expr)))
    if m_expr != 0:
        candidates.append(("y", y, sp.simplify(-exactness_difference / m_expr)))

    for variable_name, variable_symbol, rate in candidates:
        other_symbol = y if variable_symbol == x else x
        if other_symbol in rate.free_symbols:
            continue

        try:
            exponent = sp.simplify(sp.integrate(rate, variable_symbol))
        except Exception:
            continue
        if exponent.has(sp.Integral):
            continue

        factor = sp.simplify(sp.exp(exponent))
        next_m = sp.simplify(factor * m_expr)
        next_n = sp.simplify(factor * n_expr)
        next_difference = sp.simplify(sp.diff(next_m, y) - sp.diff(next_n, x))
        if next_difference == 0:
            return {
                "variable_name": variable_name,
                "symbol": variable_symbol,
                "rate": rate,
                "factor": factor,
                "m": next_m,
                "n": next_n,
            }

    return None


def _potential_from_exact_ode(
    m_expr: sp.Expr,
    n_expr: sp.Expr,
    x: sp.Symbol,
    y: sp.Symbol,
) -> tuple[sp.Expr, sp.Expr, sp.Expr]:
    base_potential = sp.simplify(sp.integrate(m_expr, x))
    if base_potential.has(sp.Integral):
        raise ValueError("No se pudo integrar M respecto de x simbolicamente.")

    correction_derivative = sp.simplify(n_expr - sp.diff(base_potential, y))
    if x in correction_derivative.free_symbols:
        raise ValueError("La ecuacion no pudo transformarse en exacta con los datos ingresados.")

    correction = sp.simplify(sp.integrate(correction_derivative, y))
    if correction.has(sp.Integral):
        raise ValueError("No se pudo integrar el termino restante respecto de y simbolicamente.")

    potential = sp.simplify(base_potential + correction)
    return potential, base_potential, correction


def _exact_ode_solution(
    m_expr: sp.Expr,
    n_expr: sp.Expr,
    x: sp.Symbol,
    y: sp.Symbol,
    x0: Optional[sp.Expr],
    y0: Optional[sp.Expr],
) -> Dict[str, Any]:
    original_m = m_expr
    original_n = n_expr
    equation_latex = _exact_ode_equation_latex(m_expr, n_expr, x, y)
    m_y = sp.simplify(sp.diff(m_expr, y))
    n_x = sp.simplify(sp.diff(n_expr, x))
    exactness_difference = sp.simplify(m_y - n_x)
    exactness_latex = rf"\frac{{\partial M}}{{\partial {sp.latex(y)}}} = {sp.latex(m_y)},\quad \frac{{\partial N}}{{\partial {sp.latex(x)}}} = {sp.latex(n_x)}"

    steps = [
        _step(
            "EDO exacta",
            "Se plantea la ecuacion diferencial en la forma M(x,y) dx + N(x,y) dy = 0.",
            equation_latex,
        ),
        _step(
            "Prueba de exactitud",
            "Se compara la derivada parcial de M respecto de y con la de N respecto de x.",
            exactness_latex,
        ),
    ]

    integrating_factor_latex = None
    if exactness_difference != 0:
        factor_data = _try_integrating_factor(m_expr, n_expr, x, y, exactness_difference)
        if factor_data is None:
            raise ValueError(
                "La ecuacion no es exacta y no se encontro un factor integrante simple en x o en y."
            )

        m_expr = factor_data["m"]
        n_expr = factor_data["n"]
        integrating_factor_latex = sp.latex(factor_data["factor"])
        steps.append(
            _step(
                "Factor integrante",
                f"No era exacta. Se encontro un factor integrante dependiente de {factor_data['variable_name']}.",
                rf"\mu\left({sp.latex(factor_data['symbol'])}\right) = e^{{\int {sp.latex(factor_data['rate'])}\,d{sp.latex(factor_data['symbol'])}}} = {integrating_factor_latex}",
            )
        )
        steps.append(
            _step(
                "Ecuacion equivalente exacta",
                "Se multiplica M y N por el factor integrante.",
                _exact_ode_equation_latex(m_expr, n_expr, x, y),
            )
        )
    else:
        steps.append(
            _step(
                "Exactitud confirmada",
                "Las derivadas parciales coinciden, entonces existe una funcion potencial F(x,y).",
                rf"\frac{{\partial M}}{{\partial {sp.latex(y)}}} - \frac{{\partial N}}{{\partial {sp.latex(x)}}} = 0",
            )
        )

    potential, base_potential, correction = _potential_from_exact_ode(m_expr, n_expr, x, y)
    c = sp.Symbol("C")
    implicit_general_latex = rf"{sp.latex(potential)} = C"
    steps.extend([
        _step(
            "Potencial parcial",
            "Se integra M respecto de x.",
            rf"F\left({sp.latex(x)}, {sp.latex(y)}\right) = \int {sp.latex(m_expr)}\,d{sp.latex(x)} = {sp.latex(base_potential)} + h\left({sp.latex(y)}\right)",
        ),
        _step(
            "Termino restante",
            "Se usa N para hallar h(y).",
            rf"h\left({sp.latex(y)}\right) = {sp.latex(correction)}",
        ),
        _step(
            "Solucion implicita general",
            "La solucion queda dada por F(x,y) = C.",
            implicit_general_latex,
        ),
    ])

    general_solutions = _solve_potential_for_y(potential, c, x, y)
    general_latex = _format_ode_solution_latex(general_solutions, y, x)
    general_plain = _format_ode_solution_plain(general_solutions, y, x)

    c_value = None
    particular_solutions: List[sp.Expr] = []
    particular_latex = None
    particular_plain = None
    implicit_latex = implicit_general_latex
    display_latex = general_latex or implicit_general_latex
    result_latex = display_latex
    result_plain = general_plain or f"{_format_plain(potential)} = C"
    message = f"Solucion implicita general: {_format_plain(potential)} = C"

    if x0 is not None and y0 is not None:
        c_value = sp.simplify(potential.subs({x: x0, y: y0}))
        implicit_latex = rf"{sp.latex(potential)} = {sp.latex(c_value)}"
        particular_solutions = _solve_potential_for_y(potential, c_value, x, y, x0, y0)
        particular_latex = _format_ode_solution_latex(particular_solutions, y, x)
        particular_plain = _format_ode_solution_plain(particular_solutions, y, x)
        display_latex = particular_latex or implicit_latex
        result_latex = display_latex
        result_plain = particular_plain or f"{_format_plain(potential)} = {_format_plain(c_value)}"
        message = f"C = {_format_plain(c_value)}\nSolucion: {result_plain}"
        steps.append(
            _step(
                "Condicion inicial",
                "Se reemplaza el punto inicial en F(x,y) = C.",
                rf"C = F\left({sp.latex(x0)}, {sp.latex(y0)}\right) = {sp.latex(c_value)}",
            )
        )
        steps.append(
            _step(
                "Solucion con C calculada",
                "Se reemplaza C y, si es posible, se despeja y(x).",
                display_latex,
            )
        )

    return {
        "steps": steps,
        "display_latex": display_latex,
        "result": result_plain,
        "result_latex": result_latex,
        "message": message,
        "ode_solution": {
            "mode": "exact",
            "equation_latex": equation_latex,
            "general": general_plain or f"{_format_plain(potential)} = C",
            "general_latex": general_latex or implicit_general_latex,
            "particular": particular_plain,
            "particular_latex": particular_latex,
            "constant_value": _format_plain(c_value) if c_value is not None else None,
            "constant_latex": sp.latex(c_value) if c_value is not None else None,
            "initial_point_latex": (
                rf"\left({sp.latex(x0)}, {sp.latex(y0)}\right)"
                if x0 is not None and y0 is not None
                else None
            ),
            "integrating_factor_latex": integrating_factor_latex,
            "implicit_latex": implicit_latex,
            "exactness_latex": exactness_latex,
            "original_equation_latex": _exact_ode_equation_latex(original_m, original_n, x, y),
        },
    }


def _polynomial_form(label: str, expr: sp.Expr) -> Dict[str, str]:
    return {
        "label": label,
        "plain": _format_symbolic(expr),
        "latex": sp.latex(expr),
    }


def _make_polynomial_coefficients(poly: sp.Poly, x: sp.Symbol) -> List[Dict[str, Any]]:
    coefficients = []
    degree = poly.degree()
    for exponent, coefficient in zip(range(degree, -1, -1), poly.all_coeffs()):
        term_expr = coefficient * x**exponent
        coefficients.append({
            "degree": int(exponent),
            "coefficient": _format_symbolic(coefficient),
            "coefficient_latex": sp.latex(coefficient),
            "term_latex": sp.latex(term_expr),
        })
    return coefficients


def _polynomial_steps(
    original_expr: sp.Expr,
    normalized_expr: sp.Expr,
    expanded: sp.Expr,
    collected: sp.Expr,
    factored: sp.Expr,
    simplified: sp.Expr,
    exact: bool,
) -> List[Dict[str, str]]:
    steps = [
        _step(
            "Expresión original",
            "Se toma la expresión ingresada como punto de partida.",
            sp.latex(original_expr),
        )
    ]

    if exact and sp.sstr(original_expr) != sp.sstr(normalized_expr):
        steps.append(
            _step(
                "Normalización exacta",
                "Los decimales se convierten a fracciones para evitar redondeos en el álgebra simbólica.",
                sp.latex(normalized_expr),
            )
        )

    steps.extend([
        _step(
            "Distributiva",
            "Se expanden productos y potencias para obtener la suma de términos.",
            sp.latex(expanded),
        ),
        _step(
            "Agrupar términos semejantes",
            "Se ordenan y agrupan los términos según la potencia de la variable.",
            sp.latex(collected),
        ),
        _step(
            "Factorizar",
            "Se busca una forma factorizada equivalente.",
            sp.latex(factored),
        ),
        _step(
            "Simplificar",
            "Se reduce la expresión conservando una forma algebraicamente equivalente.",
            sp.latex(simplified),
        ),
    ])
    return steps


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/methods")
def list_methods():
    """Return all registered methods grouped by class, for the frontend."""
    methods = {}
    for key, info in REGISTRY.items():
        methods[key] = {
            "nombre": info["nombre"],
            "clase": info["clase"],
            "requiere": info["requiere"],
            "opcionales": info.get("opcionales", []),
            "headers": info["headers"],
            "marco_teorico": info.get("marco_teorico"),
        }
    return methods


@app.post("/api/calculus")
def calculate_symbolic(req: CalculusRequest):
    """Calculate symbolic derivatives, integrals and first-order ODEs."""
    try:
        operation = req.operation.strip().lower()
        operation, expression_text = _extract_inline_calculus_command(operation, req.expression)
        if operation not in ("edo", "ode", "ecuacion_diferencial", "differential") and not expression_text:
            raise ValueError("Ingresa una expresion para calcular.")
        expr = sp.Integer(0)
        variable = req.variable.strip() or "x"
        operation_label = ""
        result_latex = ""
        result_plain = ""
        message = ""
        steps: List[Dict[str, str]] = []
        derivative_evaluation = None
        a_expr = None
        b_expr = None
        bounds_payload: List[Dict[str, Optional[str]]] = []
        response_variables: List[str] = []
        response_expression_plain: Optional[str] = None
        response_expression_latex: Optional[str] = None
        display_latex = ""
        approximate = None
        response_definite = False
        ode_solution = None

        if operation in ("derivar", "derivada", "derivative", "diff"):
            variable = req.variable.strip() or "x"
            x = sp.Symbol(variable)
            expr = _parse_symbolic_expression(expression_text, variable)
            steps, result = _derivative_steps(expr, x, req.order)
            operation_label = "Derivada"
            result_latex = sp.latex(result)
            result_plain = _format_plain(result)
            message = f"{operation_label} final: {result_plain}"
            response_variables = [variable]
            display_latex = _derivative_display_latex(expr, x, req.order, result)
            response_definite = False

            if req.eval_at and str(req.eval_at).strip():
                point_text = str(req.eval_at).strip()
                if "=" in point_text and point_text.split("=", 1)[0].strip() == variable:
                    point_text = point_text.split("=", 1)[1].strip()

                point_expr = _parse_symbolic_expression(point_text, variable)
                if point_expr.free_symbols:
                    raise ValueError("El punto de evaluacion debe ser un valor numerico, por ejemplo 2 o pi/4.")

                evaluated = sp.simplify(result.subs(x, point_expr))
                derivative_evaluation = {
                    "point": _format_plain(point_expr),
                    "point_latex": sp.latex(point_expr),
                    "value": _format_plain(evaluated),
                    "value_latex": sp.latex(evaluated),
                    "approximate": _format_numeric(evaluated),
                }
                message += (
                    f"\nEvaluacion en {variable} = {_format_plain(point_expr)}: "
                    f"{_format_plain(evaluated)}"
                )
        elif operation in ("integrar", "integral", "integrate"):
            integral_mode = req.integral_mode.strip().lower() if req.integral_mode else "simple"

            if integral_mode == "double":
                response_variables = _normalize_variable_names(req.double_variables or ["x", "y"])
                if len(response_variables) != 2:
                    raise ValueError("La integral doble necesita exactamente dos variables de integración.")

                expr = _parse_symbolic_expression(expression_text, response_variables)
                lower_bounds = list(req.double_lower_bounds or [])
                upper_bounds = list(req.double_upper_bounds or [])
                if len(lower_bounds) != 2 or len(upper_bounds) != 2:
                    raise ValueError("Ingresá los dos límites inferiores y superiores para la integral doble.")

                specs: List[Dict[str, Any]] = []
                for variable_name, lower_text, upper_text in zip(response_variables, lower_bounds, upper_bounds):
                    lower_value = str(lower_text).strip()
                    upper_value = str(upper_text).strip()
                    if not lower_value or not upper_value:
                        raise ValueError("Todos los límites de la integral doble deben estar completos.")

                    lower_expr = _parse_symbolic_expression(lower_value, response_variables)
                    upper_expr = _parse_symbolic_expression(upper_value, response_variables)
                    specs.append({
                        "variable": variable_name,
                        "symbol": sp.Symbol(variable_name),
                        "lower": lower_expr,
                        "upper": upper_expr,
                    })

                _validate_iterated_bounds(specs)
                steps, result = _iterated_integral_steps(expr, specs)
                operation_label = "Integral doble"
                result_latex = sp.latex(result)
                result_plain = _format_plain(result)
                message = f"{operation_label} final: {result_plain}"
                display_latex = rf"{_iterated_integral_operator(expr, specs)} = {sp.latex(result)}"
                bounds_payload = [
                    {
                        "variable": spec["variable"],
                        "lower_latex": sp.latex(spec["lower"]),
                        "upper_latex": sp.latex(spec["upper"]),
                    }
                    for spec in specs
                ]
                variable = response_variables[0]
                approximate = _format_numeric(result)
                response_definite = True
            else:
                variable = req.variable.strip() or "x"
                x = sp.Symbol(variable)
                expr = _parse_symbolic_expression(expression_text, variable)
                a_expr = _parse_symbolic_expression(req.a, variable) if req.a else None
                b_expr = _parse_symbolic_expression(req.b, variable) if req.b else None
                steps, result = _integral_steps(expr, x, req.definite, a_expr, b_expr)
                operation_label = "Integral definida" if req.definite else "Integral indefinida"
                result_latex = sp.latex(result) if req.definite else rf"{sp.latex(result)} + C"
                result_plain = _format_plain(result) if req.definite else f"{_format_plain(result)} + C"
                message = f"{operation_label} final: {result_plain}"
                response_variables = [variable]
                display_latex = _single_integral_display_latex(expr, x, result, req.definite, a_expr, b_expr)
                bounds_payload = (
                    [
                        {
                            "variable": variable,
                            "lower_latex": sp.latex(a_expr) if a_expr is not None else None,
                            "upper_latex": sp.latex(b_expr) if b_expr is not None else None,
                        }
                    ]
                    if req.definite
                    else []
                )
                approximate = _format_numeric(result) if req.definite else None
                response_definite = req.definite
        elif operation in ("edo", "ode", "ecuacion_diferencial", "differential"):
            variable_names = _normalize_variable_names([
                req.variable.strip() or "x",
                req.dependent_variable.strip() or "y",
            ])
            variable, dependent_variable = variable_names
            x = sp.Symbol(variable)
            y = sp.Symbol(dependent_variable)
            response_variables = [variable, dependent_variable]
            ode_mode = req.ode_mode.strip().lower() if req.ode_mode else "linear"

            if ode_mode in ("separable", "separables", "variables_separables"):
                equation_text = _required_expression(req.ode_equation or expression_text, "la ecuacion diferencial")
                rhs_expr, standard_latex = _parse_first_order_derivative_equation(
                    equation_text,
                    variable,
                    dependent_variable,
                )
                if req.initial_condition and str(req.initial_condition).strip():
                    x0, y0 = _parse_initial_condition_text(req.initial_condition, variable, dependent_variable)
                else:
                    x0, y0 = _parse_initial_pair(req.initial_x, req.initial_y, variable, dependent_variable, [variable, dependent_variable])
                interval_info = _parse_interval_expression(req.interval_expression, variable)

                solution_data = _separable_ode_solution(rhs_expr, standard_latex, x, y, x0, y0, interval_info)
                steps = solution_data["steps"]
                display_latex = solution_data["display_latex"]
                result_plain = solution_data["result"]
                result_latex = solution_data["result_latex"]
                message = solution_data["message"]
                ode_solution = solution_data["ode_solution"]
                operation_label = "EDO separable"
                expr = rhs_expr
                response_expression_latex = ode_solution["equation_latex"]
                response_expression_plain = f"d{dependent_variable}/d{variable} = {_format_plain(rhs_expr)}"
                response_definite = False
            elif ode_mode in ("equation", "ecuacion", "direct", "directa"):
                equation_text = _required_expression(req.ode_equation or expression_text, "la ecuacion diferencial")
                p_expr, q_expr, standard_latex = _parse_linear_ode_equation(equation_text, variable, dependent_variable)
                if req.initial_condition and str(req.initial_condition).strip():
                    x0, y0 = _parse_initial_condition_text(req.initial_condition, variable, dependent_variable)
                else:
                    x0, y0 = _parse_initial_pair(req.initial_x, req.initial_y, variable, dependent_variable, variable)
                interval_info = _parse_interval_expression(req.interval_expression, variable)

                solution_data = _linear_ode_solution(p_expr, q_expr, x, y, x0, y0, interval_info)
                steps = solution_data["steps"]
                steps.insert(
                    0,
                    _step(
                        "Ecuacion ingresada",
                        "Se interpreta la ecuacion y se lleva a la forma lineal estandar.",
                        standard_latex,
                    ),
                )
                display_latex = solution_data["display_latex"]
                result_plain = solution_data["result"]
                result_latex = solution_data["result_latex"]
                message = solution_data["message"]
                ode_solution = solution_data["ode_solution"]
                operation_label = "EDO lineal"
                expr = q_expr
                response_expression_latex = ode_solution["equation_latex"]
                response_expression_plain = (
                    f"d{dependent_variable}/d{variable} = {_format_plain(q_expr)}"
                    if sp.simplify(p_expr) == 0
                    else f"d{dependent_variable}/d{variable} + ({_format_plain(p_expr)}){dependent_variable} = {_format_plain(q_expr)}"
                )
                response_definite = False
            elif ode_mode in ("linear", "lineal", "pq", "p_q"):
                p_text = _required_expression(req.p_expression, "P(x)")
                q_text = _required_expression(req.q_expression, "Q(x)")
                p_expr = _parse_symbolic_expression(p_text, variable)
                q_expr = _parse_symbolic_expression(q_text, variable)
                allowed_symbols = {x}
                invalid_symbols = (p_expr.free_symbols | q_expr.free_symbols) - allowed_symbols
                if invalid_symbols:
                    invalid_names = ", ".join(sorted(sp.sstr(symbol) for symbol in invalid_symbols))
                    raise ValueError(f"P(x) y Q(x) solo pueden depender de {variable}; se encontro {invalid_names}.")

                x0, y0 = _parse_initial_pair(req.initial_x, req.initial_y, variable, dependent_variable, variable)
                solution_data = _linear_ode_solution(p_expr, q_expr, x, y, x0, y0)
                steps = solution_data["steps"]
                display_latex = solution_data["display_latex"]
                result_plain = solution_data["result"]
                result_latex = solution_data["result_latex"]
                message = solution_data["message"]
                ode_solution = solution_data["ode_solution"]
                operation_label = "EDO lineal"
                expr = p_expr
                response_expression_latex = ode_solution["equation_latex"]
                response_expression_plain = (
                    f"d{dependent_variable}/d{variable} = {_format_plain(q_expr)}"
                    if sp.simplify(p_expr) == 0
                    else f"d{dependent_variable}/d{variable} + ({_format_plain(p_expr)}){dependent_variable} = {_format_plain(q_expr)}"
                )
                response_definite = False
            elif ode_mode in ("exact", "exacta"):
                m_text = _required_expression(req.m_expression, "M(x,y)")
                n_text = _required_expression(req.n_expression, "N(x,y)")
                variables = [variable, dependent_variable]
                m_expr = _parse_symbolic_expression(m_text, variables)
                n_expr = _parse_symbolic_expression(n_text, variables)
                allowed_symbols = {x, y}
                invalid_symbols = (m_expr.free_symbols | n_expr.free_symbols) - allowed_symbols
                if invalid_symbols:
                    invalid_names = ", ".join(sorted(sp.sstr(symbol) for symbol in invalid_symbols))
                    raise ValueError(
                        f"M(x,y) y N(x,y) solo pueden depender de {variable} y {dependent_variable}; se encontro {invalid_names}."
                    )

                x0, y0 = _parse_initial_pair(req.initial_x, req.initial_y, variable, dependent_variable, variables)
                solution_data = _exact_ode_solution(m_expr, n_expr, x, y, x0, y0)
                steps = solution_data["steps"]
                display_latex = solution_data["display_latex"]
                result_plain = solution_data["result"]
                result_latex = solution_data["result_latex"]
                message = solution_data["message"]
                ode_solution = solution_data["ode_solution"]
                operation_label = "EDO exacta"
                expr = m_expr
                response_expression_latex = ode_solution["equation_latex"]
                response_expression_plain = (
                    f"({_format_plain(m_expr)}) d{variable} + ({_format_plain(n_expr)}) d{dependent_variable} = 0"
                )
                response_definite = False
            else:
                raise ValueError("Modo de EDO no reconocido. Usa lineal, separable o exacta.")
        else:
            raise ValueError("Operacion no reconocida. Usa 'derivar', 'integrar' o 'edo'.")

        return {
            "operation": operation_label,
            "expression": response_expression_plain or _format_plain(expr),
            "expression_latex": response_expression_latex or sp.latex(expr),
            "variable": variable,
            "variables": response_variables,
            "order": req.order,
            "definite": response_definite,
            "lower_latex": sp.latex(a_expr) if a_expr is not None else None,
            "upper_latex": sp.latex(b_expr) if b_expr is not None else None,
            "bounds": bounds_payload,
            "display_latex": display_latex,
            "result": result_plain,
            "result_latex": result_latex,
            "approximate": approximate,
            "derivative_evaluation": derivative_evaluation,
            "ode_solution": ode_solution,
            "steps": steps,
            "message": message,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/polynomial")
def calculate_polynomial(req: PolynomialRequest):
    """Expand, factor, collect and simplify polynomial-like expressions."""
    try:
        variable = req.variable.strip() or "x"
        if not re.match(r"^[A-Za-z_]\w*$", variable):
            raise ValueError(f"Variable inválida '{variable}'")

        x = sp.Symbol(variable)
        original_expr = _parse_symbolic_expression(req.expression, variable)
        expr = sp.nsimplify(original_expr, rational=True)

        simplified = sp.simplify(expr)
        expanded = sp.expand(expr)
        collected = sp.collect(expanded, x)
        factored = sp.factor(simplified)
        cancelled = sp.cancel(simplified)

        forms = {
            "simplified": _polynomial_form("Simplificada", simplified),
            "expanded": _polynomial_form("Expandida", expanded),
            "collected": _polynomial_form("Agrupada por potencias", collected),
            "factored": _polynomial_form("Factorizada", factored),
            "cancelled": _polynomial_form("Racional simplificada", cancelled),
        }

        operation = req.operation.strip().lower()
        operation_map = {
            "expand": ("Expandir distributiva", expanded),
            "expandir": ("Expandir distributiva", expanded),
            "distributiva": ("Expandir distributiva", expanded),
            "factor": ("Factorizar", factored),
            "factorizar": ("Factorizar", factored),
            "collect": ("Agrupar", collected),
            "agrupar": ("Agrupar", collected),
            "simplify": ("Simplificar", simplified),
            "simplificar": ("Simplificar", simplified),
            "all": ("Todas las formas", simplified),
            "todo": ("Todas las formas", simplified),
        }
        if operation not in operation_map:
            raise ValueError("Operación no reconocida. Usá expandir, factorizar, agrupar o simplificar.")

        operation_label, final_expr = operation_map[operation]
        degree = None
        coefficients: List[Dict[str, Any]] = []
        is_polynomial = True
        polynomial_error = None

        try:
            poly = sp.Poly(expanded, x)
            degree = int(poly.degree())
            coefficients = _make_polynomial_coefficients(poly, x)
        except Exception as exc:
            is_polynomial = False
            polynomial_error = f"No se pudo leer como polinomio en {variable}: {exc}"

        return {
            "operation": operation_label,
            "expression": _format_symbolic(expr),
            "expression_latex": sp.latex(expr),
            "variable": variable,
            "exact": True,
            "is_polynomial": is_polynomial,
            "polynomial_error": polynomial_error,
            "degree": degree,
            "final": _format_symbolic(final_expr),
            "final_latex": sp.latex(final_expr),
            "forms": forms,
            "coefficients": coefficients,
            "steps": _polynomial_steps(
                original_expr,
                expr,
                expanded,
                collected,
                factored,
                simplified,
                True,
            ),
            "message": f"{operation_label}: {_format_symbolic(final_expr)}",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/solve")
def solve(req: SolveRequest):
    if req.method not in REGISTRY:
        raise HTTPException(status_code=400, detail=f"Método '{req.method}' no reconocido")

    info = REGISTRY[req.method]
    requiere = info["requiere"]
    opcionales = info.get("opcionales", [])
    resolver = info["resolver"]
    root_col = info["root_col"]
    uses_raw_expression = info.get("uses_raw_expression", False)

    try:
        kwargs = {"max_iter": req.max_iter, "tol": req.tol, "precision": req.precision}
        plot_span = 50
        parsed_a = parse_scalar_value(req.a, "a")
        parsed_b = parse_scalar_value(req.b, "b")
        parsed_e = parse_scalar_value(req.e, "e")
        parsed_x0 = parse_scalar_value(req.x0, "x0")
        parsed_y0 = parse_scalar_value(req.y0, "y0")
        parsed_h = parse_scalar_value(req.h, "h")

        if "x_data" in requiere or "x_data" in opcionales:
            if req.x_data:
                kwargs["x_data"] = [eval_math_expr(x.strip()) for x in req.x_data.split(",") if x.strip()]
        if "y_data" in requiere or "y_data" in opcionales:
            if req.y_data:
                kwargs["y_data"] = [eval_math_expr(y.strip()) for y in req.y_data.split(",") if y.strip()]
        if "variables" in requiere or "variables" in opcionales:
            kwargs["variables"] = req.variables
        if "bounds" in requiere or "bounds" in opcionales:
            kwargs["bounds"] = req.bounds
        if "seed" in requiere or "seed" in opcionales:
            kwargs["seed"] = req.seed
        if "confidence_level" in requiere or "confidence_level" in opcionales:
            kwargs["confidence_level"] = req.confidence_level
        if "y0" in requiere or "y0" in opcionales:
            if parsed_y0 is not None:
                kwargs["y0"] = parsed_y0
        if "e" in requiere or "e" in opcionales:
            if parsed_e is not None:
                kwargs["e"] = parsed_e
        if "x0" in opcionales and parsed_x0 is not None and (
            ("a" in requiere and "b" in requiere) or ("a" in opcionales and "b" in opcionales)
        ):
            kwargs["x0"] = parsed_x0
        if "h" in requiere or "h" in opcionales:
            if parsed_h is not None:
                kwargs["h"] = parsed_h
        if "exact_expr" in requiere or "exact_expr" in opcionales:
            if req.exact_expr:
                kwargs["exact_expr_str"] = req.exact_expr
        if "n" in requiere or "n" in opcionales:
            if req.n is not None:
                try:
                    kwargs["n"] = int(str(req.n).strip())
                except Exception as exc:
                    raise ValueError(f"No se pudo interpretar n='{req.n}' como entero.") from exc

        plot_fn = None
        fn = None
        f_fn = None
        
        if "g_expr" in requiere or "g_expr" in opcionales:
            if req.g_expr:
                fn = parse_function(req.g_expr)
        if "f_expr" in requiere or "f_expr" in opcionales:
            if req.f_expr:
                if uses_raw_expression:
                    kwargs["f_expr_str"] = req.f_expr
                else:
                    f_fn = parse_function(req.f_expr)
                    if ("g_expr" not in requiere) and ("g_expr" not in opcionales):
                        fn = f_fn
                    plot_fn = f_fn

        # Only pass string expressions to methods that explicitly support/need them
        if req.method in ["lagrange", "newton_dif_div"]:
            if req.f_expr:
                kwargs["f_expr_str"] = req.f_expr
            if req.g_expr:
                kwargs["g_expr_str"] = req.g_expr

        if plot_fn is None:
            plot_fn = fn

        if ("a" in requiere and "b" in requiere) or ("a" in opcionales and "b" in opcionales):
            if parsed_a is not None and parsed_b is not None:
                res = resolver(fn, parsed_a, parsed_b, **kwargs)
                plot_center = (parsed_a + parsed_b) / 2
                plot_span = max(abs(parsed_b - parsed_a) * 1.5, 5)
            else:
                res = resolver(fn, **kwargs)
                plot_center = 0
        elif ("x0" in requiere or "x0" in opcionales) and "x_data" not in requiere:
            if parsed_x0 is not None:
                res = resolver(fn, parsed_x0, **kwargs)
                plot_center = parsed_x0
            else:
                res = resolver(fn, **kwargs)
                plot_center = 0
        else:
            if ("x0" in requiere or "x0" in opcionales) and parsed_x0 is not None:
                try:
                    kwargs["x0"] = parsed_x0
                except Exception:
                    pass
            res = resolver(fn, **kwargs)
            if "x_data" in kwargs and kwargs["x_data"]:
                # Centrar gráfico usando x_data para interpolación
                min_x = min(kwargs["x_data"])
                max_x = max(kwargs["x_data"])
                plot_center = (min_x + max_x) / 2
                plot_span = max((max_x - min_x) * 1.5, 5)
            else:
                plot_center = 0

        # Unpack response from resolver
        headers = info["headers"]
        plot_secondary = None
        plot_bases = []
        latex_str = None
        latex_decimal_str = None
        bases_latex = None
        errores_latex = None
        
        # Determine the shape of res
        if isinstance(res, tuple):
            if len(res) >= 9: # iteraciones, mensaje, poly, bases, headers, latex, bases_latex, errores_latex, latex_decimal
                iterations, message, poly_expr, bases_expr, dynamic_headers, latex_str, bases_latex, errores_latex, latex_decimal_str = res
                if dynamic_headers:
                    headers = dynamic_headers
            elif len(res) == 8: # iteraciones, mensaje, poly, bases, headers, latex, bases_latex, errores_latex
                iterations, message, poly_expr, bases_expr, dynamic_headers, latex_str, bases_latex, errores_latex = res
                if dynamic_headers:
                    headers = dynamic_headers
            elif len(res) == 7: # iteraciones, mensaje, poly, bases, headers, latex, bases_latex
                iterations, message, poly_expr, bases_expr, dynamic_headers, latex_str, bases_latex = res
                if dynamic_headers:
                    headers = dynamic_headers
            elif len(res) == 6: # iteraciones, mensaje, poly, bases, headers, latex
                iterations, message, poly_expr, bases_expr, dynamic_headers, latex_str = res
                if dynamic_headers:
                    headers = dynamic_headers
            elif len(res) == 5: # iteraciones, mensaje, poly, bases, headers
                iterations, message, poly_expr, bases_expr, dynamic_headers = res
                if dynamic_headers:
                    headers = dynamic_headers
            elif len(res) == 4: # iteraciones, mensaje, poly, bases
                iterations, message, poly_expr, bases_expr = res
            elif len(res) == 3: # iteraciones, mensaje, poly
                iterations, message, poly_expr = res
                bases_expr = None
            else:
                iterations, message = res
                poly_expr = None
                bases_expr = None
                
            if poly_expr is not None:
                poly_fn = parse_function(poly_expr)
                # Adjust span to encompass all nodes plus margin
                span = plot_span
                if "x_data" in kwargs and kwargs["x_data"]:
                    min_x = min(kwargs["x_data"])
                    max_x = max(kwargs["x_data"])
                    span = max((max_x - min_x) * 1.5, 5) # Set span based on node spread
                x_plot2, y_plot2 = generate_plot_data(poly_fn, center=plot_center, span=span)
                plot_secondary = {"x": x_plot2, "y": y_plot2, "label": "P(x)"}
                
            if bases_expr:
                span = plot_span
                if "x_data" in kwargs and kwargs["x_data"]:
                    min_x = min(kwargs["x_data"])
                    max_x = max(kwargs["x_data"])
                    span = max((max_x - min_x) * 1.5, 5)
                for i, base_str in enumerate(bases_expr):
                    try:
                        base_fn = parse_function(base_str)
                        x_base, y_base = generate_plot_data(base_fn, center=plot_center, span=span)
                        plot_bases.append({"x": x_base, "y": y_base, "label": f"L_{i}(x)"})
                    except Exception:
                        pass
        else:
            iterations, message = res

        nodes = None
        if "x_data" in kwargs and "y_data" in kwargs:
            nodes = [{"x": x, "y": y} for x, y in zip(kwargs["x_data"], kwargs["y_data"])]

        x_plot, y_plot = [], []
        if plot_fn is not None:
            span = plot_span
            if "x_data" in kwargs and kwargs["x_data"]:
                min_x = min(kwargs["x_data"])
                max_x = max(kwargs["x_data"])
                span = max((max_x - min_x) * 1.5, 5)
            x_plot, y_plot = generate_plot_data(plot_fn, center=plot_center, span=span)

        root = None
        if iterations and root_col is not None:
            last_row = iterations[-1]
            if isinstance(last_row, dict) and root_col in last_row:
                root = last_row[root_col]
            elif isinstance(last_row, list) and isinstance(root_col, int) and root_col < len(last_row):
                root = last_row[root_col]

        root_y = None
        if root is not None and plot_fn is not None:
            try:
                root_y = float(plot_fn(root))
                if not np.isfinite(root_y):
                    root_y = 0
            except Exception:
                root_y = 0

        is_fx = "f_expr" in requiere or "f_expr" in opcionales

        method_class = info.get("clase", "")
        is_newton_cotes = "Newton-Cotes" in method_class
        plot_window = None
        integration_window = None

        def _make_bounds_window(a_val: float, b_val: float, margin_ratio: float = 0.15, min_margin: float = 0.5):
            lo = min(a_val, b_val)
            hi = max(a_val, b_val)
            span = max(hi - lo, 1e-9)
            margin = max(span * margin_ratio, min_margin)
            return {"x_min": lo - margin, "x_max": hi + margin}

        def _make_center_window(center_val: float, half_width: float = 10.0):
            return {"x_min": center_val - half_width, "x_max": center_val + half_width}

        if is_newton_cotes and parsed_a is not None and parsed_b is not None:
            integration_window = {
                "x_min": min(parsed_a, parsed_b),
                "x_max": max(parsed_a, parsed_b),
            }
            plot_window = _make_bounds_window(parsed_a, parsed_b, margin_ratio=0.15, min_margin=0.5)
        elif "x_data" in kwargs and kwargs["x_data"]:
            xs = kwargs["x_data"]
            min_x = min(xs)
            max_x = max(xs)
            span = max(max_x - min_x, 1e-9)
            margin = max(span * 0.1, 0.2)
            plot_window = {"x_min": min_x - margin, "x_max": max_x + margin}
        elif parsed_a is not None and parsed_b is not None:
            plot_window = _make_bounds_window(parsed_a, parsed_b, margin_ratio=0.15, min_margin=0.5)
        else:
            center_val = None
            if root is not None and math.isfinite(root):
                center_val = root
            elif parsed_x0 is not None and math.isfinite(parsed_x0):
                center_val = parsed_x0
            if center_val is not None:
                plot_window = _make_center_window(center_val, half_width=10.0)

        # Preformatear mensaje conservando saltos de linea
        message = message.replace('\n', '\n')

        return {
            "headers": headers,
            "iterations": iterations,
            "message": message,
            "latex_str": latex_str,
            "latex_decimal_str": latex_decimal_str,
            "bases_latex": bases_latex,
            "errores_latex": errores_latex,
            "plot": {"x": x_plot, "y": y_plot, "center": plot_center} if (plot_fn and len(x_plot) > 0) else None,
            "plot_secondary": plot_secondary,
            "plot_bases": plot_bases if len(plot_bases) > 0 else None,
            "nodes": nodes,
            "root": {"x": root, "y": root_y} if root is not None else None,
            "is_fx": is_fx,
            "plot_window": plot_window,
            "integration_window": integration_window,
            "is_newton_cotes": is_newton_cotes,
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
