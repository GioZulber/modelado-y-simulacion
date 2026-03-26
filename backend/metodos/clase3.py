import math
import sympy as sp
import numpy as np

def resolver_lagrange(fn, x_data=None, y_data=None, x0=None, **kwargs):
    if not x_data or not y_data:
        raise ValueError("x_data y y_data son obligatorios para Lagrange")
    if len(x_data) != len(y_data):
        raise ValueError("x_data y y_data deben tener la misma cantidad de elementos")

    x_sym = sp.Symbol('x')
    n = len(x_data)
    polinomio = 0
    
    # Construcción del polinomio de Lagrange
    for i in range(n):
        l_i = 1
        for j in range(n):
            if i != j:
                # Evitar división por cero si hay puntos x duplicados
                if x_data[i] == x_data[j]:
                    raise ValueError(f"Los puntos en x_data no pueden estar duplicados: {x_data[i]}")
                l_i *= (x_sym - x_data[j]) / (x_data[i] - x_data[j])
        polinomio += y_data[i] * l_i
        
    polinomio_expandido = sp.expand(polinomio)
    
    # Evaluar en x0 si se proporciona
    valor_x0 = None
    if x0 is not None:
        # Evaluate using subs
        valor_x0 = float(polinomio_expandido.subs(x_sym, x0))
    
    mensaje = f"Polinomio de Lagrange: P(x) = {polinomio_expandido}"
    if valor_x0 is not None:
        mensaje += f"\nEvaluación en x0={x0}: P({x0}) = {valor_x0}"
        
    # Devolveremos los puntos como iteraciones para que se muestren en la tabla
    iteraciones = []
    for i in range(n):
        iteraciones.append({
            "i": i,
            "x": x_data[i],
            "y": y_data[i]
        })
        
    # Return the symbolic expression string so the backend can parse it for plotting
    return iteraciones, mensaje, str(polinomio_expandido)


METODOS = {
    "lagrange": {
        "nombre": "Interpolación de Lagrange",
        "clase": "Clase 3: Interpolación",
        "requiere": ["x_data", "y_data", "x0", "f_expr"], # f_expr es opcional, se usa para comparar
        "headers": ["i", "x", "y"],
        "root_col": None,
        "resolver": resolver_lagrange
    }
}
