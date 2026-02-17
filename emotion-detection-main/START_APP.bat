@echo off
REM EMOTI - Emotion Detection AI Chat Launcher
REM This is the DEFINITIVE working version

setlocal enabledelayedexpansion
color 0A

echo.
echo ============================================================
echo          EMOTI - Starting Emotion Detection AI Chat
echo ============================================================
echo.

REM Kill any existing Python processes
taskkill /F /IM python.exe >nul 2>&1

REM Use absolute path - this WILL work
set PYTHON_PATH=c:\project backup code\.venv\Scripts\python.exe

REM Verify Python exists
if not exist "%PYTHON_PATH%" (
    echo ERROR: Python not found at:
    echo %PYTHON_PATH%
    echo.
    echo Please ensure the virtual environment exists.
    pause
    exit /b 1
)

echo Python: %PYTHON_PATH%
echo.

REM Change to the correct directory
cd /d "c:\project backup code\emotion-detection-main"

REM Verify we're in the right place
if not exist "app.py" (
    echo ERROR: app.py not found in current directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Directory: %CD%
echo.

REM Verify langdetect can be imported
echo Checking dependencies...
"%PYTHON_PATH%" -c "import langdetect; print('  OK: langdetect available')" >nul 2>&1

if errorlevel 1 (
    echo.
    echo Installing langdetect...
    "%PYTHON_PATH%" -m pip install langdetect -q
)

echo.
echo ============================================================
echo Starting Flask Server...
echo ============================================================
echo.
echo Opening on: http://127.0.0.1:5000
echo.
echo Press CTRL+C to stop
echo.
echo ============================================================
echo.

REM Run the app
"%PYTHON_PATH%" app.py

REM If we get here, something went wrong
echo.
echo Application stopped.
echo.
pause

endlocal
