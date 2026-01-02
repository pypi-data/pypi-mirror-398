@echo off
REM ojsTerminalBio - Run Server Script

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting ojsTerminalBio...
echo Access: http://localhost:7777
echo Press Ctrl+C to stop
echo.

ojsterminalbio runserver
