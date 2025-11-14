@echo off
title WAWA Auto-Restart + Crash Logger
color 0e

call venv\Scripts\activate

if not exist logs mkdir logs

:loop
echo Starting WAWA bot...
python main.py

echo [%date% %time%] Bot crashed or stopped. >> logs/wawa_crash.log
echo Restarting in 3 seconds... >> logs/wawa_crash.log

timeout /t 3 >nul
goto loop
