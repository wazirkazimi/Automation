@echo off
REM Quick start script for local development (Windows)

echo.
echo 🚀 Video Reel Creator - Local Development Setup
echo ==================================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

REM Check FFmpeg
echo Checking FFmpeg...
where ffmpeg >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ FFmpeg found
    ffmpeg -version | findstr /B "ffmpeg"
) else (
    echo ⚠️  FFmpeg not found. Install with:
    echo    Windows: scoop install ffmpeg
    echo    Or download from https://ffmpeg.org
)
echo.

REM Create folders
echo Creating upload/output folders...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
echo.

REM Run app
echo ✅ Setup complete!
echo.
echo 🌐 Starting app on http://localhost:5000
echo Press Ctrl+C to stop
echo.

set FLASK_ENV=development
python app.py
