import math

import numpy as np
import sympy as sp


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


TRUNCATION_ERROR_SPECS = {
    "rectangulo_medio": {
        "order": 2,
        "coefficient": lambda h, a, b: (b - a) * h**2 / 24.0,
        "formula": "((b-a) h^2 / 24) f''(e)",
    },
    "trapecio": {
        "order": 2,
        "coefficient": lambda h, a, b: -(h**3) / 12.0,
        "formula": "-(h^3 / 12) f''(e)",
    },
    "trapecio_compuesto": {
        "order": 2,
        "coefficient": lambda h, a, b: -(b - a) * h**2 / 12.0,
        "formula": "-((b-a) h^2 / 12) f''(e)",
    },
    "simpson_1_3": {
        "order": 4,
        "coefficient": lambda h, a, b: -(h**5) / 90.0,
        "formula": "-(h^5 / 90) f^(4)(e)",
    },
    "simpson_1_3_compuesta": {
        "order": 4,
        "coefficient": lambda h, a, b: -(b - a) * h**4 / 180.0,
        "formula": "-((b-a) h^4 / 180) f^(4)(e)",
    },
    "simpson_3_8": {
        "order": 4,
        "coefficient": lambda h, a, b: -3.0 * h**5 / 80.0,
        "formula": "-(3 h^5 / 80) f^(4)(e)",
    },
    "simpson_3_8_compuesta": {
        "order": 4,
        "coefficient": lambda h, a, b: -(b - a) * h**4 / 80.0,
        "formula": "-((b-a) h^4 / 80) f^(4)(e)",
    },
}


def _a_float_finito(valor):
    if isinstance(valor, complex):
        if abs(valor.imag) < 1e-10:
            valor = valor.real
        else:
            raise ValueError("resultado complejo")

    try:
        resultado = float(valor)
    except (TypeError, ValueError):
        complejo = complex(sp.N(valor))
        if abs(complejo.imag) >= 1e-10:
            raise ValueError("resultado complejo")
        resultado = float(complejo.real)

    if not math.isfinite(resultado):
        raise ValueError("resultado no finito")
    return resultado


def _punto_exactificado(x_i):
    return sp.nsimplify(float(x_i), rational=True)


def _limite_finito(expr, symbol, x_i):
    x_exact = _punto_exactificado(x_i)
    limites = []

    for direccion in ("+", "-"):
        try:
            limite = sp.limit(expr, symbol, x_exact, dir=direccion)
            limites.append(_a_float_finito(limite))
        except Exception:
            continue

    if not limites:
        raise ValueError("no existe un limite finito en ese punto")

    referencia = limites[0]
    tolerancia = max(1e-9, abs(referencia) * 1e-8)
    if any(abs(valor - referencia) > tolerancia for valor in limites[1:]):
        raise ValueError("los limites laterales no coinciden")

    return referencia


def _evaluar_expr_en_punto(expr, symbol, x_i):
    x_exact = _punto_exactificado(x_i)
    try:
        return _a_float_finito(sp.N(expr.subs(symbol, x_exact)))
    except Exception:
        return _limite_finito(expr, symbol, x_i)


def _evaluar_funcion_en_nodo(funcion, x_i, precision):
    try:
        return _a_float_finito(funcion(float(x_i))), None
    except Exception as exc:
        expr = getattr(funcion, "_sympy_expr", None)
        symbol = getattr(funcion, "_sympy_symbol", None)
        if expr is None or symbol is None:
            raise exc

        valor = _limite_finito(expr, symbol, x_i)
        nota = (
            f"f({_redondear(x_i, precision)}) se obtuvo por limite: "
            f"lim x->{_redondear(x_i, precision)} f(x) = {_redondear(valor, precision)}"
        )
        return valor, nota


def _derivada_label(orden):
    return "f''(e)" if orden == 2 else f"f^({orden})(e)"


def _lineas_error_truncamiento(funcion, spec_key, e, h, a, b, precision):
    if e is None or spec_key is None:
        return []

    expr = getattr(funcion, "_sympy_expr", None)
    symbol = getattr(funcion, "_sympy_symbol", None)
    spec = TRUNCATION_ERROR_SPECS.get(spec_key)
    if expr is None or symbol is None or spec is None:
        return [
            "",
            "Error de truncamiento en un punto:",
            "  No disponible: falta la expresion simbolica de f(x).",
        ]

    try:
        derivada = sp.diff(expr, symbol, spec["order"])
        derivada_en_e = _evaluar_expr_en_punto(derivada, symbol, e)
        coeficiente = spec["coefficient"](float(h), float(a), float(b))
        error = coeficiente * derivada_en_e
    except Exception as exc:
        return [
            "",
            f"Error de truncamiento en e = {_redondear(e, precision)}:",
            f"  No se pudo calcular: {exc}",
        ]

    label = _derivada_label(spec["order"])
    return [
        "",
        f"Error de truncamiento en e = {_redondear(e, precision)}:",
        f"  Formula = {spec['formula']}",
        f"  {label} = {_redondear(derivada_en_e, precision)}",
        f"  Coeficiente = {_redondear(coeficiente, precision)}",
        f"  Error de truncamiento = {_redondear(error, precision)}",
    ]


