@echo off
REM Start Emotion Detection App - Windows Launcher
REM This script properly activates the .venv and starts the Flask app

setlocal enabledelayedexpansion
color 0A

echo.
echo ============================================================
echo         EMOTI - Emotion Detection AI Chat
echo ============================================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
REM Get the parent directory (project backup code)
set PARENT_DIR=%~dp0..

echo Script is in: %SCRIPT_DIR%
echo Parent directory: %PARENT_DIR%
echo.

cd /d "%SCRIPT_DIR%"

echo Checking virtual environment...
set VENV_PATH=%PARENT_DIR%\.venv

if not exist "%VENV_PATH%" (
    echo ERROR: Virtual environment not found at %VENV_PATH%
    echo.
    echo Please create it by running:
    echo   cd "%PARENT_DIR%"
    echo   python -m venv .venv
    pause
    exit /b 1
)

echo ✓ Virtual environment found at: %VENV_PATH%

REM Use the absolute path to Python in the virtual environment
set PYTHON_EXE=%VENV_PATH%\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo ERROR: Python executable not found at %PYTHON_EXE%
    pause
    exit /b 1
)

echo ✓ Python executable found: %PYTHON_EXE%
echo.
echo Verifying langdetect is installed...
"%PYTHON_EXE%" -c "import langdetect; print('  ✓ langdetect available')" >nul 2>&1

if errorlevel 1 (
    echo Installing langdetect...
    "%PYTHON_EXE%" -m pip install langdetect -q >nul 2>&1
)

echo.
echo ============================================================
echo Starting Flask Application...
echo ============================================================
echo.
echo Server will run on: http://127.0.0.1:5000
echo.
echo Open your browser and go to: http://127.0.0.1:5000
echo.
echo To STOP the server, press: CTRL + C
echo.
echo ============================================================
echo.

REM Start the Flask app using the virtual environment's Python directly
"%PYTHON_EXE%" app.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo ERROR: Application failed to start
    echo ============================================================
    echo.
    pause
)

endlocal
