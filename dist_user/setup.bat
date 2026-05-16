@echo off
title Cipher 43 Tool - Setup
cd /d "%~dp0"

echo ============================================
echo   Cipher 43 Tool - First Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chua duoc cai dat.
    echo Tai Python 3.11+ tai: https://www.python.org/downloads/
    echo Nho tick "Add Python to PATH" khi cai.
    pause
    exit /b 1
)

echo [OK] Python da san sang.

:: Create venv
if not exist "venv\" (
    echo.
    echo [1/2] Tao virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Khong tao duoc venv.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment da tao.
) else (
    echo [OK] Virtual environment da ton tai.
)

:: Install packages
echo.
echo [2/2] Cai dat packages (co the mat 1-2 phut)...
venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Cai dat packages that bai.
    pause
    exit /b 1
)

echo [OK] Packages da cai xong.
echo.
echo ============================================
echo   Setup hoan tat! Chay start.bat de bat dau.
echo ============================================
echo.
pause
