import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Question Paper Analyzer"
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-1.5-pro"  # Ensure this model supports structured output
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    ALLOWED_EXTENSIONS: set = {".pdf"}
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 2
    
    # Content Extraction Configuration
    ENABLE_ENHANCED_EXTRACTION: bool = os.getenv("ENABLE_ENHANCED_EXTRACTION", "true").lower() == "true"
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "50000"))
    
    # Structured Output Configuration
    USE_NATIVE_STRUCTURED_OUTPUT: bool = os.getenv("USE_NATIVE_STRUCTURED_OUTPUT", "true").lower() == "true"
    
    # Rubric Generation Configuration
    ENABLE_RUBRIC_GENERATION: bool = os.getenv("ENABLE_RUBRIC_GENERATION", "true").lower() == "true"
    RUBRIC_WORKER_COUNT: int = int(os.getenv("RUBRIC_WORKER_COUNT", "4"))
    RUBRIC_QUALITY_MODE: str = os.getenv("RUBRIC_QUALITY_MODE", "balanced")  # high, balanced, fast
    RUBRIC_MAX_CRITERIA: int = int(os.getenv("RUBRIC_MAX_CRITERIA", "6"))
    RUBRIC_TIMEOUT_SECONDS: int = int(os.getenv("RUBRIC_TIMEOUT_SECONDS", "300"))
    RUBRIC_BATCH_DELAY: float = 2.0  # Delay between batches (seconds)
    RUBRIC_BATCH_SIZE: int = 2  # Process in small batches
    RUBRIC_REQUEST_DELAY: float = 1.0  # Delay between requests (seconds)

    
    # WebSocket Configuration
    WEBSOCKET_HEARTBEAT_INTERVAL: int = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))
    WEBSOCKET_MAX_CONNECTIONS: int = int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "10"))
    
    class Config:
        case_sensitive = True

settings = Settings()
