@echo off
title WAWA Auto-Restart Launcher
color 0c

echo ==========================================
echo         WAWA BOT AUTO-RESTART
echo ==========================================
echo.

call venv\Scripts\activate

:loop
echo Starting WAWA bot...
python main.py

echo.
echo Bot crashed or stopped. Restarting in 3 seconds...
timeout /t 3 >nul

goto loop
