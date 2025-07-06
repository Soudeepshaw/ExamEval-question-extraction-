

# Setup Guide - Question Paper Analyzer

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Git (for cloning)

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd question_paper_analyzer
```

### 2. Get Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy the API key for the next step

### 3. Environment Setup

#### Option A: Automatic Setup (Recommended)

**Linux/Mac:**
```bash
./start.sh
```

**Windows:**
```batch
start.bat
```

#### Option B: Manual Setup

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate.bat  # Windows
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Test setup:**
```bash
python test_setup.py
```

5. **Start server:**
```bash
python -m app.main
```

### 4. Verify Installation

1. **Check server status:**
   - Open: http://localhost:8000
   - Should show welcome message

2. **Test API documentation:**
   - Open: http://localhost:8000/docs
   - Interactive API documentation

3. **Test health endpoint:**
   - GET: http://localhost:8000/api/v1/health
   - Should return: `{"status": "healthy"}`

### 5. Test with Sample PDF

```bash
python example_usage.py
```

## Docker Setup (Alternative)

### Prerequisites
- Docker and Docker Compose

### Steps

1. **Build and run:**
```bash
docker-compose up --build
```

2. **Set environment variables:**
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
docker-compose up
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Gemini API Key Issues**
   - Verify key is correct in `.env`
   - Check API key permissions
   - Ensure billing is enabled on Google Cloud

3. **Port Already in Use**
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9  # Mac/Linux
   netstat -ano | findstr :8000   # Windows
   ```

4. **File Upload Issues**
   - Check file size (max 20MB)
   - Ensure file is valid PDF
   - Check network connectivity

5. **Slow Processing**
   - Large PDFs take 30-60 seconds
   - Complex layouts may take longer
   - Check Gemini API quotas

### Debug Mode

Run with debug logging:
```bash
LOG_LEVEL=DEBUG python -m app.main
```

### Logs Location

- Console output: Real-time logs
- File logs: `logs/app.log`

## Production Deployment

### Environment Variables

```bash
# Required
GEMINI_API_KEY=your_api_key

# Optional
MAX_FILE_SIZE_MB=20
LOG_LEVEL=WARNING
```

### Using Gunicorn

```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 25M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

## API Usage Examples

### cURL Examples

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Upload PDF
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@question_paper.pdf"

# Get question types
curl http://localhost:8000/api/v1/question-types
```

### Python Client Example

```python
import requests

# Upload and analyze PDF
with open('question_paper.pdf', 'rb') as f:
    files = {'file': f}
    response = requests.post(
        'http://localhost:8000/api/v1/upload',
        files=files,
        timeout=120
    )
    
if response.status_code == 200:
    result = response.json()
    if result['success']:
        print(f"Analysis completed in {result['processing_time']:.2f}s")
        print(f"Found {result['data']['summary']['total_questions']} questions")
    else:
        print(f"Analysis failed: {result['error']}")
```

### JavaScript/Node.js Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

async function analyzePDF(filePath) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    
    try {
        const response = await axios.post(
            'http://localhost:8000/api/v1/upload',
            form,
            {
                headers: form.getHeaders(),
                timeout: 120000
            }
        );
        
        if (response.data.success) {
            console.log('Analysis successful!');
            console.log(`Processing time: ${response.data.processing_time}s`);
            console.log(`Questions found: ${response.data.data.summary.total_questions}`);
            return response.data;
        } else {
            console.error('Analysis failed:', response.data.error);
        }
    } catch (error) {
        console.error('Request failed:', error.message);
    }
}

// Usage
analyzePDF('question_paper.pdf');
```

## Performance Optimization

### Server Configuration

```python
# For production, use these settings in .env
MAX_FILE_SIZE_MB=50
LOG_LEVEL=WARNING
```

### Scaling Options

1. **Horizontal Scaling**: Run multiple instances behind load balancer
2. **Vertical Scaling**: Increase server resources
3. **Caching**: Implement Redis for repeated analyses
4. **Queue System**: Use Celery for background processing

## Security Considerations

1. **API Key Security**: Never commit API keys to version control
2. **File Validation**: System validates PDF files and size limits
3. **Rate Limiting**: Consider implementing rate limiting for production
4. **HTTPS**: Use HTTPS in production
5. **CORS**: Configure CORS origins appropriately

## Monitoring

### Health Checks

```bash
# Simple health check
curl -f http://localhost:8000/api/v1/health

# Docker health check
docker ps  # Check container health status
```

### Log Monitoring

```bash
# Follow logs in real-time
tail -f logs/app.log

# Search for errors
grep -i error logs/app.log

# Monitor file uploads
grep -i "upload" logs/app.log
```

## Support

### Getting Help

1. Check logs in `logs/app.log`
2. Run `python test_setup.py` for diagnostics
3. Verify API key and network connectivity
4. Check GitHub issues for known problems

### Reporting Issues

When reporting issues, include:
- Error messages from logs
- Python version and OS
- Steps to reproduce
- Sample PDF (if possible)

## Next Steps

After successful setup:

1. **Test with your PDFs**: Try different question paper formats
2. **Customize question types**: Edit `data/question_types.json`
3. **Integrate with your system**: Use the API in your application
4. **Monitor performance**: Check processing times and accuracy
5. **Scale as needed**: Implement load balancing for high traffic

---

For more detailed information, see the main README.md file.
```

Now let's create a final verification script to ensure everything is properly set up:

```bash
ls -la question_paper_analyzer/
```

Perfect! Let me create one final script to verify the complete setup:

```python:question_paper_analyzer/verify_complete_setup.py
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
        print("\
