# Question Paper Analyzer

Advanced AI-powered microservice for extracting question paper structure and content from PDFs using Google's Gemini AI, with comprehensive rubric generation capabilities.

## Features

- **PDF Analysis**: Extract complete question paper structure and content
- **AI-Powered Classification**: Automatic question type identification
- **Rubric Generation**: Create detailed rubrics and answer keys
- **Real-time Processing**: WebSocket-based streaming for live updates
- **Educational Standards**: Bloom's Taxonomy compliance
- **Multi-format Support**: Handle various question types (MCQ, essays, case studies, etc.)

## Quick Start

### Using Docker

1. Clone the repository
2. Copy `.env.example` to `.env` and add your Gemini API key
3. Run with Docker Compose:

```bash
docker-compose up -d
```

### Manual Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export GEMINI_API_KEY="your-api-key"
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /api/v1/upload` - Basic structure analysis
- `POST /api/v1/upload-enhanced` - Complete content extraction
- `WS /api/v1/ws/rubric-generation` - Real-time rubric generation
- `GET /api/v1/capabilities` - Service capabilities
- `GET /docs` - Interactive API documentation

## Usage

### 1. Extract Question Paper Content
```bash
curl -X POST "http://localhost:8000/api/v1/upload-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@question_paper.pdf"
```

### 2. Generate Rubrics (WebSocket)
````javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/rubric-generation');
ws.send(JSON.stringify({
    enhanced_api_response: response,
    user_preferences: {
                subject_hint: "Mathematics",
        grade_level: "10",
        quality_mode: "high",
        rubric_standard: "bloom_taxonomy"
    }
}));
```

## Configuration

Key environment variables:

- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `ENABLE_ENHANCED_EXTRACTION` - Enable content extraction (default: true)
- `ENABLE_RUBRIC_GENERATION` - Enable rubric generation (default: true)
- `RUBRIC_WORKER_COUNT` - Number of parallel workers (default: 4)
- `RUBRIC_QUALITY_MODE` - Quality mode: high/balanced/fast (default: balanced)

## Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Rubric Usage Guide](docs/RUBRIC_USAGE.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)

## License

MIT License
```

### 10. **docs/API_DOCUMENTATION.md** (New)
```markdown
# API Documentation

## Overview

The Question Paper Analyzer provides REST APIs and WebSocket endpoints for comprehensive question paper analysis and rubric generation.

## Authentication

Currently, no authentication is required. The service uses the configured Gemini API key for AI operations.

## REST Endpoints

### Upload Question Paper (Basic)
```
POST /api/v1/upload
```

**Parameters:**
- `file` (form-data): PDF file to analyze
- `extract_content` (query, optional): Boolean to enable content extraction

**Response:**
```json
{
    "success": true,
    "data": {
        "sections": [...],
        "summary": {...}
    },
    "processing_time": 12.5
}
```

### Upload Question Paper (Enhanced)
```
POST /api/v1/upload-enhanced
```

**Parameters:**
- `file` (form-data): PDF file to analyze

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
                            "text": "What is 2+2?",
                            "images": [],
                            "formulas": []
                        },
                        "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
                        "marks": 2
                    }
                ]
            }
        ],
        "summary": {...},
        "metadata": {...}
    },
    "processing_time": 45.2,
    "structure_extraction_time": 15.1,
    "content_extraction_time": 30.1
}
```

### Get Question Types
```
GET /api/v1/question-types
```

**Response:**
```json
{
    "success": true,
    "data": {
        "question_types": [
            {
                "type": "multiple_choice",
                "category": "objective",
                "identify": "Questions with multiple options"
            }
        ]
    },
    "total_types": 10
}
```

### Get Service Capabilities
```
GET /api/v1/capabilities
```

**Response:**
```json
{
    "success": true,
    "capabilities": {
        "supported_formats": [".pdf"],
        "max_file_size_mb": 20,
        "features": {
            "structure_analysis": true,
            "content_extraction": true,
            "rubric_generation": true,
            "real_time_processing": true
        }
    }
}
```

### Health Check
```
GET /api/v1/health
```

**Response:**
```json
{
    "success": true,
    "status": "healthy",
    "version": "3.0.0",
    "dependencies": {
        "gemini_api": "configured",
        "question_types": "10 types loaded"
    }
}
```

## WebSocket Endpoints

### Rubric Generation
```
WS /api/v1/ws/rubric-generation
```

**Send Message:**
```json
{
    "enhanced_api_response": {
        // Response from /upload-enhanced endpoint
    },
    "user_preferences": {
        "subject_hint": "Mathematics",
        "grade_level": "10",
        "quality_mode": "high",
        "rubric_standard": "bloom_taxonomy"
    }
}
```

**Receive Messages:**

Progress Update:
```json
{
    "type": "progress",
    "data": {
        "status": "processing",
        "current_question": 3,
        "total_questions": 10,
        "estimated_remaining_time": 45
    }
}
```

Question Complete:
```json
{
    "type": "question_complete",
    "data": {
        "question_index": 3,
        "result": {
            "classification": {
                "question_type": "essay",
                "subject": "Mathematics",
                "bloom_level": "analysis",
                "marks": 10
            },
            "rubric": {
                "type": "analytical",
                "criteria": [...]
            },
            "answer_key": {
                "expected_outline": [...],
                "key_concepts": [...]
            }
        }
    }
}
```

Final Summary:
```json
{
    "type": "final_summary",
    "data": {
        "summary": {
            "total_questions_processed": 10,
            "successful_generations": 9,
            "failed_generations": 1,
            "total_processing_time": 120.5
        }
    }
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
    "success": false,
    "error": "Error message",
    "details": {
        "exception": "Detailed error information"
    }
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid file, parameters)
- `413` - File too large
- `422` - Validation error
- `500` - Internal server error
- `503` - Service unavailable (feature disabled)

