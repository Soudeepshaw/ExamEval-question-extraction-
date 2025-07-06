@echo off
echo 🚀 Starting Question Paper Analyzer...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.example .env
    echo 📝 Please edit .env file and add your GEMINI_API_KEY
    pause
    exit /b 1
)

REM Run setup test
echo 🔍 Running setup verification...
python test_setup.py

if %errorlevel% equ 0 (
    echo ✅ Setup verification passed!
    echo 🌟 Starting the server...
    python -m app.main
) else (
    echo ❌ Setup verification failed. Please check the errors above.
    pause
    exit /b 1
)
