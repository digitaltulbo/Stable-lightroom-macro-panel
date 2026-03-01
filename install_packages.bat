@echo off
chcp 65001 > nul
title Package Installer - Studio Birthday

echo ============================================
echo   Studio Birthday - Package Install
echo ============================================
echo.

python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed.
    echo         Please install from https://www.python.org/downloads/
    echo         Check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

cd /d "%~dp0"

echo [INFO] Installing required packages...
echo.

python -m pip install --upgrade pip
pip install PySide6 pywin32 keyboard psutil pygame

echo.
if errorlevel 1 (
    echo [ERROR] Package installation failed.
    echo         Try running as Administrator.
) else (
    echo ============================================
    echo   Installation Complete!
    echo ============================================
    echo.
    echo   Double-click "run_macro_panel.bat" to start
    echo.
)

pause
