@echo off
title Cipher 43 Tool
cd /d "%~dp0"

:: Check venv exists
if not exist "venv\" (
    echo [ERROR] Chua chay setup.bat. Hay chay setup.bat truoc.
    pause
    exit /b 1
)

echo Dang khoi dong Cipher 43 Tool...
venv\Scripts\python.exe launcher.py
