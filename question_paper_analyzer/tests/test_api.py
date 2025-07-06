import pytest
from fastapi.testclient import TestClient
from app.main import app
import io

client = TestClient(app)

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Question Paper Analyzer" in response.json()["message"]

def test_get_question_types():
    """Test question types endpoint"""
    response = client.get("/api/v1/question-types")
    assert response.status_code == 200
    data = response.json()
    assert "question_types" in data
    assert len(data["question_types"]) > 0

def test_upload_invalid_file():
    """Test upload with invalid file type"""
    # Create a fake text file
    fake_file = io.BytesIO(b"This is not a PDF")
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", fake_file, "text/plain")}
    )
    
    assert response.status_code == 422 or response.status_code == 500

def test_upload_no_file():
    """Test upload without file"""
    response = client.post("/api/v1/upload")
    assert response.status_code == 422

# Note: Add more comprehensive tests with actual PDF files
