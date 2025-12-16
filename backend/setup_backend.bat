@echo off
echo Setting up Vibe Coding Backend...
echo.

REM Find Python installation - Prefer Python 3.11 for compatibility
set PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python311\python.exe

REM Check if Python 3.11 exists, if not try Python 3.13
if not exist "%PYTHON_PATH%" (
    set PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python313\python.exe
    echo WARNING: Using Python 3.13 - may require Rust for some packages
)

if not exist "%PYTHON_PATH%" (
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Found Python: %PYTHON_PATH%
%PYTHON_PATH% --version
echo.

REM Create virtual environment
echo Creating virtual environment...
%PYTHON_PATH% -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment!
    pause
    exit /b 1
)

echo.
echo Installing pip...
call venv\Scripts\python.exe -m ensurepip --upgrade

echo.
echo Upgrading pip, setuptools, wheel...
call venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

echo.
echo Installing dependencies (this may take a few minutes)...
call venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Backend setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create a .env file in the backend directory
echo 2. Add your OPENAI_API_KEY to .env
echo 3. Run: venv\Scripts\activate
echo 4. Run: uvicorn app.main:app --reload
echo.
pause

