@echo off
title WAWA Bot Launcher
color 0b

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Starting WAWA bot...
python main.py

echo.
pause
