#!/usr/bin/env python3
"""
Simple test script to verify the setup is working correctly
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    try:
        import fastapi
        import uvicorn
        import google.generativeai as genai
        import pydantic
        import loguru
        import tenacity
        import aiofiles
        print("✅ All required packages imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/gemini_client.py",
        "app/services/pdf_analyzer.py",
        "app/services/question_classifier.py",
        "app/models/schemas.py",
        "app/api/endpoints.py",
        "app/utils/logger.py",
        "data/question_types.json",
        "requirements.txt"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_env_setup():
    """Test environment setup"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found. Copy .env.example to .env and add your GEMINI_API_KEY")
        return False
    
    # Try to load environment
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            print("⚠️  GEMINI_API_KEY not found in .env file")
            return False
        
        print("✅ Environment configuration looks good")
        return True
    except Exception as e:
        print(f"❌ Environment setup error: {e}")
        return False

def test_question_types():
    """Test question types loading"""
    try:
        import json
        with open("data/question_types.json", 'r') as f:
            data = json.load(f)
        
        if "question_types" not in data:
            print("❌ Invalid question_types.json format")
            return False
        
        print(f"✅ Question types loaded successfully ({len(data['question_types'])} types)")
        return True
    except Exception as e:
        print(f"❌ Question types loading error: {e}")
        return False

def test_app_startup():
    """Test if the app can start without errors"""
    try:
        # Add current directory to Python path
        sys.path.insert(0, str(Path.cwd()))
        
        from app.core.config import settings
        from app.services.question_classifier import question_classifier
        
        print("✅ App modules loaded successfully")
        print(f"   - Max file size: {settings.MAX_FILE_SIZE_MB}MB")
        print(f"   - Gemini model: {settings.GEMINI_MODEL}")
        print(f"   - Question types: {len(question_classifier.question_types['question_types'])}")
        
        return True
    except Exception as e:
        print(f"❌ App startup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing Question Paper Analyzer Setup\n")
    
    tests = [
        ("Package Imports", test_imports),
        ("File Structure", test_file_structure),
        ("Environment Setup", test_env_setup),
        ("Question Types", test_question_types),
        ("App Startup", test_app_startup)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append(result)
    
    print("\n" + "="*50)
    print("📊 SUMMARY:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        print("\n🚀 Your setup is ready! You can now start the server with:")
        print("   python -m app.main")
        print("\n📖 API docs will be available at: http://localhost:8000/docs")
    else:
        print(f"❌ {total - passed} test(s) failed ({passed}/{total} passed)")
        print("\n🔧 Please fix the issues above before running the application.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
