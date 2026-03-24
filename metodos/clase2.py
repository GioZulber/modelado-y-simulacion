import numpy as np


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------

def aitken(funcion, x0, max_iter=100, tol=1e-6, precision=8):
    """Método de Aceleración de Aitken (Δ²)."""
    iteraciones = []
    for i in range(max_iter):
        try:
            x1 = round(funcion(x0), precision)
            x2 = round(funcion(x1), precision)
        except Exception as exc:
            return iteraciones, f"Error evaluando g(x): {exc}"

        denominador = x2 - 2 * x1 + x0
        if denominador == 0:
            return iteraciones, "Denominador cero — se detuvo para evitar división por cero."

        x_aitken = round(x0 - (x1 - x0) ** 2 / denominador, precision)
        error_abs = round(abs(x_aitken - x0), precision)
        iteraciones.append([i + 1, x0, x1, x2, x_aitken, error_abs])

        if error_abs < tol:
            return iteraciones, f"Punto fijo acelerado encontrado: {x_aitken} en la iteración {i + 1}"

        x0 = x_aitken

    return iteraciones, f"Se alcanzó el máximo de iteraciones. Última aproximación: {x0}"


def derivada(funcion, x, h=1e-5):
    """Derivada numérica centrada."""
    return (funcion(x + h) - funcion(x - h)) / (2 * h)


def newton_raphson(funcion, x0, max_iter=100, tol=1e-6, precision=8):
    """Método de Newton-Raphson para encontrar raíces."""
    iteraciones = []
    for i in range(max_iter):
        try:
            f_x0 = round(funcion(x0), precision)
            f_prime_x0 = round(derivada(funcion, x0), precision)
        except Exception as exc:
            return iteraciones, f"Error evaluando f(x) en x={x0}: {exc}"

        if f_prime_x0 == 0:
            return iteraciones, "Derivada cero — se detuvo para evitar división por cero."

        x1 = round(x0 - f_x0 / f_prime_x0, precision)
        error_abs = round(abs(x1 - x0), precision)
        error_rel = round(error_abs / abs(x1), precision) * 100 if x1 != 0 else None
        iteraciones.append([i + 1, x0, f_x0, f_prime_x0, x1, error_abs, error_rel])

        if error_abs < tol:
            return iteraciones, f"Raíz encontrada: {x1} en la iteración {i + 1}"

        x0 = x1

    return iteraciones, f"Se alcanzó el máximo de iteraciones. Última aproximación: {x0}"


# ---------------------------------------------------------------------------
# Registry — the web app auto-discovers this dict
# ---------------------------------------------------------------------------

METODOS = {
    "aitken": {
        "nombre": "Aitken (Aceleración Δ²)",
        "clase": "Clase 2",
        "requiere": ["f_expr", "g_expr", "x0"],
        "headers": ["Iteración", "x0", "x1", "x2", "x_aitken", "Error Abs"],
        "resolver": aitken,
        "root_col": 4,
    },
    "newton_raphson": {
        "nombre": "Newton-Raphson",
        "clase": "Clase 2",
        "requiere": ["f_expr", "x0"],
        "headers": ["Iteración", "x0", "f(x0)", "f'(x0)", "x1", "Error Abs", "Error Rel (%)"],
        "resolver": newton_raphson,
        "root_col": 4,
    },
}
