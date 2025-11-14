@echo off
title Add WAWA Bot To Startup

set shortcut="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\wawa_startup.vbs"

echo Creating startup entry...

echo Set WshShell = CreateObject("WScript.Shell") > %shortcut%
echo WshShell.Run chr(34^) ^& "%~dp0run_forever.bat" ^& chr(34^), 0 >> %shortcut%
echo Set WshShell = Nothing >> %shortcut%

echo Done! WAWA will now auto-start with Windows.
pause
