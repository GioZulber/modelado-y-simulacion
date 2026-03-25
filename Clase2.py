# Metodo de aceleracion Aitken
import numpy as np
from tabulate import tabulate

# 1. Usar el metodo de punto fijo y obtener x0, x1, x2
# 2. Calcular el nuevo punto fijo usando la formula de Aitken: x_aitken = x0 - (x1 - x0)^2 / (x2 - 2*x1 + x0)
# 3. Repetir el proceso hasta que el error absoluto sea menor que la tolerancia o se alcance el número máximo de iteraciones.


def aitken(funcion, x0, max_iter=100, tol=1e-6, precision = 8):
    iteraciones = []
    for i in range(max_iter):
        x1 = round(funcion(x0), precision)
        x2 = round(funcion(x1), precision)
        
        denominador = x2 - 2*x1 + x0
        if denominador == 0:
            print("Denominador cero, se detiene la iteración para evitar división por cero.")
            break
            
        x_aitken = round(x0 - (x1 - x0)**2 / denominador, precision) # Calcular el nuevo punto fijo usando la formula de Aitken
        errorAbs = round(abs(x_aitken - x0), precision) # Calcular el error absoluto
        iteraciones.append([i + 1, x0, x1, x2, x_aitken, errorAbs]) # Guardar la iteración, los valores anteriores, el nuevo valor y el error absoluto
        
        if errorAbs < tol:
            print(f"Punto fijo acelerado encontrado: {x_aitken} en la iteración {i + 1}")
            break
        x0 = x_aitken # Actualizar x0 para la siguiente iteración

    print(tabulate(iteraciones, headers=["Iteración", "x0", "x1", "x2", "x_aitken", "Error Abs"], tablefmt="grid", floatfmt=f".{precision}f"))
    return x_aitken


# funcion f(x) = pi/2 ** 2 - x - x --> g(x) = x = 2/pi + 4/(pi * x)
funcionAitken1 = lambda x: 2/np.pi + 4/(np.pi * x) # Ejemplo de función para punto fijo g(x) = 2/pi + 4/pi * x
x0 = 1.4  # Punto inicial

# f(x) = cos(x) - x --> g(x) = x = cos(x)
funcionAitken2 = lambda x: np.cos(x) # Ejemplo de función para punto fijo g(x) = cos(x)
x02 = 1.0  # Punto

# ncionAitken2 = lambda x:

# g(x) = e^(-x), x0 = 1
funcionAitken3 = lambda x: np.exp(-x)
x03 = 1

# g(x) = ln(x + 1), x0 = 0.5
funcionAitken4 = lambda x: np.log(x + 1)
x04 = 0.5


#aitken(funcionAitken1, x0)
#aitken(funcionAitken2, x02)
#aitken(funcionAitken3, x03)
#aitken(funcionAitken4, x04)



# METODO DE NEWTON-RAPHSON
"""
    Buscamos la raiz de una función f(x) utilizando el método de Newton-Raphson.
    1. Definir la función f(x) y su derivada f'(x).
    2. Elegir un punto inicial x0.
    3. Iterar utilizand
    
    A tener en cuenta: 
     - La pemdiente de la tangente en el punto x0 no debe ser cero (f'(x0) != 0).
     - La funcion debe ser una funcion continua y suave para garantizar la convergencia del método.
    
    Pros: 
        - Convergencia rápida cuando se está cerca de la raíz.
        - Requiere menos iteraciones que otros métodos como la bisección o el punto fijo.
    Contras:
        - Puede divergir si el punto inicial no está bien elegido o si la función tiene inflexiones cerca de la raíz.
        - Puede haber errores si la derivada es cero o muy pequeña en el punto inicial, lo que puede llevar a una división por cero o a una convergencia muy lenta.
        - Requiere el cálculo de la derivada, lo que puede ser complicado para funciones complejas o no diferenciables.
"""    

fx = lambda x: np.exp(x) + x**2 - 4 # Ejemplo de función: f(x) = e^x + x^2 - 4
x0 = 0.5
def derivada(funcion, x, h=1e-5):
    return (funcion(x + h) - funcion(x - h)) / (2 * h)

def newton_raphson(funcion, x0, max_iter=100, tol=1e-6, precision=8):
    iteraciones = []
    for i in range(max_iter):
        f_x0 = round(funcion(x0), precision)
        f_prime_x0 = round(derivada(funcion, x0), precision)
        
        if f_prime_x0 == 0:
            print("Derivada cero, se detiene la iteración para evitar división por cero.")
            break
        
        x1 = round(x0 - f_x0 / f_prime_x0, precision) # Calcular el nuevo punto usando la fórmula de Newton-Raphson
        errorAbs = round(abs(x1 - x0), precision) # Calcular el error absoluto
        errorRel = round(errorAbs / abs(x1), precision) * 100 if x1 != 0 else None # Calcular el error relativo
        iteraciones.append([i + 1, x0, f_x0, f_prime_x0, x1, errorAbs, errorRel]) # Guardar la iteración, el valor anterior, la función en el valor anterior, la derivada en el valor anterior, el nuevo valor y el error absoluto
        
        if errorAbs < tol:
            print(f"Raíz encontrada: {x1} en la iteración {i + 1}")
            break
        
        x0 = x1 # Actualizar x0 para la siguiente iteración

    print(tabulate(iteraciones, headers=["Iteración", "x0", "f(x0)", "f'(x0)", "x1", "Error Abs", "Error Rel"], tablefmt="grid", floatfmt=f".{precision}f"))
    return x1

#newton_raphson(fx, x0)

funcion2 = lambda x: (x-1)**2 
# newton_raphson(funcion2, 0)

funcion3 = lambda x: x**3 - 2*x -5
#newton_raphson(funcion3, 1.5)

funcion4 = lambda x: x * np.exp(-x)
newton_raphson(funcion4, -1)
