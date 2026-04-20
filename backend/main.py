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
    a: Optional[str] = None
    b: Optional[str] = None
    x0: Optional[str] = None
    n: Optional[str] = None
    max_iter: int = 100
    tol: float = 1e-6
    precision: int = 8


class CalculusRequest(BaseModel):
    operation: str = Field(..., description="derivar o integrar")
    expression: str = Field(..., min_length=1)
    variable: str = "x"
    order: int = Field(1, ge=1, le=6)
    definite: bool = False
    a: Optional[str] = None
    b: Optional[str] = None


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
    text = re.sub(r'\be\b', 'E', text)
    text = re.sub(r'\bx(\d+)\b', r'x**\1', text)
    return text


def _parse_symbolic_expression(expr_str: str, variable: str = "x") -> sp.Expr:
    normalized = _normalize_expression(expr_str)
    if not re.match(r"^[A-Za-z_]\w*$", variable):
        raise ValueError(f"Variable inválida '{variable}'")

    symbol = sp.Symbol(variable)
    local_dict = {
        variable: symbol,
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
        "abs": sp.Abs,
    }
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


def _is_constant(expr: sp.Expr, x: sp.Symbol) -> bool:
    return not expr.has(x)


def _format_plain(expr: sp.Expr) -> str:
    text = str(sp.sstr(sp.simplify(expr)))
    return re.sub(r"(?<=\d)\*(?=[A-Za-z_])", "", text)


def _extract_inline_calculus_command(operation: str, expression: str) -> tuple[str, str]:
    text = expression.strip()
    lower_text = text.lower()
    commands = {
        "derivar": "derivar",
        "derivada": "derivar",
        "integrar": "integrar",
        "integral": "integrar",
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
        }
    return methods


@app.post("/api/calculus")
def calculate_symbolic(req: CalculusRequest):
    """Calculate symbolic derivatives and integrals with explanatory steps."""
    try:
        operation = req.operation.strip().lower()
        variable = req.variable.strip() or "x"
        x = sp.Symbol(variable)
        operation, expression_text = _extract_inline_calculus_command(operation, req.expression)
        if not expression_text:
            raise ValueError("Ingresá una expresión para calcular.")
        expr = _parse_symbolic_expression(expression_text, variable)
        a_expr = None
        b_expr = None

        if operation in ("derivar", "derivada", "derivative", "diff"):
            steps, result = _derivative_steps(expr, x, req.order)
            operation_label = "Derivada"
            result_latex = sp.latex(result)
            result_plain = _format_plain(result)
            message = f"{operation_label} final: {result_plain}"
        elif operation in ("integrar", "integral", "integrate"):
            a_expr = _parse_symbolic_expression(req.a, variable) if req.a else None
            b_expr = _parse_symbolic_expression(req.b, variable) if req.b else None
            steps, result = _integral_steps(expr, x, req.definite, a_expr, b_expr)
            operation_label = "Integral definida" if req.definite else "Integral indefinida"
            result_latex = sp.latex(result) if req.definite else rf"{sp.latex(result)} + C"
            result_plain = _format_plain(result) if req.definite else f"{_format_plain(result)} + C"
            message = f"{operation_label} final: {result_plain}"
        else:
            raise ValueError("Operación no reconocida. Usá 'derivar' o 'integrar'.")

        approximate = None
        if operation in ("integrar", "integral", "integrate") and req.definite:
            approximate = float(sp.N(result))

        return {
            "operation": operation_label,
            "expression": _format_plain(expr),
            "expression_latex": sp.latex(expr),
            "variable": variable,
            "order": req.order,
            "definite": req.definite,
            "lower_latex": sp.latex(a_expr) if a_expr is not None else None,
            "upper_latex": sp.latex(b_expr) if b_expr is not None else None,
            "result": result_plain,
            "result_latex": result_latex,
            "approximate": approximate,
            "steps": steps,
            "message": message,
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

    try:
        kwargs = {"max_iter": req.max_iter, "tol": req.tol, "precision": req.precision}
        plot_span = 50
        parsed_a = parse_scalar_value(req.a, "a")
        parsed_b = parse_scalar_value(req.b, "b")
        parsed_x0 = parse_scalar_value(req.x0, "x0")

        if "x_data" in requiere or "x_data" in opcionales:
            if req.x_data:
                kwargs["x_data"] = [eval_math_expr(x.strip()) for x in req.x_data.split(",") if x.strip()]
        if "y_data" in requiere or "y_data" in opcionales:
            if req.y_data:
                kwargs["y_data"] = [eval_math_expr(y.strip()) for y in req.y_data.split(",") if y.strip()]
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
        bases_latex = None
        errores_latex = None
        
        # Determine the shape of res
        if isinstance(res, tuple):
            if len(res) >= 8: # iteraciones, mensaje, poly, bases, headers, latex, bases_latex, errores_latex
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

        # Preformatear mensaje conservando saltos de linea
        message = message.replace('\n', '\n')

        return {
            "headers": headers,
            "iterations": iterations,
            "message": message,
            "latex_str": latex_str,
            "bases_latex": bases_latex,
            "errores_latex": errores_latex,
            "plot": {"x": x_plot, "y": y_plot, "center": plot_center} if (plot_fn and len(x_plot) > 0) else None,
            "plot_secondary": plot_secondary,
            "plot_bases": plot_bases if len(plot_bases) > 0 else None,
            "nodes": nodes,
            "root": {"x": root, "y": root_y} if root is not None else None,
            "is_fx": is_fx,
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
