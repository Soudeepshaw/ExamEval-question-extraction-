#!/bin/bash

# Question Paper Analyzer Startup Script

echo "🚀 Starting Question Paper Analyzer..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file and add your GEMINI_API_KEY"
    exit 1
fi

# Run setup test
echo "🔍 Running setup verification..."
python test_setup.py

if [ $? -eq 0 ]; then
    echo "✅ Setup verification passed!"
    echo "🌟 Starting the server..."
    python -m app.main
else
    echo "❌ Setup verification failed. Please check the errors above."
    exit 1
fi
