#!/bin/bash
set -e

# Make sure we are in the script's directory
cd "$(dirname "$0")"

echo "====================================="
echo "⚙️ Iniciando Modelado y Simulación..."
echo "====================================="

# Check/Create Python virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "🐍 Creando entorno virtual de Python..."
    python3 -m venv backend/.venv
fi

# Activate and install backend deps
echo "📦 Instalando dependencias del backend..."
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

# Install frontend deps
echo "📦 Instalando dependencias del frontend..."
cd frontend
npm install
cd ..

# Start backend in background
echo "🚀 Levantando servidor FastAPI..."
source backend/.venv/bin/activate
cd backend
# Explicitly use uvicorn with restricted watch directory to prevent high CPU usage
uvicorn main:app --host 0.0.0.0 --port 8000 --reload --reload-dir . &
BACKEND_PID=$!
cd ..

# Start frontend
echo "🚀 Levantando servidor React (Vite)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Todo listo! La aplicación se está ejecutando."
echo "Para cerrar los servidores, presiona Ctrl+C"

# Wait for Ctrl+C to kill background processes
trap "echo 'Apagando servidores...'; kill $BACKEND_PID; kill $FRONTEND_PID; exit" INT

wait