def _resolver_regla(nombre, funcion, xs, pesos, factor, h, precision, n=None, a=None, b=None, e=None, x0=None, truncation_key=None):
    iteraciones = []
    sumatoria = 0.0
    notas_indeterminacion = []

    for i, (x_i, peso) in enumerate(zip(xs, pesos)):
        try:
            fx_i, nota_indeterminacion = _evaluar_funcion_en_nodo(funcion, x_i, precision)
        except Exception as exc:
            raise ValueError(f"No se pudo evaluar f(x) en x = {x_i}: {exc}") from exc

        if nota_indeterminacion:
            notas_indeterminacion.append(nota_indeterminacion)

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

    if notas_indeterminacion:
        lineas.extend(["", "Indeterminaciones removibles salvadas:"])
        lineas.extend(f"  {nota}" for nota in notas_indeterminacion)

    punto_error = e if e is not None else x0
    lineas.extend(_lineas_error_truncamiento(funcion, truncation_key, punto_error, h, a, b, precision))

    return iteraciones, "\n".join(lineas)


def trapecio(funcion, a, b, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = b - a
    xs = [a, b]
    pesos = [1, 1]
    factor = h / 2.0
    return _resolver_regla(
        "Regla del trapecio", funcion, xs, pesos, factor, h, precision,
        a=a, b=b, e=e, x0=x0, truncation_key="trapecio"
    )


def rectangulo_medio(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=1)

    h = (b - a) / n
    xs = [a + (i + 0.5) * h for i in range(n)]
    pesos = [1] * n
    factor = h
    return _resolver_regla(
        "Regla del rectangulo medio", funcion, xs, pesos, factor, h, precision, n=n,
        a=a, b=b, e=e, x0=x0, truncation_key="rectangulo_medio"
    )


def trapecio_compuesto(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)
    n = _validar_subintervalos(n, minimo=1)

    h = (b - a) / n
    xs = np.linspace(a, b, n + 1)
    pesos = [1] + [2] * (n - 1) + [1]
    factor = h / 2.0
    return _resolver_regla(
        "Regla del trapecio compuesta", funcion, xs, pesos, factor, h, precision, n=n,
        a=a, b=b, e=e, x0=x0, truncation_key="trapecio_compuesto"
    )


def _simpson_simple(nombre, funcion, a, b, precision, e=None, x0=None):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = (b - a) / 2.0
    xs = np.linspace(a, b, 3)
    pesos = [1, 4, 1]
    factor = h / 3.0
    return _resolver_regla(
        nombre, funcion, xs, pesos, factor, h, precision,
        a=a, b=b, e=e, x0=x0, truncation_key="simpson_1_3"
    )


def simpson(funcion, a, b, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    return _simpson_simple("Regla de Simpson", funcion, a, b, precision, e=e, x0=x0)


def simpson_1_3(funcion, a, b, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    return _simpson_simple("Regla de Simpson 1/3", funcion, a, b, precision, e=e, x0=x0)


def simpson_1_3_compuesta(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
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
    return _resolver_regla(
        "Regla de Simpson 1/3 compuesta", funcion, xs, pesos, factor, h, precision, n=n,
        a=a, b=b, e=e, x0=x0, truncation_key="simpson_1_3_compuesta"
    )


def simpson_3_8(funcion, a, b, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
    _asegurar_funcion(funcion)
    _asegurar_intervalo(a, b)

    h = (b - a) / 3.0
    xs = np.linspace(a, b, 4)
    pesos = [1, 3, 3, 1]
    factor = 3.0 * h / 8.0
    return _resolver_regla(
        "Regla de Simpson 3/8", funcion, xs, pesos, factor, h, precision,
        a=a, b=b, e=e, x0=x0, truncation_key="simpson_3_8"
    )


def simpson_3_8_compuesta(funcion, a, b, n=None, max_iter=100, tol=1e-6, precision=8, e=None, x0=None):
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
    return _resolver_regla(
        "Regla de Simpson 3/8 compuesta", funcion, xs, pesos, factor, h, precision, n=n,
        a=a, b=b, e=e, x0=x0, truncation_key="simpson_3_8_compuesta"
    )


METODOS = {
    "rectangulo_medio": {
        "nombre": "Regla del Rectangulo Medio",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": rectangulo_medio,
        "root_col": None,
    },
    "trapecio": {
        "nombre": "Regla del Trapecio",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": trapecio,
        "root_col": None,
    },
    "trapecio_compuesto": {
        "nombre": "Regla del Trapecio Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": trapecio_compuesto,
        "root_col": None,
    },
    "simpson": {
        "nombre": "Regla de Simpson",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": simpson,
        "root_col": None,
    },
    "simpson_1_3": {
        "nombre": "Regla de Simpson 1/3",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": simpson_1_3,
        "root_col": None,
    },
    "simpson_1_3_compuesta": {
        "nombre": "Regla de Simpson 1/3 Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": simpson_1_3_compuesta,
        "root_col": None,
    },
    "simpson_3_8": {
        "nombre": "Regla de Simpson 3/8",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": simpson_3_8,
        "root_col": None,
    },
    "simpson_3_8_compuesta": {
        "nombre": "Regla de Simpson 3/8 Compuesta",
        "clase": "Clase 4: Integración (Newton-Cotes)",
        "requiere": ["f_expr", "a", "b", "n"],
        "opcionales": ["e"],
        "headers": HEADERS,
        "resolver": simpson_3_8_compuesta,
        "root_col": None,
    },
}
