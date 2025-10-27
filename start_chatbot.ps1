# Flask Chatbot Startup Script for PowerShell
# This script activates the conda environment and runs the Flask chatbot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🚀 QUANTUM BLUE AI CHATBOT - STARTUP SCRIPT" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Check if conda is available
try {
    $condaVersion = conda --version 2>$null
    Write-Host "✅ Conda found: $condaVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Conda not found in PATH. Please install Anaconda/Miniconda first." -ForegroundColor Red
    Write-Host "💡 Download from: https://www.anaconda.com/products/distribution" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate the highvolt conda environment
Write-Host "🔧 Activating conda environment: highvolt" -ForegroundColor Blue
try {
    conda activate highvolt
    Write-Host "✅ Environment 'highvolt' activated" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to activate conda environment 'highvolt'" -ForegroundColor Red
    Write-Host "💡 Make sure the environment exists: conda create -n highvolt python=3.9" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "run.py")) {
    Write-Host "❌ run.py not found. Please run this script from the chatbot-project directory." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if requirements are installed
Write-Host "🔍 Checking Python dependencies..." -ForegroundColor Blue
try {
    python -c "import flask" 2>$null
    Write-Host "✅ Flask is installed" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Flask not found. Installing requirements..." -ForegroundColor Yellow
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install requirements" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Check for .env file
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "💡 Created .env from example. Please edit with your configuration." -ForegroundColor Yellow
    } else {
        Write-Host "💡 Please create a .env file with your configuration" -ForegroundColor Yellow
        Write-Host "   See README.md for required environment variables" -ForegroundColor Yellow
    }
}

Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host "🌐 Starting Flask chatbot..." -ForegroundColor Blue
Write-Host "📱 The chatbot will be available at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

# Run the Flask application
try {
    python run.py
} catch {
    Write-Host ""
    Write-Host "❌ Application exited with an error" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
