from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import numpy as np
import sympy as sp
import math

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
    a: Optional[float] = None
    b: Optional[float] = None
    x0: Optional[float] = None
    max_iter: int = 100
    tol: float = 1e-6
    precision: int = 8

def eval_math_expr(expr_str: str) -> float:
    """Safely evaluates a single math expression to a float."""
    import re
    expr_str = re.sub(r'\be\b', 'E', expr_str)
    try:
        val = sp.sympify(expr_str).evalf()
        return float(val)
    except Exception as e:
        raise ValueError(f"Could not evaluate '{expr_str}': {str(e)}")

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
    
    # Reemplazar e por E SOLO si 'e' está solo (para el número de Euler).
    # Si hacemos un replace simple de 'e', convertimos 'exp' en 'Exp', lo cual rompe Sympy.
    import re
    expr_str = re.sub(r'\be\b', 'E', expr_str)
    
    try:
        # Parse expression safely
        x = sp.Symbol('x')
        # We use standard transformations to allow implicit multiplication if needed,
        # but standard sympify is usually enough for well-formed math strings.
        expr = sp.sympify(expr_str)
        
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
            "headers": info["headers"],
        }
    return methods

@app.post("/api/solve")
def solve(req: SolveRequest):
    if req.method not in REGISTRY:
        raise HTTPException(status_code=400, detail=f"Método '{req.method}' no reconocido")

    info = REGISTRY[req.method]
    requiere = info["requiere"]
    resolver = info["resolver"]
    root_col = info["root_col"]

    try:
        kwargs = {"max_iter": req.max_iter, "tol": req.tol, "precision": req.precision}

        if "x_data" in requiere:
            kwargs["x_data"] = [eval_math_expr(x.strip()) for x in req.x_data.split(",") if x.strip()]
        if "y_data" in requiere:
            kwargs["y_data"] = [eval_math_expr(y.strip()) for y in req.y_data.split(",") if y.strip()]

        plot_fn = None
        fn = None
        f_fn = None
        
        if "g_expr" in requiere:
            fn = parse_function(req.g_expr)
        if "f_expr" in requiere:
            f_fn = parse_function(req.f_expr)
            if "g_expr" not in requiere:
                fn = f_fn
            plot_fn = f_fn

        if plot_fn is None:
            plot_fn = fn

        if "a" in requiere and "b" in requiere:
            if req.a is None or req.b is None:
                raise ValueError("Parameters 'a' and 'b' are required")
            res = resolver(fn, float(req.a), float(req.b), **kwargs)
            plot_center = (req.a + req.b) / 2
        elif "x0" in requiere and "x_data" not in requiere:
            if req.x0 is None:
                raise ValueError("Parameter 'x0' is required")
            res = resolver(fn, float(req.x0), **kwargs)
            plot_center = req.x0
        else:
            if "x0" in requiere and req.x0 is not None:
                kwargs["x0"] = float(req.x0)
            res = resolver(fn, **kwargs)
            if "x_data" in kwargs and kwargs["x_data"]:
                plot_center = sum(kwargs["x_data"]) / len(kwargs["x_data"])
            else:
                plot_center = 0

        plot_secondary = None
        if isinstance(res, tuple) and len(res) == 3:
            iterations, message, poly_expr = res
            poly_fn = parse_function(poly_expr)
            x_plot2, y_plot2 = generate_plot_data(poly_fn, center=plot_center)
            plot_secondary = {"x": x_plot2, "y": y_plot2, "label": "P(x)"}
        else:
            iterations, message = res

        nodes = None
        if "x_data" in kwargs and "y_data" in kwargs:
            nodes = [{"x": x, "y": y} for x, y in zip(kwargs["x_data"], kwargs["y_data"])]

        x_plot, y_plot = [], []
        if plot_fn is not None:
            x_plot, y_plot = generate_plot_data(plot_fn, center=plot_center)

        root = None
        if iterations and root_col and root_col in iterations[-1]:
            root = iterations[-1][root_col]

        root_y = None
        if root is not None and plot_fn is not None:
            try:
                root_y = float(plot_fn(root))
                if not np.isfinite(root_y):
                    root_y = 0
            except Exception:
                root_y = 0

        is_fx = "f_expr" in requiere

        return {
            "headers": info["headers"],
            "iterations": iterations,
            "message": message,
            "plot": {"x": x_plot, "y": y_plot, "center": plot_center} if plot_fn else None,
            "plot_secondary": plot_secondary,
            "nodes": nodes,
            "root": {"x": root, "y": root_y} if root is not None else None,
            "is_fx": is_fx,
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
