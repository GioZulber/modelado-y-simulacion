MARCOS_TEORICOS = {
    "biseccion": {
        "titulo": "Metodo de Biseccion",
        "resumen": "Metodo cerrado para aproximar una raiz usando un intervalo donde la funcion cambia de signo.",
        "formulas": [
            {
                "etiqueta": "Punto medio",
                "latex": r"c_k = \frac{a_k + b_k}{2}",
                "detalle": "En cada iteracion se toma el punto medio del intervalo actual.",
            },
            {
                "etiqueta": "Seleccion del subintervalo",
                "latex": r"\begin{aligned} f(a_k)f(c_k) &< 0 \\ b_{k+1} &= c_k,\quad a_{k+1}=a_k \end{aligned}",
                "detalle": "Si hay cambio de signo entre a y c, la raiz queda en ese tramo; si no, queda entre c y b.",
            },
            {
                "etiqueta": "Cota de error",
                "latex": r"E_k \leq \frac{b_k-a_k}{2}",
                "detalle": "El error maximo se reduce a la mitad en cada iteracion.",
            },
        ],
        "pasos": [
            "Verificar que f(a) y f(b) tengan signos opuestos.",
            "Calcular el punto medio c.",
            "Evaluar f(c) y decidir que mitad del intervalo conserva el cambio de signo.",
            "Repetir hasta que |f(c)| o el tamano del intervalo sea menor que la tolerancia.",
        ],
        "condiciones": [
            "f debe ser continua en [a,b].",
            "Debe cumplirse f(a)f(b) < 0.",
            "Converge siempre bajo esas condiciones, aunque puede hacerlo lentamente.",
        ],
    },
    "punto_fijo": {
        "titulo": "Metodo de Punto Fijo",
        "resumen": "Reescribe el problema f(x)=0 como x=g(x) y genera una sucesion iterativa.",
        "formulas": [
            {
                "etiqueta": "Iteracion",
                "latex": r"x_{k+1} = g(x_k)",
                "detalle": "Cada aproximacion nueva se obtiene evaluando la funcion de iteracion g.",
            },
            {
                "etiqueta": "Error absoluto",
                "latex": r"E_k = |x_{k+1}-x_k|",
                "detalle": "La implementacion detiene el proceso cuando este error cae bajo la tolerancia.",
            },
            {
                "etiqueta": "Criterio local de convergencia",
                "latex": r"|g'(x)| < 1",
                "detalle": "Cerca del punto fijo, esta condicion favorece la convergencia.",
            },
        ],
        "pasos": [
            "Elegir una funcion g(x) equivalente al problema original.",
            "Partir de un valor inicial x0.",
            "Calcular x1 = g(x0) y medir la diferencia con x0.",
            "Usar x1 como nuevo valor inicial hasta cumplir la tolerancia.",
        ],
        "condiciones": [
            "La eleccion de g(x) es clave: distintas formas pueden converger o divergir.",
            "Conviene que |g'(x)| sea menor que 1 cerca de la solucion.",
        ],
    },
    "aitken": {
        "titulo": "Aceleracion de Aitken Delta Cuadrado",
        "resumen": "Acelera una sucesion de punto fijo cuando la convergencia es aproximadamente lineal.",
        "formulas": [
            {
                "etiqueta": "Tres aproximaciones",
                "latex": r"x_1=g(x_0),\quad x_2=g(x_1)",
                "detalle": "Se generan dos pasos ordinarios de punto fijo desde el valor actual.",
            },
            {
                "etiqueta": "Aitken",
                "latex": r"\begin{aligned} \hat{x} &= x_0-\frac{(x_1-x_0)^2}{x_2-2x_1+x_0} \end{aligned}",
                "detalle": "La nueva aproximacion extrapola la sucesion para acercarse mas rapido al limite.",
            },
            {
                "etiqueta": "Error absoluto",
                "latex": r"E_k = |\hat{x}_k-x_k|",
                "detalle": "Se usa para decidir si la aproximacion acelerada ya es suficiente.",
            },
        ],
        "pasos": [
            "Partir de x0 y calcular x1 = g(x0).",
            "Calcular x2 = g(x1).",
            "Aplicar la formula de Aitken para obtener una aproximacion acelerada.",
            "Repetir usando la aproximacion acelerada como nuevo punto.",
        ],
        "condiciones": [
            "El denominador x2 - 2x1 + x0 no puede ser cero.",
            "Funciona mejor cuando la iteracion de punto fijo ya converge, pero lentamente.",
        ],
    },
    "newton_raphson": {
        "titulo": "Metodo de Newton-Raphson",
        "resumen": "Metodo abierto que aproxima una raiz usando la recta tangente a la funcion.",
        "formulas": [
            {
                "etiqueta": "Formula iterativa",
                "latex": r"x_{k+1}=x_k-\frac{f(x_k)}{f'(x_k)}",
                "detalle": "El siguiente valor es el corte con el eje x de la tangente en x_k.",
            },
            {
                "etiqueta": "Derivada numerica centrada",
                "latex": r"f'(x_k)\approx \frac{f(x_k+h)-f(x_k-h)}{2h}",
                "detalle": "La implementacion estima la derivada numericamente cuando solo se ingresa f(x).",
            },
            {
                "etiqueta": "Error absoluto",
                "latex": r"E_k=|x_{k+1}-x_k|",
                "detalle": "El proceso se detiene cuando el cambio entre aproximaciones es pequeno.",
            },
        ],
        "pasos": [
            "Elegir un valor inicial x0 cercano a la raiz esperada.",
            "Evaluar f(xk) y aproximar f'(xk).",
            "Aplicar la formula de Newton-Raphson.",
            "Repetir hasta cumplir la tolerancia o llegar al maximo de iteraciones.",
        ],
        "condiciones": [
            "f'(xk) no debe ser cero.",
            "La convergencia depende mucho del valor inicial.",
            "Si el punto inicial esta cerca de una raiz simple, suele converger rapidamente.",
        ],
    },
    "lagrange": {
        "titulo": "Interpolacion de Lagrange",
        "resumen": "Construye un polinomio que pasa exactamente por los puntos dados usando bases de Lagrange.",
        "formulas": [
            {
                "etiqueta": "Polinomio interpolador",
                "latex": r"P_n(x)=\sum_{i=0}^{n} y_i L_i(x)",
                "detalle": "El polinomio se arma como suma ponderada de las bases.",
            },
            {
                "etiqueta": "Base de Lagrange",
                "latex": r"\begin{aligned} L_i(x) &= \prod_{\substack{j=0\\j\neq i}}^{n}\frac{x-x_j}{x_i-x_j} \end{aligned}",
                "detalle": "Cada base vale 1 en su nodo y 0 en los demas nodos.",
            },
            {
                "etiqueta": "Error teorico",
                "latex": r"\begin{aligned} E(x) &= \frac{f^{(n+1)}(\xi)}{(n+1)!}\\ &\quad \prod_{i=0}^{n}(x-x_i) \end{aligned}",
                "detalle": "Si se conoce f, esta expresion permite estimar el error de interpolacion.",
            },
        ],
        "pasos": [
            "Ingresar los nodos x_data y sus valores y_data.",
            "Construir cada base L_i(x).",
            "Multiplicar cada base por su valor y_i.",
            "Sumar todos los terminos y simplificar el polinomio.",
        ],
        "condiciones": [
            "Los valores de x_data no pueden repetirse.",
            "Debe haber la misma cantidad de x_data e y_data.",
        ],
    },
    "newton_dif_div": {
        "titulo": "Interpolacion de Newton por Diferencias Divididas",
        "resumen": "Construye el polinomio interpolador usando coeficientes obtenidos por diferencias divididas.",
        "formulas": [
            {
                "etiqueta": "Diferencia dividida",
                "latex": r"\begin{aligned} f[x_i,\ldots,x_{i+j}] &= \frac{f[x_{i+1},\ldots,x_{i+j}]-f[x_i,\ldots,x_{i+j-1}]}{x_{i+j}-x_i} \end{aligned}",
                "detalle": "Estos valores forman la tabla triangular de coeficientes.",
            },
            {
                "etiqueta": "Polinomio de Newton",
                "latex": r"\begin{aligned} P_n(x) &= f[x_0]+\sum_{k=1}^{n} f[x_0,\ldots,x_k]\\ &\quad \prod_{j=0}^{k-1}(x-x_j) \end{aligned}",
                "detalle": "Los coeficientes usados son los de la primera fila de la tabla.",
            },
            {
                "etiqueta": "Error teorico",
                "latex": r"\begin{aligned} E(x) &= \frac{f^{(n+1)}(\xi)}{(n+1)!}\\ &\quad \prod_{i=0}^{n}(x-x_i) \end{aligned}",
                "detalle": "Comparte la misma forma del error de interpolacion polinomial.",
            },
        ],
        "pasos": [
            "Ingresar los nodos y sus valores.",
            "Armar la tabla de diferencias divididas.",
            "Tomar los coeficientes de la primera fila.",
            "Construir el polinomio agregando factores (x-x0), (x-x1), etc.",
        ],
        "condiciones": [
            "Los nodos x deben ser distintos.",
            "Agregar un nuevo nodo permite extender el polinomio sin recomenzar desde cero.",
        ],
    },
    "rectangulo_medio": {
        "titulo": "Regla del Rectangulo Medio",
        "resumen": "Aproxima una integral definida evaluando la funcion en el punto medio de cada subintervalo.",
        "formulas": [
            {
                "etiqueta": "Ancho de subintervalo",
                "latex": r"h=\frac{b-a}{n}",
                "detalle": "El intervalo se divide en n partes de igual longitud.",
            },
            {
                "etiqueta": "Puntos medios",
                "latex": r"\begin{aligned} x_i^* &= a+\left(i+\frac{1}{2}\right)h\\ i &= 0,\ldots,n-1 \end{aligned}",
                "detalle": "La funcion se evalua en el centro de cada subintervalo.",
            },
            {
                "etiqueta": "Aproximacion",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx h\sum_{i=0}^{n-1} f(x_i^*) \end{aligned}",
                "detalle": "Cada rectangulo tiene base h y altura f(x_i^*).",
            },
        ],
        "pasos": [
            "Elegir a, b y la cantidad de subintervalos n.",
            "Calcular h.",
            "Calcular el punto medio de cada subintervalo.",
            "Sumar las evaluaciones f(x_i*) y multiplicar por h.",
        ],
        "condiciones": [
            "n debe ser mayor o igual a 1.",
            "La funcion debe poder evaluarse en todos los puntos medios.",
        ],
    },
    "trapecio": {
        "titulo": "Regla del Trapecio",
        "resumen": "Aproxima el area bajo la curva con un trapecio sobre todo el intervalo.",
        "formulas": [
            {
                "etiqueta": "Ancho",
                "latex": r"h=b-a",
                "detalle": "Para la regla simple se usa un solo intervalo.",
            },
            {
                "etiqueta": "Aproximacion",
                "latex": r"\int_a^b f(x)\,dx \approx \frac{h}{2}\left[f(a)+f(b)\right]",
                "detalle": "Promedia las alturas de los extremos y multiplica por la base.",
            },
        ],
        "pasos": [
            "Evaluar f(a) y f(b).",
            "Sumar ambas alturas.",
            "Multiplicar por (b-a)/2.",
        ],
        "condiciones": [
            "El intervalo no puede tener longitud cero.",
            "Es exacta para funciones lineales.",
        ],
    },
    "trapecio_compuesto": {
        "titulo": "Regla del Trapecio Compuesta",
        "resumen": "Divide el intervalo en subintervalos y aplica la regla del trapecio en cada uno.",
        "formulas": [
            {
                "etiqueta": "Ancho",
                "latex": r"h=\frac{b-a}{n}",
                "detalle": "Todos los subintervalos tienen el mismo ancho.",
            },
            {
                "etiqueta": "Aproximacion compuesta",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{h}{2}\Big[f(x_0)\\ &\quad +2\sum_{i=1}^{n-1}f(x_i)+f(x_n)\Big] \end{aligned}",
                "detalle": "Los nodos interiores pesan 2 porque pertenecen a dos trapecios.",
            },
        ],
        "pasos": [
            "Dividir [a,b] en n subintervalos.",
            "Evaluar f en todos los nodos.",
            "Aplicar peso 1 a los extremos y peso 2 a los interiores.",
            "Multiplicar la sumatoria ponderada por h/2.",
        ],
        "condiciones": [
            "n debe ser mayor o igual a 1.",
            "Mejora al aumentar n para funciones suficientemente suaves.",
        ],
    },
    "simpson": {
        "titulo": "Regla de Simpson",
        "resumen": "Aproxima la integral usando un polinomio cuadratico que interpola tres puntos.",
        "formulas": [
            {
                "etiqueta": "Paso",
                "latex": r"h=\frac{b-a}{2}",
                "detalle": "La regla simple usa los extremos y el punto medio.",
            },
            {
                "etiqueta": "Aproximacion",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{h}{3}\left[f(a)+4f(a+h)+f(b)\right] \end{aligned}",
                "detalle": "El punto medio recibe peso 4.",
            },
        ],
        "pasos": [
            "Calcular el punto medio del intervalo.",
            "Evaluar la funcion en a, en el punto medio y en b.",
            "Aplicar pesos 1, 4 y 1.",
            "Multiplicar por h/3.",
        ],
        "condiciones": [
            "Es exacta para polinomios de grado menor o igual a 3.",
            "Requiere que la funcion sea evaluable en los tres nodos.",
        ],
    },
    "simpson_1_3": {
        "titulo": "Regla de Simpson 1/3",
        "resumen": "Caso simple de Simpson basado en interpolacion cuadratica.",
        "formulas": [
            {
                "etiqueta": "Paso",
                "latex": r"h=\frac{b-a}{2}",
                "detalle": "Se forman dos subintervalos de igual longitud.",
            },
            {
                "etiqueta": "Aproximacion",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{h}{3}\left[f(x_0)+4f(x_1)+f(x_2)\right] \end{aligned}",
                "detalle": "Los pesos caracteristicos son 1, 4, 1.",
            },
        ],
        "pasos": [
            "Tomar x0=a, x1=a+h y x2=b.",
            "Evaluar la funcion en los tres nodos.",
            "Aplicar pesos 1, 4 y 1.",
            "Multiplicar la sumatoria por h/3.",
        ],
        "condiciones": [
            "Es una formula cerrada de Newton-Cotes.",
            "Es exacta para polinomios hasta grado 3.",
        ],
    },
    "simpson_1_3_compuesta": {
        "titulo": "Regla de Simpson 1/3 Compuesta",
        "resumen": "Aplica Simpson 1/3 en varios pares de subintervalos.",
        "formulas": [
            {
                "etiqueta": "Ancho",
                "latex": r"h=\frac{b-a}{n}",
                "detalle": "n debe permitir formar pares de subintervalos.",
            },
            {
                "etiqueta": "Aproximacion compuesta",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{h}{3}\Big[f(x_0)\\ &\quad +4\sum_{\substack{1\le i\le n-1\\i\ \text{impar}}}f(x_i)\\ &\quad +2\sum_{\substack{2\le i\le n-2\\i\ \text{par}}}f(x_i)+f(x_n)\Big] \end{aligned}",
                "detalle": "Los indices impares pesan 4 y los pares interiores pesan 2.",
            },
        ],
        "pasos": [
            "Elegir n par y calcular h.",
            "Evaluar f en todos los nodos.",
            "Aplicar peso 1 a extremos, 4 a indices impares y 2 a pares interiores.",
            "Multiplicar por h/3.",
        ],
        "condiciones": [
            "n debe ser par.",
            "La funcion debe ser suave en el intervalo para obtener buena precision.",
        ],
    },
    "simpson_3_8": {
        "titulo": "Regla de Simpson 3/8",
        "resumen": "Formula cerrada de Newton-Cotes que usa cuatro puntos y un polinomio cubico.",
        "formulas": [
            {
                "etiqueta": "Paso",
                "latex": r"h=\frac{b-a}{3}",
                "detalle": "El intervalo se divide en tres subintervalos.",
            },
            {
                "etiqueta": "Aproximacion",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{3h}{8}\left[f(x_0)+3f(x_1)+3f(x_2)+f(x_3)\right] \end{aligned}",
                "detalle": "Los pesos son 1, 3, 3 y 1.",
            },
        ],
        "pasos": [
            "Dividir [a,b] en tres subintervalos iguales.",
            "Evaluar f en los cuatro nodos.",
            "Aplicar pesos 1, 3, 3 y 1.",
            "Multiplicar por 3h/8.",
        ],
        "condiciones": [
            "Es exacta para polinomios de grado menor o igual a 3.",
            "Usa un tramo de tres subintervalos.",
        ],
    },
    "simpson_3_8_compuesta": {
        "titulo": "Regla de Simpson 3/8 Compuesta",
        "resumen": "Aplica Simpson 3/8 en bloques de tres subintervalos.",
        "formulas": [
            {
                "etiqueta": "Ancho",
                "latex": r"h=\frac{b-a}{n}",
                "detalle": "n debe ser multiplo de 3 para formar bloques completos.",
            },
            {
                "etiqueta": "Aproximacion compuesta",
                "latex": r"\begin{aligned} \int_a^b f(x)\,dx &\approx \frac{3h}{8}\Big[f(x_0)\\ &\quad +3\sum_{\substack{1\le i\le n-1\\3\nmid i}}f(x_i)\\ &\quad +2\sum_{\substack{3\le i\le n-3\\3\mid i}}f(x_i)+f(x_n)\Big] \end{aligned}",
                "detalle": "Los nodos internos multiplos de 3 pesan 2; los demas pesan 3.",
            },
        ],
        "pasos": [
            "Elegir n multiplo de 3 y calcular h.",
            "Evaluar f en todos los nodos.",
            "Aplicar peso 1 a extremos, 2 a multiplos internos de 3 y 3 al resto.",
            "Multiplicar la sumatoria ponderada por 3h/8.",
        ],
        "condiciones": [
            "n debe ser multiplo de 3.",
            "Es util cuando la cantidad de subintervalos se organiza naturalmente en bloques de tres.",
        ],
    },
    "monte_carlo_integral": {
        "titulo": "Metodo de Monte Carlo para Integrales",
        "resumen": "Aproxima integrales en una o mas dimensiones usando muestras aleatorias uniformes sobre el dominio.",
        "formulas": [
            {
                "etiqueta": "Dominio",
                "latex": r"D=[a_1,b_1]\times\cdots\times[a_d,b_d]",
                "detalle": "El dominio se define con un intervalo por variable.",
            },
            {
                "etiqueta": "Estimador",
                "latex": r"\hat I_N = V(D)\frac{1}{N}\sum_{i=1}^{N} f(U_i)",
                "detalle": "Cada U_i es un punto aleatorio uniforme en D y V(D) es el volumen del dominio.",
            },
            {
                "etiqueta": "Error estandar",
                "latex": r"SE(\hat I_N)=V(D)\frac{s_N}{\sqrt{N}}",
                "detalle": "La incertidumbre baja proporcionalmente a 1/sqrt(N).",
            },
            {
                "etiqueta": "Intervalo de confianza",
                "latex": r"\hat I \pm z_{\alpha/2}\frac{s}{\sqrt{n}}",
                "detalle": "Para un nivel de confianza C, alpha = 1 - C. En una integral sobre un dominio de volumen V(D), se usa s = V(D)s_f, donde s_f es el desvio muestral de f(U).",
            },
            {
                "etiqueta": "Relacion error-muestras",
                "latex": r"E_n \approx z_{\alpha/2}\frac{s}{\sqrt{n}}\quad\Rightarrow\quad \frac{E_2}{E_1}\approx\sqrt{\frac{n_1}{n_2}}",
                "detalle": "El error baja con la raiz cuadrada de n: para reducir el error a la mitad se necesitan aproximadamente cuatro veces mas muestras.",
            },
            {
                "etiqueta": "Muestras necesarias",
                "latex": r"n_2\approx n_1\left(\frac{E_1}{E_2}\right)^2",
                "detalle": "Si se quiere dividir el error por k, entonces hay que multiplicar la cantidad de muestras por k^2.",
            },
        ],
        "pasos": [
            "Definir las variables y los limites del dominio.",
            "Generar puntos aleatorios uniformes dentro de ese dominio.",
            "Evaluar la funcion en cada punto generado.",
            "Promediar los valores y multiplicar por el volumen del dominio.",
            "Elegir el nivel de confianza y calcular el valor critico z correspondiente.",
            "Estimar el error estandar y construir el intervalo de confianza aproximado.",
            "Para reducir el error, aumentar n: si se busca la mitad del error, usar aproximadamente 4n muestras.",
        ],
        "condiciones": [
            "La funcion debe poder evaluarse en todo el dominio indicado.",
            "El metodo es probabilistico: distintas semillas pueden dar aproximaciones levemente distintas.",
            "Aumentar n reduce el error esperado, aunque la convergencia es lenta: orden 1/sqrt(n).",
        ],
    },
    "euler_edo": {
        "titulo": "Metodo de Euler para Ecuaciones Diferenciales",
        "resumen": "Aproxima la solucion de una ecuacion diferencial ordinaria de primer orden y' = f(x,y) avanzando con la pendiente al inicio de cada paso.",
        "formulas": [
            {
                "etiqueta": "Ecuacion diferencial",
                "latex": r"y'=f(x,y),\quad y(x_0)=y_0",
                "detalle": "El metodo parte de una condicion inicial conocida.",
            },
            {
                "etiqueta": "Paso en x",
                "latex": r"x_{n+1}=x_n+h",
                "detalle": "h es el tamano de paso.",
            },
            {
                "etiqueta": "Actualizacion de Euler",
                "latex": r"y_{n+1}=y_n+h\,f(x_n,y_n)",
                "detalle": "Usa la pendiente inicial del intervalo para avanzar una recta tangente.",
            },
            {
                "etiqueta": "Error absoluto",
                "latex": r"E_n=\left|y_{\text{exacta}}(x_n)-y_n\right|",
                "detalle": "Solo se calcula si se ingresa la solucion exacta.",
            },
        ],
        "pasos": [
            "Ingresar f(x,y), x0, y0, h y n.",
            "Evaluar la pendiente f(xn,yn).",
            "Calcular yn+1 = yn + h f(xn,yn).",
            "Avanzar x al siguiente punto y repetir n pasos.",
            "Si hay solucion exacta, comparar el valor aproximado contra y exacta.",
        ],
        "condiciones": [
            "La funcion f debe poder evaluarse en los puntos generados.",
            "h no puede ser cero y n debe ser mayor o igual a 1.",
            "Euler es simple pero de bajo orden; errores grandes pueden aparecer si h es demasiado grande.",
        ],
    },
    "rk4_edo": {
        "titulo": "Runge-Kutta de Orden 4 para Ecuaciones Diferenciales",
        "resumen": "Aproxima la solucion de y' = f(x,y) combinando cuatro pendientes por paso para lograr mayor precision que Euler.",
        "formulas": [
            {
                "etiqueta": "Pendientes ponderadas",
                "latex": r"\begin{aligned} k_1&=h f(x_n,y_n)\\ k_2&=h f(x_n+\frac{h}{2},y_n+\frac{k_1}{2})\\ k_3&=h f(x_n+\frac{h}{2},y_n+\frac{k_2}{2})\\ k_4&=h f(x_n+h,y_n+k_3) \end{aligned}",
                "detalle": "Cada k ya incluye el factor h.",
            },
            {
                "etiqueta": "Actualizacion RK4",
                "latex": r"y_{n+1}=y_n+\frac{k_1+2k_2+2k_3+k_4}{6}",
                "detalle": "Promedia las pendientes con mayor peso para las estimaciones intermedias.",
            },
            {
                "etiqueta": "Paso en x",
                "latex": r"x_{n+1}=x_n+h",
                "detalle": "Se avanza la variable independiente con paso constante.",
            },
            {
                "etiqueta": "Error absoluto",
                "latex": r"E_n=\left|y_{\text{exacta}}(x_n)-y_n\right|",
                "detalle": "Solo se calcula si se ingresa la solucion exacta.",
            },
        ],
        "pasos": [
            "Ingresar f(x,y), x0, y0, h y n.",
            "Calcular k1 con la pendiente al inicio del intervalo.",
            "Calcular k2 y k3 usando puntos intermedios.",
            "Calcular k4 usando el extremo del intervalo.",
            "Actualizar y con el promedio ponderado y repetir n pasos.",
            "Si hay solucion exacta, comparar el valor aproximado contra y exacta.",
        ],
        "condiciones": [
            "La funcion f debe poder evaluarse en todos los puntos intermedios.",
            "h no puede ser cero y n debe ser mayor o igual a 1.",
            "RK4 suele ser mucho mas preciso que Euler para el mismo h, pero evalua f cuatro veces por paso.",
        ],
    },
}
