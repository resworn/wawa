@echo off
:loop
python wawa/main.py
timeout /t 3 >nul
goto loop
