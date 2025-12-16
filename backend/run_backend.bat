@echo off
echo Starting Vibe Coding Backend Server...
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo WARNING: .env file not found!
    echo Please create .env file with your OPENAI_API_KEY
    echo Copy .env.example to .env and edit it
    echo.
)

REM Activate venv and run server
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

uvicorn app.main:app --reload

