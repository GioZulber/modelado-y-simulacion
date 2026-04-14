import math
import sympy as sp
import numpy as np
import re
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


_PARSER_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)


def _parse_symbolic_expression(expr_str: str):
    text = expr_str.strip()
    text = re.sub(r'\be\b', 'E', text)
    text = re.sub(r'\bx(\d+)\b', r'x**\1', text)
    x = sp.Symbol('x')
    return parse_expr(text, transformations=_PARSER_TRANSFORMATIONS, local_dict={"x": x}, evaluate=True)

def resolver_lagrange(fn, x_data=None, y_data=None, x0=None, **kwargs):
    if not x_data or not y_data:
        raise ValueError("x_data y y_data son obligatorios para Lagrange")
    if len(x_data) != len(y_data):
        raise ValueError("x_data y y_data deben tener la misma cantidad de elementos")

    x_sym = sp.Symbol('x')
    n = len(x_data)
    polinomio = 0
    bases_str = []
    bases_latex = []
    
    # Construcción del polinomio de Lagrange
    for i in range(n):
        l_i = 1
        for j in range(n):
            if i != j:
                # Evitar división por cero si hay puntos x duplicados
                if x_data[i] == x_data[j]:
                    raise ValueError(f"Los puntos en x_data no pueden estar duplicados: {x_data[i]}")
                l_i *= (x_sym - x_data[j]) / (x_data[i] - x_data[j])
        
        # Guardar la base (L_i)
        l_i_simplificada = sp.nsimplify(sp.expand(l_i), tolerance=1e-10, rational=True)
        bases_str.append(str(l_i_simplificada))
        bases_latex.append(sp.latex(l_i_simplificada))
        polinomio += y_data[i] * l_i
        
    polinomio_expandido = sp.nsimplify(sp.expand(polinomio), tolerance=1e-10, rational=True)
    
    # Evaluar en x0 si se proporciona
    valor_x0 = None
    if x0 is not None:
        try:
            valor_x0 = float(polinomio_expandido.subs(x_sym, x0))
        except Exception:
            pass
    
    # Análisis de error si hay función original y x0
    error_info = ""
    errores_latex = []
    cota_error = None
    if fn is not None and x0 is not None:
        try:
            # Error local real
            valor_real = float(fn(x0))
            error_local = abs(valor_real - valor_x0)
            error_relativo = error_local / abs(valor_real) if valor_real != 0 else float('inf')
            error_info = f"\nAnálisis de Error:\n  Valor real f({x0}) = {valor_real:g}\n  Error local = {error_local:g}\n  Error relativo = {error_relativo:g}"
            errores_latex.append(f"\\text{{Valor real}} \\ f({x0}) = {valor_real:g}")
            errores_latex.append(f"\\text{{Error Local}} = {error_local:g}")
            errores_latex.append(f"\\text{{Error Relativo}} = {error_relativo:g}")
            
            # Cota de error teórico
            f_expr_str = kwargs.get("f_expr_str")
            if f_expr_str:
                f_sym = _parse_symbolic_expression(f_expr_str)
                # Derivada de orden n
                f_deriv_n = sp.diff(f_sym, x_sym, n)
                
                # Evaluar máximo en el intervalo
                nodos_y_x0 = x_data + [x0]
                a_int, b_int = float(min(nodos_y_x0)), float(max(nodos_y_x0))
                
                # Crear malla para buscar máximo absoluto
                malla = np.linspace(a_int, b_int, 10000)
                f_deriv_n_func = sp.lambdify(x_sym, f_deriv_n, modules=["numpy", "sympy"])
                
                max_deriv = 0
                for val in malla:
                    try:
                        d_val = abs(float(f_deriv_n_func(val)))
                        if d_val > max_deriv:
                            max_deriv = d_val
                    except Exception:
                        pass
                
                # Producto nodal
                prod_nodal = 1
                for xi in x_data:
                    prod_nodal *= abs(x0 - xi)
                    
                cota_error = (max_deriv / math.factorial(n)) * prod_nodal
                error_info += f"\n  Cota de error teórico = {cota_error:g}"
                errores_latex.append(f"\\text{{Error Global (Cota)}} = {cota_error:g}")
        except Exception as e:
            # Si falla el cálculo simbólico, mostramos solo lo que se pudo
            pass

    mensaje = "Interpolación de Lagrange completada exitosamente."
    if valor_x0 is not None:
        mensaje += f"\n\nEvaluación en x0={x0}:\n  P({x0}) = {valor_x0:g}"
    if error_info:
        mensaje += error_info
        
    # Devolveremos los puntos como iteraciones (arrays simples para la tabla frontend)
    iteraciones = []
    for i in range(n):
        iteraciones.append([i, x_data[i], y_data[i]])
        
    latex_str = sp.latex(polinomio_expandido)
        
    # Agregamos las bases al return como un cuarto elemento, y el látex del polinomio
    return iteraciones, mensaje, str(polinomio_expandido), bases_str, ["i", "x", "y"], latex_str, bases_latex, errores_latex


