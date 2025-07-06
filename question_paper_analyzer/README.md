# Enhanced Question Paper Analyzer v2.0

Advanced AI-powered question paper analysis system with comprehensive content extraction capabilities using Google's Gemini AI.

## 🚀 Features

### Core Capabilities
- **Structure Analysis**: Extract question paper structure, sections, and question types
- **Content Extraction**: Complete question text, images, diagrams, and multimedia content
- **Multi-format Support**: Handle various question types (MCQ, essays, case studies, etc.)
- **Image Description**: AI-powered description of images, diagrams, and charts
- **Formula Extraction**: Mathematical formulas and equations preservation
- **Table Processing**: Structured extraction of tabular data
- **Optional Logic Detection**: Identify optional questions and choice patterns
- **Marks Allocation**: Extract marks and time allocation information

### Enhanced Features (v2.0)
- **Two-Stage Processing**: Separate structure and content extraction for better accuracy
- **Comprehensive Content Types**: Support for code snippets, case studies, comprehension passages
- **Advanced Validation**: Robust data validation with Pydantic models
- **Error Recovery**: Intelligent JSON parsing with fallback mechanisms
- **Performance Monitoring**: Detailed timing and performance metrics
- **Backward Compatibility**: Maintains compatibility with v1.0 API

## 📋 Requirements

- Python 3.8+
- Google Gemini API Key
- FastAPI
- Uvicorn
- Google GenerativeAI
- Pydantic v2
- Other dependencies (see requirements.txt)

## 🛠 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd question_paper_analyzer
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up configuration**
```bash
python update_config.py
```

4. **Configure API key**
Create a `.env` file with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-pro
ENABLE_ENHANCED_EXTRACTION=true
MAX_FILE_SIZE_MB=20
LOG_LEVEL=INFO
```

## 🚀 Quick Start

1. **Start the server**
```bash
python -m app.main
```

2. **Test the API**
```bash
# Basic health check
curl http://localhost:8000/api/v1/health

# Run comprehensive tests
python test_enhanced_api.py path/to/your/question_paper.pdf
```

3. **Access documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📚 API Endpoints

### Core Endpoints

#### `POST /api/v1/upload`
Basic structure analysis with optional content extraction.

**Parameters:**
- `file`: PDF file (required)
- `extract_content`: Boolean (optional, default: false)

**Response:**
```json
{
  "success": true,
  "data": {
    "sections": [...],
    "summary": {...}
  },
  "processing_time": 2.34
}
```

#### `POST /api/v1/upload-enhanced`
Comprehensive content extraction with full analysis.

**Parameters:**
- `file`: PDF file (required)

**Response:**
```json
{
  "success": true,
  "data": {
    "sections": [
      {
        "name": "Section A",
        "questions": [
          {
            "number": "1",
            "type": "multiple_choice",
            "content": {
              "text": "What is the capital of France?",
              "images": [...],
              "formulas": [...],
              "tables": [...]
            },
            "options": ["A) London", "B) Berlin", "C) Paris", "D) Madrid"],
            "marks": 2
          }
        ]
      }
    ],
    "summary": {...}
  },
  "processing_time": 15.67,
  "structure_extraction_time": 3.45,
  "content_extraction_time": 12.22
}
```

### Information Endpoints

#### `GET /api/v1/capabilities`
Get service capabilities and configuration.

#### `GET /api/v1/question-types`
Get all supported question types.

#### `GET /api/v1/health`
Health check endpoint.

#### `GET /api/v1/stats`
Service statistics and usage information.

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | - | Google Gemini API key (required) |
| `GEMINI_MODEL` | `gemini-1.5-pro` | Gemini model to use |
| `ENABLE_ENHANCED_EXTRACTION` | `true` | Enable enhanced content extraction |
| `MAX_FILE_SIZE_MB` | `20` | Maximum file size in MB |
| `MAX_CONTENT_LENGTH` | `50000` | Maximum content length per question |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_RETRIES` | `3` | Maximum retry attempts |
| `RETRY_DELAY` | `2` | Retry delay in seconds |

### Question Types

