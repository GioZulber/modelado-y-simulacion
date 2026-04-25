import numpy as np


HEADERS = ["i", "x_i", "f(x_i)", "Peso", "Peso * f(x_i)"]


def _asegurar_funcion(funcion):
    if funcion is None:
        raise ValueError("Debés ingresar una función f(x) válida.")


def _asegurar_intervalo(a, b):
    if a == b:
        raise ValueError("El intervalo no puede tener longitud cero. Verificá que a != b.")


def _validar_subintervalos(n, minimo=1, debe_ser_par=False, multiplo=None):
    if n is None:
        raise ValueError("Debés ingresar n (cantidad de subintervalos) para este método.")

    n = int(n)
    if n < minimo:
        raise ValueError(f"n debe ser mayor o igual a {minimo}.")
    if debe_ser_par and n % 2 != 0:
        raise ValueError("n debe ser par para aplicar esta regla compuesta.")
    if multiplo is not None and n % multiplo != 0:
        raise ValueError(f"n debe ser múltiplo de {multiplo} para aplicar esta regla.")
    return n


def _redondear(valor, precision):
    return round(float(valor), precision)


def _resolver_regla(nombre, funcion, xs, pesos, factor, h, precision, n=None):
    iteraciones = []
    sumatoria = 0.0

    for i, (x_i, peso) in enumerate(zip(xs, pesos)):
        try:
            fx_i = float(funcion(float(x_i)))
        except Exception as exc:
            raise ValueError(f"No se pudo evaluar f(x) en x = {x_i}: {exc}") from exc

        termino = peso * fx_i
        sumatoria += termino
        iteraciones.append([
            i,
            _redondear(x_i, precision),
            _redondear(fx_i, precision),
            peso,
            _redondear(termino, precision),
        ])

    aproximacion = factor * sumatoria

    lineas = [f"{nombre} completada exitosamente.", "", "Datos:"]
    if n is not None:
        lineas.append(f"  n = {n}")
    lineas.extend([
        f"  h = {_redondear(h, precision)}",
        f"  Sumatoria ponderada = {_redondear(sumatoria, precision)}",
        f"  Factor = {_redondear(factor, precision)}",
        f"  Integral aproximada = {_redondear(aproximacion, precision)}",
    ])

    return iteraciones, "\n".join(lineas)


def trapecio(funcion, a, b, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = b - a
    xs = [a, b]
    pesos = [1, 1]
    factor = h / 2.0
    return _resolver_regla("Regla del trapecio", funcion, xs, pesos, factor, h, precision)


def rectangulo_medio(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=1)

    h = (b - a) / n
    xs = [a + (i + 0.5) * h for i in range(n)]
    pesos = [1] * n
    factor = h
    return _resolver_regla("Regla del rectangulo medio", funcion, xs, pesos, factor, h, precision, n=n)


def trapecio_compuesto(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=1)

    h = (b - a) / n
    xs = np.linspace(a, b, n + 1)
    pesos = [1] + [2] * (n - 1) + [1]
    factor = h / 2.0
    return _resolver_regla("Regla del trapecio compuesta", funcion, xs, pesos, factor, h, precision, n=n)


def _simpson_simple(nombre, funcion, a, b, precision):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = (b - a) / 2.0
    xs = np.linspace(a, b, 3)
    pesos = [1, 4, 1]
    factor = h / 3.0
    return _resolver_regla(nombre, funcion, xs, pesos, factor, h, precision)


def simpson(funcion, a, b, max_iter=100, tol=1e-6, precision=8):
    return _simpson_simple("Regla de Simpson", funcion, a, b, precision)


def simpson_1_3(funcion, a, b, max_iter=100, tol=1e-6, precision=8):
    return _simpson_simple("Regla de Simpson 1/3", funcion, a, b, precision)


def simpson_1_3_compuesta(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=2, debe_ser_par=True)

    h = (b - a) / n
    xs = np.linspace(a, b, n + 1)
    pesos = [1]
    for i in range(1, n):
        pesos.append(4 if i % 2 != 0 else 2)
    pesos.append(1)

    factor = h / 3.0
    return _resolver_regla("Regla de Simpson 1/3 compuesta", funcion, xs, pesos, factor, h, precision, n=n)


def simpson_3_8(funcion, a, b, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = (b - a) / 3.0
    xs = np.linspace(a, b, 4)
    pesos = [1, 3, 3, 1]
    factor = 3.0 * h / 8.0
    return _resolver_regla("Regla de Simpson 3/8", funcion, xs, pesos, factor, h, precision)


def simpson_3_8_compuesta(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=3, multiplo=3)

    h = (b - a) / n
    xs = np.linspace(a, b, n + 1)
    pesos = [1]
    for i in range(1, n):
        pesos.append(2 if i % 3 == 0 else 3)
    pesos.append(1)

    factor = 3.0 * h / 8.0
    return _resolver_regla("Regla de Simpson 3/8 compuesta", funcion, xs, pesos, factor, h, precision, n=n)


METODOS = {
    "rectangulo_medio": {
        "nombre": "Regla del Rectangulo Medio",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "headers": HEADERS,
        "resolver": rectangulo_medio,
        "root_col": None,
    },
    "trapecio": {
        "nombre": "Regla del Trapecio",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "headers": HEADERS,
        "resolver": trapecio,
        "root_col": None,
    },
    "trapecio_compuesto": {
        "nombre": "Regla del Trapecio Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "headers": HEADERS,
        "resolver": trapecio_compuesto,
        "root_col": None,
    },
    "simpson": {
        "nombre": "Regla de Simpson",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "headers": HEADERS,
        "resolver": simpson,
        "root_col": None,
    },
    "simpson_1_3": {
        "nombre": "Regla de Simpson 1/3",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "headers": HEADERS,
        "resolver": simpson_1_3,
        "root_col": None,
    },
    "simpson_1_3_compuesta": {
        "nombre": "Regla de Simpson 1/3 Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "headers": HEADERS,
        "resolver": simpson_1_3_compuesta,
        "root_col": None,
    },
    "simpson_3_8": {
        "nombre": "Regla de Simpson 3/8",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "headers": HEADERS,
        "resolver": simpson_3_8,
        "root_col": None,
    },
    "simpson_3_8_compuesta": {
        "nombre": "Regla de Simpson 3/8 Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "headers": HEADERS,
        "resolver": simpson_3_8_compuesta,
        "root_col": None,
    },
}