def resolver_newton(fn, x_data=None, y_data=None, x0=None, **kwargs):
    if not x_data or not y_data:
        raise ValueError("x_data y y_data son obligatorios para Newton")
    if len(x_data) != len(y_data):
        raise ValueError("x_data y y_data deben tener la misma cantidad de elementos")

    n = len(x_data)
    
    # Si x0 está dado, ordenamos de forma centrada (zigzag)
    if x0 is not None:
        pares = list(zip(x_data, y_data))
        pares.sort(key=lambda p: abs(p[0] - x0))
        x_usar = [p[0] for p in pares]
        y_usar = [p[1] for p in pares]
    else:
        x_usar = list(x_data)
        y_usar = list(y_data)
        
    # Matriz para almacenar las diferencias
    F = np.zeros((n, n))
    F[:, 0] = y_usar
    
    # Cálculo de las diferencias divididas
    for j in range(1, n):
        for i in range(n - j):
            if x_usar[i+j] == x_usar[i]:
                raise ValueError(f"División por cero. Puntos duplicados detectados: {x_usar[i]}")
            F[i, j] = (F[i+1, j-1] - F[i, j-1]) / (x_usar[i+j] - x_usar[i])
            
    # Los coeficientes son la primera fila
    coeficientes = F[0, :]
    
    x_sym = sp.Symbol('x')
    P = coeficientes[0]
    producto_nodal = 1
    
    for i in range(1, n):
        producto_nodal *= (x_sym - x_usar[i-1])
        P += coeficientes[i] * producto_nodal
        
    polinomio_expandido = sp.expand(P)
    
    # Evaluar en x0 si se proporciona
    valor_x0 = None
    if x0 is not None:
        try:
            valor_x0 = float(polinomio_expandido.subs(x_sym, x0))
        except Exception:
            pass

    # Análisis de error si hay función original y x0
    error_info = ""
    cota_error = None
    if fn is not None and x0 is not None:
        try:
            # Error local real
            valor_real = float(fn(x0))
            error_local = abs(valor_real - valor_x0)
            error_info = f"\nAnálisis de Error:\n  Valor real f({x0}) = {valor_real:g}\n  Error local = {error_local:g}"
            
            # Cota de error teórico
            f_expr_str = kwargs.get("f_expr_str")
            if f_expr_str:
                f_sym = _parse_symbolic_expression(f_expr_str)
                # Derivada de orden n
                f_deriv_n = sp.diff(f_sym, x_sym, n)
                
                # Evaluar máximo en el intervalo
                nodos_y_x0 = x_data + [x0]
                a_int, b_int = float(min(nodos_y_x0)), float(max(nodos_y_x0))
                
                # Crear malla para buscar máximo absoluto
                malla = np.linspace(a_int, b_int, 10000)
                f_deriv_n_func = sp.lambdify(x_sym, f_deriv_n, modules=["numpy", "sympy"])
                
                max_deriv = 0
                for val in malla:
                    try:
                        d_val = abs(float(f_deriv_n_func(val)))
                        if d_val > max_deriv:
                            max_deriv = d_val
                    except Exception:
                        pass
                
                # Producto nodal
                prod_nodal = 1
                for xi in x_data:
                    prod_nodal *= abs(x0 - xi)
                    
                cota_error = (max_deriv / math.factorial(n)) * prod_nodal
                error_info += f"\n  Cota de error teórico = {cota_error:g}"
        except Exception as e:
            # Si falla el cálculo simbólico, mostramos solo lo que se pudo
            pass

    mensaje = "Interpolación de Newton completada exitosamente."
    if x0 is not None:
        mensaje += f"\n\nNodos ordenados (centrados respecto a x0={x0}):\nx: {x_usar}\ny: {y_usar}"
        if valor_x0 is not None:
            mensaje += f"\n\nEvaluación en x0={x0}:\n  P({x0}) = {valor_x0:g}"
    else:
        mensaje += f"\n\nNodos utilizados:\nx: {x_usar}\ny: {y_usar}"
        
    if error_info:
        mensaje += error_info
        
    # Devolveremos la matriz de diferencias divididas como iteraciones (aproximado)
    iteraciones = []
    for i in range(n):
        row = [i, x_usar[i], F[i, 0]]
        for j in range(1, n - i):
            row.append(F[i, j])
        iteraciones.append(row)
        
    headers = ["i", "x", "f[x0]"] + [f"f[..{j}]" for j in range(1, n)]

    latex_str = sp.latex(polinomio_expandido)

    # Newton no devuelve bases
    return iteraciones, mensaje, str(polinomio_expandido), None, headers, latex_str


METODOS = {
    "lagrange": {
        "nombre": "Interpolación de Lagrange",
        "clase": "Clase 3: Interpolación",
        "requiere": ["x_data", "y_data"],
        "opcionales": ["f_expr", "x0"],
        "headers": ["i", "x", "y"],
        "root_col": None,
        "resolver": resolver_lagrange
    },
    "newton_dif_div": {
        "nombre": "Diferencias Divididas (Newton)",
        "clase": "Clase 3: Interpolación",
        "requiere": ["x_data", "y_data"],
        "opcionales": ["f_expr", "x0"],
        "headers": ["i", "x", "f[x0]"],
        "root_col": None,
        "resolver": resolver_newton
    }
}
