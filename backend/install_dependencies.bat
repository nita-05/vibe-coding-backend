@echo off
echo ========================================
echo Installing Vibe Coding Backend Dependencies
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    echo Please run setup_backend.bat first
    pause
    exit /b 1
)

echo Using Python 3.11 for compatibility...
echo.

REM Use Python 3.11 directly
set PYTHON311=%LOCALAPPDATA%\Programs\Python\Python311\python.exe

if not exist "%PYTHON311%" (
    echo ERROR: Python 3.11 not found!
    echo Please install Python 3.11 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Creating new virtual environment with Python 3.11...
if exist venv rmdir /s /q venv
"%PYTHON311%" -m venv venv

echo.
echo Installing pip...
call venv\Scripts\python.exe -m ensurepip --upgrade

echo.
echo Upgrading pip, setuptools, wheel...
call venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

echo.
echo Installing dependencies (this may take a few minutes)...
call venv\Scripts\python.exe -m pip install fastapi==0.104.1
call venv\Scripts\python.exe -m pip install "uvicorn[standard]==0.24.0"
call venv\Scripts\python.exe -m pip install openai==1.3.7
call venv\Scripts\python.exe -m pip install pydantic==2.5.0
call venv\Scripts\python.exe -m pip install pydantic-settings==2.1.0
call venv\Scripts\python.exe -m pip install python-dotenv==1.0.0
call venv\Scripts\python.exe -m pip install sqlalchemy==2.0.23
call venv\Scripts\python.exe -m pip install python-multipart==0.0.6
call venv\Scripts\python.exe -m pip install httpx==0.25.2
call venv\Scripts\python.exe -m pip install aiofiles==23.2.1

if errorlevel 1 (
    echo.
    echo ERROR: Failed to install some dependencies!
    echo Trying alternative installation method...
    call venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Installation failed!
        echo.
        echo Troubleshooting:
        echo 1. Make sure you're using Python 3.11 (not 3.13)
        echo 2. Try running: venv\Scripts\python.exe -m pip install --upgrade pip
        echo 3. Check your internet connection
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Dependencies installed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Create .env file with your OPENAI_API_KEY
echo 2. Run: run_backend.bat
echo.
pause

