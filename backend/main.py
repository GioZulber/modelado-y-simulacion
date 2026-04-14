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


def _parse_symbolic_expression(expr_str: str) -> sp.Expr:
    normalized = _normalize_expression(expr_str)
    x = sp.Symbol('x')
    try:
        return parse_expr(normalized, transformations=_PARSER_TRANSFORMATIONS, local_dict={"x": x}, evaluate=True)
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
