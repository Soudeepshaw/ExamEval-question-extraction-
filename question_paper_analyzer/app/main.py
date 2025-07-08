from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.endpoints import router
from app.api.websocket_endpoints import router as websocket_router
from app.core.config import settings
from app.utils.logger import app_logger
import os

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    Advanced API for extracting question paper structure and content from PDFs using Gemini AI.
    
    ## Features
    
    * **Structure Analysis**: Extract question paper structure, sections, and question types
    * **Content Extraction**: Extract complete question text, images, diagrams, and multimedia content
    * **Rubric Generation**: AI-powered rubric and answer key generation with real-time WebSocket streaming
    * **Multi-format Support**: Handle various question types including MCQ, essays, case studies, etc.
    * **Image Description**: AI-powered description of images, diagrams, and charts
    * **Formula Extraction**: Mathematical formulas and equations preservation
    * **Table Processing**: Structured extraction of tabular data
    * **Optional Logic Detection**: Identify optional questions and choice patterns
    * **Marks Allocation**: Extract marks and time allocation information
    * **Educational Standards**: Bloom's Taxonomy compliance and grade-level assessment
    
    ## Endpoints
    
    * `/upload` - Basic structure analysis (fast)
    * `/upload-enhanced` - Complete content extraction (comprehensive but slower)
    * `/ws/rubric-generation` - WebSocket for real-time rubric generation
    * `/question-types` - Get supported question types
    * `/capabilities` - Get service capabilities
    
    ## WebSocket Usage
    
    Connect to `/ws/rubric-generation` and send:
    ```json
    {
        "enhanced_api_response": { ... },
        "user_preferences": {
            "subject_hint": "Mathematics",
            "grade_level": "10",
            "quality_mode": "high",
            "rubric_standard": "bloom_taxonomy"
        }
    }
    ```
    
    Receive real-time updates:
    - `progress`: Processing status updates
    - `question_complete`: Individual question rubrics
    - `final_summary`: Complete processing summary
    - `error`: Error messages
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.API_V1_STR, tags=["Question Paper Analysis"])
app.include_router(websocket_router, prefix=settings.API_V1_STR, tags=["WebSocket Rubric Generation"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    app_logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "details": str(exc) if settings.LOG_LEVEL == "DEBUG" else None
        }
    )

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    app_logger.info(f"Starting {settings.PROJECT_NAME} v3.0.0")
    app_logger.info(f"Max file size: {settings.MAX_FILE_SIZE_MB}MB")
    app_logger.info(f"Gemini model: {settings.GEMINI_MODEL}")
    app_logger.info(f"Enhanced extraction enabled: {settings.ENABLE_ENHANCED_EXTRACTION}")
    app_logger.info(f"Rubric generation enabled: {settings.ENABLE_RUBRIC_GENERATION}")
    app_logger.info(f"Rubric worker count: {settings.RUBRIC_WORKER_COUNT}")
    app_logger.info(f"Rubric quality mode: {settings.RUBRIC_QUALITY_MODE}")
    
    # Validate Gemini API key
    if not settings.GEMINI_API_KEY:
        app_logger.error("GEMINI_API_KEY not found in environment variables")
        raise ValueError("GEMINI_API_KEY is required")
    
    # Load question types
    from app.services.question_classifier import question_classifier
    app_logger.info(f"Loaded {len(question_classifier.question_types['question_types'])} question types")
    
    # Initialize rubric services
    if settings.ENABLE_RUBRIC_GENERATION:
        from app.services.rubric_workers import rubric_worker_pool
        from app.core.rubric_gemini_client import rubric_gemini_client
        app_logger.info(f"Initialized rubric generation with {rubric_worker_pool.worker_count} workers")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    app_logger.info(f"Shutting down {settings.PROJECT_NAME}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} v3.0.0",
        "description": "Advanced Question Paper Analysis with AI-powered rubric generation",
        "version": "3.0.0",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health",
        "capabilities": f"{settings.API_V1_STR}/capabilities",
        "websocket": f"{settings.API_V1_STR}/ws/rubric-generation",
        "features": {
            "structure_analysis": True,
            "content_extraction": True,
            "rubric_generation": settings.ENABLE_RUBRIC_GENERATION,
            "image_description": True,
            "formula_extraction": True,
            "enhanced_extraction": settings.ENABLE_ENHANCED_EXTRACTION,
            "real_time_processing": True,
            "educational_standards": True,
            "bloom_taxonomy": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
