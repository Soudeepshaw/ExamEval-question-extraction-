#!/usr/bin/env python3
"""
Complete setup verification script
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Tuple

def check_file_exists(file_path: str) -> bool:
    """Check if file exists"""
    return Path(file_path).exists()

def check_directory_structure() -> Tuple[bool, List[str]]:
    """Check if all required directories and files exist"""
    required_structure = [
        # Core app files
        "app/__init__.py",
        "app/main.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/core/gemini_client.py",
        "app/services/__init__.py",
        "app/services/pdf_analyzer.py",
        "app/services/question_classifier.py",
        "app/models/__init__.py",
        "app/models/schemas.py",
        "app/api/__init__.py",
        "app/api/endpoints.py",
        "app/utils/__init__.py",
        "app/utils/logger.py",
        "app/utils/helpers.py",
        
        # Data files
        "data/question_types.json",
        
        # Configuration files
        "requirements.txt",
        ".env.example",
        
        # Documentation
        "README.md",
        "SETUP.md",
        
        # Scripts
        "test_setup.py",
        "example_usage.py",
        "verify_complete_setup.py",
        "start.sh",
        "start.bat",
        
        # Docker files
        "Dockerfile",
        "docker-compose.yml",
        
        # Test files
        "tests/__init__.py",
        "tests/test_api.py"
    ]
    
    missing_files = []
    for file_path in required_structure:
        if not check_file_exists(file_path):
            missing_files.append(file_path)
    
    return len(missing_files) == 0, missing_files

def check_json_files() -> Tuple[bool, List[str]]:
    """Check if JSON files are valid"""
    json_files = ["data/question_types.json"]
    errors = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{json_file}: {str(e)}")
        except FileNotFoundError:
            errors.append(f"{json_file}: File not found")
    
    return len(errors) == 0, errors

def check_python_syntax() -> Tuple[bool, List[str]]:
    """Check Python files for syntax errors"""
    python_files = [
        "app/main.py",
        "app/core/config.py",
        "app/core/gemini_client.py",
        "app/services/pdf_analyzer.py",
        "app/services/question_classifier.py",
        "app/models/schemas.py",
        "app/api/endpoints.py",
        "app/utils/logger.py",
        "app/utils/helpers.py",
        "test_setup.py",
        "example_usage.py"
    ]
    
    errors = []
    for py_file in python_files:
        if check_file_exists(py_file):
            try:
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
            except SyntaxError as e:
                errors.append(f"{py_file}: Line {e.lineno}: {e.msg}")
            except Exception as e:
                errors.append(f"{py_file}: {str(e)}")
    
    return len(errors) == 0, errors

def check_requirements() -> Tuple[bool, List[str]]:
    """Check if requirements.txt is valid"""
    try:
        with open("requirements.txt", 'r') as f:
            lines = f.readlines()
        
        required_packages = [
            "fastapi",
            "uvicorn",
            "python-multipart",
            "google-generativeai",
            "pydantic",
            "python-dotenv",
            "aiofiles",
            "loguru",
            "tenacity"
        ]
        
        content = ''.join(lines).lower()
        missing_packages = []
        
        for package in required_packages:
            if package.lower() not in content:
                missing_packages.append(package)
        
        return len(missing_packages) == 0, missing_packages
        
    except FileNotFoundError:
        return False, ["requirements.txt not found"]

def check_executable_permissions() -> Tuple[bool, List[str]]:
    """Check if shell scripts have executable permissions"""
    if os.name == 'posix':  # Unix-like systems
        script_files = ["start.sh"]
        non_executable = []
        
        for script in script_files:
            if check_file_exists(script):
                if not os.access(script, os.X_OK):
                    non_executable.append(script)
        
        return len(non_executable) == 0, non_executable
    
    return True, []  # Skip on Windows

def main():
    """Run complete verification"""
    print("🔍 Complete Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("JSON Files", check_json_files),
        ("Python Syntax", check_python_syntax),
        ("Requirements", check_requirements),
        ("Executable Permissions", check_executable_permissions)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        try:
            passed, errors = check_func()
            if passed:
                print(f"   ✅ Passed")
            else:
                print(f"   ❌ Failed")
                for error in errors:
                    print(f"      - {error}")
                all_passed = False
        except Exception as e:
            print(f"   ❌ Error during check: {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULT:")
    
    if all_passed:
        print("✅ All checks passed! Your setup is complete.")
        print("\n🚀 Next steps:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your GEMINI_API_KEY to .env")
        print("   3. Run: python -m app.main")
        print("   4. Test: python example_usage.py")
        print("\n📖 Documentation:")
        print("   - API docs: http://localhost:8000/docs")
        print("   - Setup guide: SETUP.md")
        print("   - Main docs: README.md")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("   - Run: pip install -r requirements.txt")
        print("   - Check file permissions: chmod +x start.sh")
        print("   - Verify JSON syntax in data files")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
