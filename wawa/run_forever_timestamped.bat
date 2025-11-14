@echo off
title WAWA Restart With Timestamps
color 0d

call venv\Scripts\activate

:loop
echo [%date% %time%] Starting bot...
python main.py
echo [%date% %time%] Bot stopped or crashed.
echo Restarting in 3 seconds...

timeout /t 3 >nul
goto loop
