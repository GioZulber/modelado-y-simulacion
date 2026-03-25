from flask import Flask, render_template, request, jsonify
import numpy as np

from metodos import REGISTRY

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Safe math expression evaluator
# ---------------------------------------------------------------------------

SAFE_NAMESPACE = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "pi": np.pi,
    "e": np.e,
    "asin": np.arcsin,
    "acos": np.arccos,
    "atan": np.arctan,
    "nroot": lambda x, n: x ** (1 / n),
}


def parse_function(expr: str):
    """Return a callable f(x) from a math expression string."""
    def fn(x):
        namespace = {**SAFE_NAMESPACE, "x": x}
        return eval(expr, {"__builtins__": {}}, namespace)
    return fn


# ---------------------------------------------------------------------------
# Plot data helper
# ---------------------------------------------------------------------------

def generate_plot_data(fn, center=0, span=50, n=2000):
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

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/methods", methods=["GET"])
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
    return jsonify(methods)


@app.route("/api/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)
    method_key = data.get("method", "")
    f_expr = data.get("f_expr", "")
    g_expr = data.get("g_expr", "")
    a = data.get("a")
    b = data.get("b")
    x0 = data.get("x0")
    max_iter = int(data.get("max_iter", 100))
    tol = float(data.get("tol", 1e-6))
    precision = int(data.get("precision", 8))

    if method_key not in REGISTRY:
        return jsonify({"error": f"Método '{method_key}' no reconocido"}), 400

    info = REGISTRY[method_key]
    requiere = info["requiere"]
    resolver = info["resolver"]
    root_col = info["root_col"]

    try:
        # Build arguments based on what the method requires
        kwargs = {"max_iter": max_iter, "tol": tol, "precision": precision}

        # Parse functions: g_expr is used for solving, f_expr for plotting
        plot_fn = None
        if "g_expr" in requiere:
            fn = parse_function(g_expr)
        if "f_expr" in requiere:
            f_fn = parse_function(f_expr)
            if "g_expr" not in requiere:
                fn = f_fn  # f(x)-only methods (biseccion, newton)
            plot_fn = f_fn  # always plot f(x) when available

        if plot_fn is None:
            plot_fn = fn

        # Determine positional args based on requirements
        if "a" in requiere and "b" in requiere:
            a_val, b_val = float(a), float(b)
            iterations, message = resolver(fn, a_val, b_val, **kwargs)
            plot_center = (a_val + b_val) / 2
        elif "x0" in requiere:
            x0_val = float(x0)
            iterations, message = resolver(fn, x0_val, **kwargs)
            plot_center = x0_val
        else:
            iterations, message = resolver(fn, **kwargs)
            plot_center = 0

        # Generate plot data
        x_plot, y_plot = generate_plot_data(plot_fn, center=plot_center)

        # Find root/fixed point for marking on plot
        root = None
        if iterations:
            root = iterations[-1][root_col]

        root_y = None
        if root is not None:
            try:
                root_y = float(plot_fn(root))
                if not np.isfinite(root_y):
                    root_y = 0
            except Exception:
                root_y = 0

        # Plot f(x) with y=0 line whenever f_expr is available
        is_fx = "f_expr" in requiere

        return jsonify({
            "headers": info["headers"],
            "iterations": iterations,
            "message": message,
            "plot": {"x": x_plot, "y": y_plot, "center": plot_center},
            "root": {"x": root, "y": root_y} if root is not None else None,
            "is_fx": is_fx,
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
