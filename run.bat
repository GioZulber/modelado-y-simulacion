@echo off
echo =====================================
echo [⚙️] Iniciando Modelado y Simulacion...
echo =====================================

cd /d "%~dp0"

IF NOT EXIST "backend\.venv" (
    echo [🐍] Creando entorno virtual de Python...
    py -m venv backend\.venv
)

echo [📦] Instalando dependencias del backend...
call backend\.venv\Scripts\activate.bat
pip install -r backend\requirements.txt

echo [📦] Instalando dependencias del frontend...
cd frontend
call npm install
cd ..

echo [🚀] Levantando servidores...
echo Nota: Se abriran dos nuevas ventanas. Para apagar los servidores, cierra esas ventanas.

start "Backend FastAPI" cmd /c "cd backend && call .venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir ."
start "Frontend React (Vite)" cmd /c "cd frontend && npm run dev"

echo [✅] Todo listo! La aplicacion se esta ejecutando en http://localhost:5173
pause
