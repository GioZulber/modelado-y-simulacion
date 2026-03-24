import numpy as np


# ---------------------------------------------------------------------------
# Methods
# ---------------------------------------------------------------------------

def biseccion(funcion, a, b, max_iter=100, tol=1e-6, precision=6):
    """Método de Bisección para encontrar raíces."""
    if funcion(a) * funcion(b) >= 0:
        return [], "La función no cambia de signo en el intervalo [a, b]. Verificá que f(a) y f(b) tengan signos opuestos."

    iteraciones = []
    c = a
    for i in range(max_iter):
        c = round((a + b) / 2.0, precision)
        fc = round(funcion(c), precision)

        if i in [0, 1]:
            error_abs = None
        else:
            error_abs = round(abs(iteraciones[-1][3] - iteraciones[-2][3]), precision)

        iteraciones.append([i + 1, a, b, c, fc, error_abs])

        if abs(fc) < tol or (b - a) / 2 < tol:
            return iteraciones, f"Raíz encontrada: {c} en la iteración {i + 1}"

        if funcion(a) * funcion(c) < 0:
            b = c
        else:
            a = c

    return iteraciones, f"Se alcanzó el máximo de iteraciones. Última aproximación: {c}"


def punto_fijo(funcion, x0, max_iter=100, tol=1e-6, precision=6):
    """Método de Punto Fijo."""
    iteraciones = []
    for i in range(max_iter):
        try:
            x1 = round(funcion(x0), precision)
        except Exception as exc:
            return iteraciones, f"Error evaluando g(x) en x={x0}: {exc}"

        error_abs = round(abs(x1 - x0), precision)
        iteraciones.append([i + 1, x0, x1, error_abs])

        if error_abs < tol:
            return iteraciones, f"Punto fijo encontrado: {x1} en la iteración {i + 1}"

        x0 = x1

    return iteraciones, f"Se alcanzó el máximo de iteraciones. Última aproximación: {x0}"


# ---------------------------------------------------------------------------
# Registry — the web app auto-discovers this dict
# ---------------------------------------------------------------------------

METODOS = {
    "biseccion": {
        "nombre": "Bisección",
        "clase": "Clase 1",
        "requiere": ["f_expr", "a", "b"],
        "headers": ["Iteración", "a", "b", "c", "f(c)", "Error Abs"],
        "resolver": biseccion,
        "root_col": 3,
    },
    "punto_fijo": {
        "nombre": "Punto Fijo",
        "clase": "Clase 1",
        "requiere": ["f_expr", "g_expr", "x0"],
        "headers": ["Iteración", "x0", "x1", "Error Abs"],
        "resolver": punto_fijo,
        "root_col": 2,
    },
}
