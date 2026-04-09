import numpy as np
import sympy as sp
import math

def lagrange(x_data, y_data, x_eval, func_str=None):
    """
    Calcula el polinomio de Lagrange.
    Si se proporciona la función original (func_str), calcula los errores.
    Si no, solo realiza la interpolación con los datos.
    """
    x = sp.Symbol('x')
    n = len(x_data) - 1
    
    # ==========================================
    # 1. Cálculo del Polinomio de Lagrange P(x)
    # ==========================================
    P = 0
    bases = []
    for i in range(n + 1):
        L_i = 1
        for j in range(n + 1):
            if i != j:
                L_i *= (x - x_data[j]) / (x_data[i] - x_data[j])
        bases.append(sp.nsimplify(sp.expand(L_i), tolerance=1e-10, rational=True))
        P += y_data[i] * L_i
        
    P_simplificado = sp.nsimplify(sp.expand(P), tolerance=1e-10, rational=True)
    valor_aprox = P_simplificado.subs(x, x_eval)
    
    # ==========================================
    # 2. Resultados de Interpolación
    # ==========================================
    print("--- RESULTADOS DE INTERPOLACIÓN ---")
    for i, base in enumerate(bases):
        print(f"Base L_{i}(x):\n{base}\n")
    print(f"Polinomio de Lagrange P(x):\n{P_simplificado}\n")
    print(f"Evaluación en x = {x_eval}:")
    print(f"  Valor aprox P({x_eval}) = {float(valor_aprox):.8f}\n")
    
    # ==========================================
    # 3. Análisis de Errores (Solo si hay función)
    # ==========================================
    if func_str is not None:
        f = sp.sympify(func_str)
        valor_real = f.subs(x, x_eval)
        error_local_real = abs(valor_real - valor_aprox)
        error_relativo = error_local_real / abs(valor_real) if valor_real != 0 else float('inf')
        
        f_deriv = sp.diff(f, x, n + 1)
        W = 1
        for xi in x_data:
            W *= (x - xi)
            
        a, b = min(x_data), max(x_data)
        t_vals = np.linspace(a, b, 1000)
        
        f_deriv_func = sp.lambdify(x, sp.Abs(f_deriv), 'numpy')
        deriv_vals = f_deriv_func(t_vals)
        max_deriv = np.max(deriv_vals) if isinstance(deriv_vals, np.ndarray) else deriv_vals
        
        W_func = sp.lambdify(x, sp.Abs(W), 'numpy')
        max_W = np.max(W_func(t_vals))
        
        cota_error_local = (max_deriv / math.factorial(n + 1)) * abs(W.subs(x, x_eval))
        cota_error_global = (max_deriv / math.factorial(n + 1)) * max_W
        
        print("--- ANÁLISIS DE ERROR ---")
        print(f"  Valor real f({x_eval})  = {float(valor_real):.8f}")
        print(f"  Error local real    = {float(error_local_real):.8e}")
        print(f"  Error relativo      = {float(error_relativo):.8e}")
        print(f"  Cota de error local = {float(cota_error_local):.8e}\n")
        print(f"Cota de Error Global en el intervalo [{a}, {b}]:")
        print(f"  Max error posible   = {float(cota_error_global):.8e}")
    else:
        print("--- ANÁLISIS DE ERROR ---")
        print("No se proporcionó la función original. La interpolación fue exitosa, ")
        print("pero no se pueden calcular los errores teóricos (requieren derivadas).")
        
    return P_simplificado


def diferencias_divididas_centradas(x_data, y_data, x_eval):
    """
    Calcula el polinomio de interpolación de Newton mediante diferencias divididas,
    ordenando los nodos de forma centrada respecto al punto a evaluar.
    """
    n = len(x_data)
    
    # ==========================================
    # 1. Ordenamiento Centrado (Zigzag)
    # ==========================================
    # Emparejamos x e y, y los ordenamos según la distancia absoluta a x_eval
    pares = list(zip(x_data, y_data))
    pares.sort(key=lambda p: abs(p[0] - x_eval))
    
    x_centrado = [p[0] for p in pares]
    y_centrado = [p[1] for p in pares]
    
    # ==========================================
    # 2. Tabla de Diferencias Divididas
    # ==========================================
    # Matriz para almacenar las diferencias (llena de ceros inicialmente)
    F = np.zeros((n, n))
    F[:, 0] = y_centrado
    
    # Cálculo de las diferencias divididas
    for j in range(1, n):
        for i in range(n - j):
            F[i, j] = (F[i+1, j-1] - F[i, j-1]) / (x_centrado[i+j] - x_centrado[i])
            
    # Los coeficientes de nuestro polinomio son la primera fila de la tabla
    coeficientes = F[0, :]
    
    # ==========================================
    # 3. Construcción del Polinomio Entero
    # ==========================================
    x = sp.Symbol('x')
    P = coeficientes[0]
    producto_nodal = 1
    
    # Armamos P(x) sumando los términos de Newton
    for i in range(1, n):
        producto_nodal *= (x - x_centrado[i-1])
        P += coeficientes[i] * producto_nodal
        
    P_simplificado = sp.expand(P)
    
    # ==========================================
    # 4. Resultados
    # ==========================================
    valor_aprox = P_simplificado.subs(x, x_eval)
    
    print("--- 1. ORDENAMIENTO DE NODOS ---")
    print("Para hacer la interpolación centrada, los puntos se ordenaron así:")
    print(f"X centrados: {x_centrado}")
    print(f"Y centrados: {y_centrado}\n")
    
    print("--- 2. POLINOMIO DE NEWTON ---")
    print(f"Polinomio P(x) desarrollado:\n{P_simplificado}\n")
    
    print("--- 3. EVALUACIÓN ---")
    print(f"Evaluación en x = {x_eval}:")
    print(f"Valor aprox P({x_eval}) = {float(valor_aprox):.8f}")
    
    return P_simplificado, F
# ==========================================
# Ejemplo de uso
# ==========================================
if __name__ == "__main__":
    # Función original: f(x) = sin(x)
    
    
    # Puntos de datos conocidos (Nodos)
    x_puntos = [1,4]  # Nodos
    y_puntos = [1,2]  # f(x) en los nodos
    
    # Punto donde queremos evaluar el error local
    x_evaluar = 1.5
    
    lagrange(x_puntos, y_puntos, x_evaluar)
    diferencias_divididas_centradas(x_puntos, y_puntos, x_evaluar)