import numpy as np
from tabulate import tabulate

def biseccion(funcion, a, b, max_iter=100, tol=1e-6, precision=5):
    # Teoria de Balsano
    if funcion(a) * funcion(b) >= 0:
        print("La función no cambia de signo en el intervalo [a, b].")
        return None

    iteraciones = []
    for i in range(max_iter):
        c = round((a + b) / 2.0, precision)
        fc = round(funcion(c), precision)
        
        if(i in [0, 1]):
            iteraciones.append([i + 1, a, b, c, fc, None])
        else:
            errorAbs = iteraciones[-1][3] - iteraciones[-2][3] if i > 0 else None  
            iteraciones.append([i + 1, a, b, c, fc, errorAbs])

        if abs(fc) < tol or (b-a) / 2 < tol:
            print(f"Raíz encontrada: {c} en la iteración {i + 1}")
            break

        if funcion(a) * funcion(c) < 0:
            b = c
        else:
            a = c

    print(tabulate(iteraciones, headers=["Iteración", "a", "b", "c", "f(c)", "Error Abs"], tablefmt="grid"))
    return c


funcion3 = lambda x: x**3 - x - 1 # Ejemplo de función: f(x) = x^3 - x - 2
a3 = 1  # Punto inicial a
b3 = 2  # Punto inicial b
#biseccion(funcion3, a3, b3)


funcion = lambda x: x**2 - 3 # Ejemplo de función: f(x) = x^2 - 3
a = 1  # Punto inicial a
b = 2  # Punto inicial b
# biseccion(funcion, a, b)

funcion2 = lambda x: np.exp(x) - x- 2# Ejemplo de función: f(x) = e^x - x - 2
a2 = 1 # Punto inicial a
b2 = 2  # Punto inicial b
#biseccion(funcion2, a2, b2)

def puntoFijo(funcion, x0, max_iter=100, tol=1e-6, precision=6):
    iteraciones = []
    for i in range(max_iter):
        x1 = round(funcion(x0), precision) # Calcular el nuevo punto fijo
        errorAbs = round(abs(x1 - x0), precision) # Calcular el error absoluto
        iteraciones.append([i + 1, x0, x1, errorAbs]) # Guardar la iteración, el valor anterior, el nuevo valor y el error absoluto
        
        if errorAbs < tol:
            print(f"Punto fijo encontrado: {x1} en la iteración {i + 1}")
            break
        
        x0 = x1

    print(tabulate(iteraciones, headers=["Iteración", "x0", "x1", "Error Abs"], tablefmt="grid"))
    return x1

funcionPF = lambda x: (x + 1)**(1/3) # Ejemplo de función para punto fijo 3√(x + 1) = x = g(x)
x0 = 1  # Punto inicial
#puntoFijo(funcionPF, x0)

funcionG = lambda x: np.exp(-x) # Ejemplo de función para punto fijo g(x) = -e^(-x) 
x0G = 0.5  # Punto inicial
#puntoFijo(funcionG, x0G) 

funcionG2 = lambda x: 1/3 * (2*np.sqrt(3) + x) # Ejemplo de función para punto fijo g(x) = x = 1/3 (2√3 + x). Con la f(x) = √3
x0G2 = 1  # Punto inicial1
puntoFijo(funcionG2, x0G2)