The system supports 20+ question types including:
- Multiple Choice Questions (MCQ)
- True/False Questions
- Fill in the Blanks
- Short Answer Questions
- Long Answer Questions
- Essay Questions
- Case Study Questions
- Comprehension Questions
- Matching Questions
- Ordering/Sequencing Questions
- Diagram-based Questions
- Mathematical Problems
- Code-based Questions
- And more...

## 📊 Performance

### Typical Processing Times
- **Structure Analysis**: 2-5 seconds
- **Content Extraction**: 10-30 seconds (depending on complexity)
- **Total Enhanced Analysis**: 15-35 seconds

### Optimization Tips
- Use basic upload for structure-only analysis (faster)
- Use enhanced upload for complete digitization
- Optimize PDF quality for better extraction
- Consider file size limits for better performance

## 🧪 Testing

### Run Test Suite
```bash
# Test without PDF upload
python test_enhanced_api.py

# Test with PDF upload
python test_enhanced_api.py path/to/test.pdf
```

### Manual Testing
```bash
# Test basic upload
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf"

# Test enhanced upload
curl -X POST "http://localhost:8000/api/v1/upload-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.pdf"
```

## 🔍 Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Ensure your API key is set in the `.env` file
   - Verify the API key is valid and has proper permissions

2. **"File processing failed"**
   - Check if the PDF is not corrupted
   - Ensure file size is within limits
   - Verify PDF is text-based (not scanned images only)

3. **"Invalid response structure"**
   - This usually indicates an issue with Gemini's response
   - Check logs for detailed error information
   - Retry the request as it might be a temporary issue

4. **Slow processing times**
   - Large files take longer to process
   - Complex layouts require more processing time
   - Consider using basic upload for faster results

### Debug Mode
Enable debug logging for detailed information:
```env
LOG_LEVEL=DEBUG
```

## 📈 Monitoring

### Logs
- Application logs: `logs/app.log`
- Rotation: 10MB files, 7 days retention
- Levels: DEBUG, INFO, WARNING, ERROR

### Metrics
- Processing times per request
- Success/failure rates
- File size statistics
- Question type distribution

## 🔒 Security

- File size limits to prevent abuse
- Temporary file cleanup
- Input validation and sanitization
- Error message sanitization in production

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "app.main"]
```

### Production Considerations
- Use environment variables for configuration
- Set up proper logging and monitoring
- Configure reverse proxy (nginx)
- Set up SSL/TLS certificates
- Monitor resource usage and scaling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review the logs for detailed error information
- Create an issue in the repository
- Contact the development team

## 🔄 Version History

### v2.0.0 (Current)
- Enhanced content extraction
- Two-stage processing
- Improved validation
- Better error handling
- Performance monitoring
- Comprehensive testing

### v1.0.0
- Basic structure analysis
- Question type classification
- Simple content extraction
- Core API endpoints

---

**Note**: This system requires a valid Google Gemini API key and processes PDF files using AI. Processing times may vary based on document complexity and API response times.
```

Finally, let's create a requirements.txt file with all necessary dependencies:

```txt:question_paper_analyzer/requirements.txt
# Core FastAPI dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
aiofiles==23.2.1

# Google Gemini AI
google-generativeai==0.3.2

# Data validation and settings
pydantic==2.5.0
pydantic-settings==2.1.0

# Retry and error handling
tenacity==8.2.3

# Logging
loguru==0.7.2

# Environment management
python-dotenv==1.0.0

# HTTP client for testing
aiohttp==3.9.1

# Type hints
typing-extensions==4.8.0

# Additional utilities
pathlib2==2.3.7; python_version < "3.4"
```

And a simple startup script:

```bash:question_paper_analyzer/start.sh
#!/bin/bash

# Enhanced Question Paper Analyzer Startup Script

echo "🚀 Starting Enhanced Question Paper Analyzer v2.0"
echo "=================================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Running setup..."
    python update_config.py
fi

# Check if virtual environment should be activated
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs temp data

# Start the application
echo "🚀 Starting server..."
python -m app.main

echo "✅ Server started successfully!"
echo "📖 Documentation: http://localhost:8000/docs"
echo "🏥 Health check: http://localhost:8000/api/v1/health"
```

```bash
chmod +x start.sh
