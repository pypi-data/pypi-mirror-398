@echo off
REM ojsTerminalBio Setup Script for Windows

echo ==========================================
echo   ojsTerminalBio Setup
echo ==========================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo X Python not found. Please install Python 3.10+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python found

REM Create virtual environment
echo.
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

REM Install package
echo.
echo Installing ojsTerminalBio...
pip install --upgrade pip
pip install ojsterminalbio

REM Initialize database
echo.
echo Initializing database...
ojsterminalbio init-db

REM Done
echo.
echo ==========================================
echo   Setup Complete!
echo ==========================================
echo.
echo To start the server:
echo   venv\Scripts\activate
echo   ojsterminalbio runserver
echo.
echo Access: http://localhost:7777
echo Login:  admin@example.com / admin123
echo.
pause
