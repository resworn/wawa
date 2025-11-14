@echo off
title WAWA Bot Setup
color 0a

echo ==========================================
echo        WAWA BOT INSTALLER (Windows)
echo ==========================================
echo.

REM Check Python version
echo Checking Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.12.6 (64-bit) and try again.
    pause
    exit /b
)

echo Python detected.
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
IF %ERRORLEVEL% NEQ 0 (
    echo Error creating virtual environment.
    pause
    exit /b
)

echo VENV created.
echo.

REM Activate VENV
echo Activating virtual environment...
call venv\Scripts\activate
echo VENV activated.
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install requirements
echo Installing required packages...
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR installing requirements!
    pause
    exit /b
)

echo Requirements installed successfully.
echo.

echo Starting the bot...
python main.py

echo.
pause
