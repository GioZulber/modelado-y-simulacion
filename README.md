# Modelado y Simulación - Métodos Numéricos

Aplicación web interactiva para la resolución y visualización de métodos numéricos. 
Reconstruida con una arquitectura moderna para garantizar un entorno escalable, eficiente y fácil de mantener.

## 🚀 Arquitectura del Proyecto

El proyecto está dividido en dos partes principales:

1. **Backend (Python + FastAPI):**
   * Se encarga de toda la lógica matemática pesada.
   * Utiliza **NumPy** para cálculos numéricos eficientes y **SymPy** para el análisis simbólico de funciones (parseo seguro, cálculo de derivadas automáticas, etc.).
   * Arquitectura "Plug & Play" en la carpeta `backend/metodos/`. Cada vez que agregues un nuevo método, la API lo detectará y el frontend se actualizará automáticamente sin tener que tocar código de UI.
2. **Frontend (React + Vite + TypeScript):**
   * Interfaz gráfica dinámica y rápida.
   * Dibuja los formularios (entradas de datos como $a$, $b$, $x_0$, $f(x)$) dinámicamente según lo que requiera cada método.
   * Gráficos interactivos generados con **Plotly.js** y renderizado de fórmulas matemáticas con **KaTeX**.

---

## 💻 Instalación y Ejecución Rápida

La forma más sencilla de ejecutar ambos servidores simultáneamente (y con recarga automática de cambios) es utilizando el script maestro:

### Prerrequisitos
* **Python 3.10+**
* **Node.js** y **npm** (para el frontend en React)

### Comando Mágico (macOS / Linux)
Abre la terminal en la raíz del proyecto y ejecuta:

```bash
chmod +x run.sh
./run.sh
```

**¿Qué hace este script?**
1. Crea un entorno virtual (`.venv`) en la carpeta del backend si no existe.
2. Instala las dependencias de Python (`fastapi`, `numpy`, `sympy`, etc.).
3. Instala los paquetes de React en la carpeta `frontend/`.
4. Levanta FastAPI en el **puerto 8000** en segundo plano (con File Watcher optimizado para no consumir CPU extra).
5. Levanta el frontend de Vite en el **puerto 5173**.

👉 Abre tu navegador web en: **[http://localhost:5173](http://localhost:5173)**

Para apagar ambos servidores, simplemente presiona `Ctrl + C` en la misma terminal.

---

## 👨‍🏫 Flujo de Trabajo (Para la clase de los jueves)

El sistema está diseñado para que agregar nuevos métodos sea extremadamente fácil. 
No necesitas tocar *absolutamente nada* de HTML, CSS o React.

### Cómo agregar un nuevo método:

1. Ve a la carpeta `backend/metodos/` y abre (o crea) tu archivo, por ejemplo `clase3.py`.
2. Programa la matemática de tu método (asegúrate de devolver las `iteraciones` y un mensaje final).
3. Añádelo al diccionario `METODOS` al final del archivo. Especifica qué inputs necesita en la lista `requiere`:

```python
METODOS = {
    "nuevo_metodo": {
        "nombre": "Mi Nuevo Método",
        "clase": "Clase 3",
        "requiere": ["f_expr", "x0", "x1"], # ¡El Frontend dibujará automáticamente estas cajitas!
        "headers": ["Iter", "x0", "x1", "Error"],
        "resolver": mi_funcion_nativa_de_python,
        "root_col": 2, # La columna del arreglo que contiene la raíz para graficarla
    }
}
```

4. **¡Listo!** Guarda el archivo. El backend se recargará automáticamente y al refrescar el navegador, el método ya estará disponible con su interfaz gráfica perfecta.

---

## 🛠 Ejecución Manual (Opcional)

Si prefieres levantar los servicios por separado en distintas pestañas de la terminal:

**1. Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir .
```

**2. Frontend:**
```bash
cd frontend
npm install
npm run dev
```
