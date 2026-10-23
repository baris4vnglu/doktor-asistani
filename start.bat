@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%OLLAMA_MODEL%"=="" set OLLAMA_MODEL=qwen2.5vl:3b

where ollama >nul 2>nul || (echo Ollama not found. Install it from https://ollama.com/download. & pause & exit /b 1)
where python >nul 2>nul || (echo Python not found. Install it from https://www.python.org/downloads/ ^(check Add to PATH^). & pause & exit /b 1)

echo [1/3] Checking model: %OLLAMA_MODEL% (first run downloads ~3 GB)
ollama pull %OLLAMA_MODEL% || (echo Could not pull model. Is the Ollama app running? & pause & exit /b 1)

echo [2/3] Installing Python packages
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt || (pause & exit /b 1)

echo [3/3] Starting app: http://localhost:8000
start "" http://localhost:8000
uvicorn backend.app:app --port 8000
pause
