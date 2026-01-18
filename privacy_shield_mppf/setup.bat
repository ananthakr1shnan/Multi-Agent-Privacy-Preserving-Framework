@echo off
REM MPPF Quick Setup Script
REM Run this to complete the installation

echo ========================================
echo MPPF Setup Script
echo ========================================
echo.

echo Step 1: Installing Python package upgrades...
pip install --upgrade pydantic typing-extensions
echo.

echo Step 2: Attempting to download spaCy model...
python -m spacy download en_core_web_sm
echo.

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: spaCy model download failed.
    echo The system will still work with limited PERSON/ORG detection.
    echo.
)

echo Step 3: Checking if GROQ_API_KEY is set...
findstr /C:"GROQ_API_KEY=your_groq_api_key_here" .env >nul
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ACTION REQUIRED!
    echo ========================================
    echo Please edit .env file and add your GROQ API key.
    echo Get your key from: https://console.groq.com/
    echo.
    echo Open .env and replace:
    echo   GROQ_API_KEY=your_groq_api_key_here
    echo.
    echo with your actual API key.
    echo ========================================
    pause
)

echo.
echo Setup complete!
echo.
echo To start the server, run:
echo   python -m app.main
echo.
echo Or:
echo   uvicorn app.main:app --reload
echo.
echo Then navigate to: http://localhost:8000
echo.
pause
