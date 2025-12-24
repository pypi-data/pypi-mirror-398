@echo off
title ColorBridge Launcher - AI8051U Serial Assistant
color 0E

echo                    ColorBridge Launcher
echo                  AI8051U USB-CDC Serial Assistant
echo                      Version: 2.1.17
echo                      Author: 076lik
echo ================================================================
echo.

:: Check Python environment
echo [INFO] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.8 or higher
    echo [INFO] Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Display Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python version: %PYTHON_VERSION%

:: Switch to ColorBridge directory
cd /d "%~dp0"
if errorlevel 1 (
    echo [ERROR] Cannot find ColorBridge directory
    pause
    exit /b 1
)
echo [SUCCESS] Switched to ColorBridge directory: %CD%

:: Check if main.py exists (for source mode)
if not exist "main.py" (
    echo [WARNING] main.py file not found (running in pip install mode)
)

:: Check and install dependencies
echo.
echo [INFO] Checking Python dependencies...
if exist "requirements.txt" (
    echo [INFO] Found requirements.txt, checking dependencies...
    python -c "import PyQt6, serial, dateutil" >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] Missing dependencies, installing...
        pip install -r requirements.txt
        if errorlevel 1 (
            echo [ERROR] Dependency installation failed
            pause
            exit /b 1
        )
        echo [SUCCESS] Dependencies installed
    ) else (
        echo [SUCCESS] All dependencies installed
    )
) else (
    echo [WARNING] requirements.txt not found
)

:: Detect running mode (pip install mode or source mode)
echo.
echo [INFO] Detecting running mode...
set RUN_MODE=source
set RUN_COMMAND=python main.py

:: Try pip install mode first
python -c "import colorbridge; print('pip mode detected')" >nul 2>&1
if not errorlevel 1 (
    set RUN_MODE=pip
    set RUN_COMMAND=python -m colorbridge
    echo [SUCCESS] Pip install mode detected, using: %RUN_COMMAND%
) else if exist "main.py" (
    echo [SUCCESS] Source mode detected, using: %RUN_COMMAND%
) else (
    echo [ERROR] Neither pip package nor source files found
    echo [INFO] Please install ColorBridge first:
    echo [INFO]   pip install colorbridge
    echo [INFO]   or download source from https://atomgit.com/H076lik/ColorBridge
    pause
    exit /b 1
)

:: Display startup options
echo.
echo ================================================================
echo                        Startup Options
echo ================================================================
echo  Running mode: %RUN_MODE% mode (%RUN_COMMAND%)
echo.
echo  1. Normal mode startup
echo  2. Debug mode startup (show detailed logs)
echo  3. Quiet mode startup (errors only)
echo  4. Show version info
echo  5. Show help info
echo  6. Quick start (skip menu)
echo  7. Exit program
echo ================================================================
echo.

:: Get user choice
set /p choice="Please select startup mode (1-7): "

:: Execute based on choice
if "%choice%"=="1" (
    echo.
    echo [INFO] Starting ColorBridge in normal mode...
    %RUN_COMMAND%
) else if "%choice%"=="2" (
    echo.
    echo [INFO] Starting ColorBridge in debug mode...
    %RUN_COMMAND% --debug
) else if "%choice%"=="3" (
    echo.
    echo [INFO] Starting ColorBridge in quiet mode...
    %RUN_COMMAND% --quiet
) else if "%choice%"=="4" (
    echo.
    %RUN_COMMAND% --version
    echo.
    pause
) else if "%choice%"=="5" (
    echo.
    %RUN_COMMAND% --help
    echo.
    pause
) else if "%choice%"=="6" (
    echo.
    echo [INFO] Quick starting ColorBridge...
    start %RUN_COMMAND%
) else if "%choice%"=="7" (
    echo.
    echo [INFO] Program exited
    pause
    exit /b 0
) else (
    echo.
    echo [ERROR] Invalid choice, please enter 1-7
    pause
    exit /b 1
)

:: Check program exit status
if errorlevel 1 (
    echo.
    echo [WARNING] ColorBridge exited abnormally, error code: %errorlevel%
    echo [INFO] Possible reasons:
    echo [INFO] - Missing dependencies
    echo [INFO] - Serial port occupied by other programs
    echo [INFO] - Python environment issues
    echo [INFO] Please check error messages and try to resolve
) else (
    echo.
    echo [SUCCESS] ColorBridge exited normally
)

echo.
echo [INFO] Press any key to exit...
pause >nul