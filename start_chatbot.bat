@echo off
REM Flask Chatbot Startup Script for Windows
REM This script activates the conda environment and runs the Flask chatbot

echo ============================================================
echo 🚀 QUANTUM BLUE AI CHATBOT - STARTUP SCRIPT
echo ============================================================

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Conda not found in PATH. Please install Anaconda/Miniconda first.
    echo 💡 Download from: https://www.anaconda.com/products/distribution
    pause
    exit /b 1
)

REM Activate the highvolt conda environment
echo 🔧 Activating conda environment: highvolt
call conda activate highvolt
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Failed to activate conda environment 'highvolt'
    echo 💡 Make sure the environment exists: conda create -n highvolt python=3.9
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "run.py" (
    echo ❌ run.py not found. Please run this script from the chatbot-project directory.
    pause
    exit /b 1
)

REM Check if requirements are installed
echo 🔍 Checking Python dependencies...
python -c "import flask" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Flask not found. Installing requirements...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to install requirements
        pause
        exit /b 1
    )
)

REM Check for .env file
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from example...
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo 💡 Please edit .env file with your configuration
    ) else (
        echo 💡 Please create a .env file with your configuration
        echo    See README.md for required environment variables
    )
)

echo ✅ Environment ready!
echo 🌐 Starting Flask chatbot...
echo 📱 The chatbot will be available at: http://localhost:5000
echo 🛑 Press Ctrl+C to stop the server
echo ============================================================

REM Run the Flask application
python run.py

REM Keep window open if there's an error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Application exited with error code %ERRORLEVEL%
    pause
)
