# Modelado y Simulación - Métodos Numéricos

Aplicación web interactiva para la resolución y visualización de métodos numéricos utilizando **Python**, **Flask** y **NumPy**.

## 🚀 Cómo Funciona

El proyecto es una aplicación web (backend en Flask, frontend en HTML/CSS/JS) que permite a los usuarios:

1. **Seleccionar métodos numéricos**: La arquitectura es escalable. Los métodos se auto-descubren leyendo cualquier archivo que empiece con `clase` dentro del directorio `metodos/`. Cada archivo expone un diccionario `METODOS` que se registra automáticamente en la aplicación.
2. **Ingresar funciones matemáticas**: Puedes ingresar funciones $f(x)$ o expresiones para $g(x)$. El backend evalúa estas expresiones de forma segura utilizando NumPy.
3. **Calcular y Visualizar**: Al hacer clic en "Resolver", la aplicación ejecuta el método seleccionado considerando la tolerancia y criterios de parada, retornando las iteraciones y los datos necesarios para graficar la función y resaltar la raíz encontrada.

### Estructura Principal

- `app.py`: Archivo principal que levanta el servidor Flask, expone la API de resolución matemática y sirve el HTML.
- `metodos/`: Directorio que contiene los algoritmos de los diferentes métodos numéricos (por ejemplo `clase1.py`, `clase2.py`). 
- `templates/` y `static/`: Archivos para la interfaz de usuario.
- `requirements.txt`: Dependencias del entorno en Python.

---

## 💻 Instalación y Ejecución Local

Sigue los siguientes pasos para correr el proyecto en tu máquina local:

### 1. Requisitos previos
- Necesitas tener **Python 3.x** instalado en tu computadora.

### 2. Clonar el repositorio
Abre una terminal en la carpeta donde deseas guardar el proyecto y clona el repositorio (o simplemente abre la carpeta del proyecto en tu terminal si ya lo tienes).

### 3. Crear y activar un Entorno Virtual (Recomendado)
Es buena práctica instalar las dependencias dentro de un entorno virtual para no afectar otras instalaciones locales de Python.

**En macOS y Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**En OS Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 4. Instalar las dependencias
Con el entorno virtual activado, instala los requerimientos definidos en `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Iniciar la aplicación
Ejecuta el archivo principal para iniciar el servidor de desarrollo:
```bash
python app.py
```
O dale play desde Visual.

### 6. Usar la aplicación
Abre tu navegador web de preferencia y navega a la siguiente dirección: 
👉 **[http://localhost:5000](http://localhost:5000)**
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

Para detener la ejecución del servidor local, simplemente presiona `Ctrl + C` en tu terminal.