## Rate Limits

Currently no rate limits are enforced, but consider implementing them for production use.

## Examples

See the [Rubric Usage Guide](RUBRIC_USAGE.md) for detailed examples and integration patterns.
```

### 11. **tests/test_api.py** (New)
```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Welcome to Question Paper Analyzer" in response.json()["message"]

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code in [200, 503]  # May fail if API key not configured

def test_capabilities():
    response = client.get("/api/v1/capabilities")
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "capabilities" in response.json()

def test_question_types():
    response = client.get("/api/v1/question-types")
    assert response.status_code == 200
    assert response.json()["success"] == True
    assert "data" in response.json()

def test_upload_without_file():
    response = client.post("/api/v1/upload")
    assert response.status_code == 422  # Validation error

def test_upload_enhanced_without_file():
    response = client.post("/api/v1/upload-enhanced")
    assert response.status_code == 422  # Validation error

# Add more tests as needed
```

### 12. **tests/test_gemini_client.py** (New)
```python
import pytest
from unittest.mock import Mock, patch
from app.core.gemini_client import GeminiClient

@pytest.fixture
def gemini_client():
    return GeminiClient()

def test_gemini_client_initialization(gemini_client):
    assert gemini_client.model is not None

@patch('app.core.gemini_client.genai.upload_file')
async def test_upload_file(mock_upload, gemini_client):
    # Mock the upload response
    mock_file = Mock()
    mock_file.state.name = "ACTIVE"
    mock_file.uri = "test-uri"
    mock_upload.return_value = mock_file
    
    result = await gemini_client.upload_file("test.pdf")
    assert result == mock_file

def test_parse_json_response(gemini_client):
    # Mock response object
    mock_response = Mock()
    mock_response.text = '{"test": "data"}'
    
    result = gemini_client._parse_json_response(mock_response)
    assert result == {"test": "data"}

def test_parse_json_response_with_markdown(gemini_client):
    # Mock response with markdown formatting
    mock_response = Mock()
    mock_response.text = '```json\n{"test": "data"}\n```'
    
    result = gemini_client._parse_json_response(mock_response)
    assert result == {"test": "data"}

# Add more tests as needed
```

## Files Already Created (from previous context):

The following files are already implemented and don't need to be created again:

1. **app/core/gemini_client.py** - Main Gemini client
2. **app/models/schemas.py** - Pydantic schemas
3. **app/services/pdf_analyzer.py** - PDF analysis service
4. **app/services/question_classifier.py** - Question classification
5. **app/utils/logger.py** - Logging configuration
6. **app/utils/helpers.py** - Utility functions
7. **app/api/endpoints.py** - REST API endpoints

## New Files to Create:

1. **app/models/rubric_schemas.py** - Rubric-specific schemas
2. **app/core/rubric_gemini_client.py** - Rubric generation client
3. **app/services/rubric_generator.py** - Core rubric logic
4. **app/services/rubric_workers.py** - Worker pool
5. **app/services/rubric_validator.py** - Quality validation
6. **app/services/question_parser.py** - Question parsing
7. **app/services/websocket_handler.py** - WebSocket handling
8. **app/api/websocket_endpoints.py** - WebSocket endpoints

## Deployment Steps:

1. **Development Setup:**
```bash
git clone <repository>
cd question_paper_analyzer
cp .env.example .env
# Edit .env with your Gemini API key
pip install -r requirements.txt
uvicorn app.main:app --reload
```

2. **Docker Deployment:**
```bash
docker-compose up -d
```

3. **Production Deployment:**
```bash
# Build and deploy using your preferred method
# Configure environment variables
# Set up reverse proxy (nginx)
# Configure SSL certificates
```

This complete file structure provides a production-ready microservice for question paper extraction and rubric generation using only Google's Gemini AI.

