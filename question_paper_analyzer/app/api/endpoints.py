from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from app.services.pdf_analyzer import pdf_analyzer
from app.services.question_classifier import question_classifier
from app.models.schemas import (
    AnalysisResponse, 
    EnhancedAnalysisResponse, 
    ErrorResponse
)
from app.utils.logger import app_logger
from app.core.config import settings
import time

router = APIRouter()

@router.post("/upload", response_model=AnalysisResponse)
async def analyze_question_paper(
    file: UploadFile = File(...),
    extract_content: bool = Query(False, description="Whether to extract question content (slower but more comprehensive)")
):
    """
    Analyze question paper structure from PDF file.
    
    - **file**: PDF file to analyze
    - **extract_content**: If True, extracts full question content (slower but comprehensive)
    
    Returns structured analysis of the question paper including:
    - Section structure
    - Question types and numbering
    - Optional question logic
    - Basic content (if extract_content=True)
    """
    try:
        app_logger.info(f"Received file: {file.filename} (content extraction: {extract_content})")
        
        result = await pdf_analyzer.analyze_question_paper(file, extract_content=extract_content)
        
        if result.success:
            app_logger.info(f"Analysis completed successfully in {result.processing_time:.2f}s")
        else:
            app_logger.error(f"Analysis failed: {result.error}")
        
        return result
        
    except Exception as e:
        app_logger.error(f"Endpoint error: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=str(e),
            processing_time=0
        )

@router.post("/upload-enhanced", response_model=EnhancedAnalysisResponse)
async def analyze_question_paper_enhanced(
    file: UploadFile = File(...)
):
    """
    Enhanced analysis with complete content extraction from PDF question paper.
    
    This endpoint provides comprehensive analysis including:
    - Complete question text extraction
    - Image and diagram descriptions
    - Mathematical formulas and equations
    - Tables and structured data
    - Code snippets (if present)
    - Multiple choice options
    - Matching question columns
    - Fill-in-the-blank details
    - Reading comprehension passages
    - Case study scenarios
    
    **Note**: This endpoint is slower than the basic upload endpoint but provides
    complete content extraction suitable for question paper digitization and rubric generation.
    
    **For Rubric Generation**: Use the WebSocket endpoint `/ws/rubric-generation` with the
    response from this endpoint to generate comprehensive rubrics and answer keys.
    """
    try:
        app_logger.info(f"Received file for enhanced analysis: {file.filename}")
        
        if not settings.ENABLE_ENHANCED_EXTRACTION:
            raise HTTPException(
                status_code=503,
                detail="Enhanced extraction is currently disabled"
            )
        
        result = await pdf_analyzer.analyze_question_paper_with_content(file)
        
        if result.success:
            app_logger.info(
                f"Enhanced analysis completed successfully in {result.processing_time:.2f}s "
                f"(structure: {result.structure_extraction_time:.2f}s, "
                f"content: {result.content_extraction_time:.2f}s)"
            )
            
            # Add rubric generation hint in response
            if settings.ENABLE_RUBRIC_GENERATION:
                result.data.metadata = result.data.metadata or {}
                result.data.metadata["rubric_generation_available"] = True
                result.data.metadata["websocket_endpoint"] = f"{settings.API_V1_STR}/ws/rubric-generation"
        else:
            app_logger.error(f"Enhanced analysis failed: {result.error}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Enhanced endpoint error: {str(e)}")
        return EnhancedAnalysisResponse(
            success=False,
            error=str(e),
            processing_time=0,
            structure_extraction_time=0,
            content_extraction_time=0
        )

@router.get("/question-types")
async def get_question_types():
    """
    Get all supported question types and their descriptions.
    
    Returns a comprehensive list of question types that the system can identify
    and classify, along with their identification patterns and examples.
    """
    try:
        question_types = question_classifier.get_question_types_for_prompt()
        return {
            "success": True,
            "data": question_types,
            "total_types": len(question_types.get("question_types", []))
        }
    except Exception as e:
        app_logger.error(f"Failed to get question types: {str(e)}")
        return ErrorResponse(
            error="Failed to retrieve question types",
            details={"exception": str(e)}
        )

@router.get("/capabilities")
async def get_capabilities():
    """
    Get service capabilities and configuration.
    
    Returns information about:
    - Supported file formats
    - Maximum file size
    - Available features
    - Model configuration
    - Processing limits
    - Rubric generation capabilities
    """
    return {
        "success": True,
        "capabilities": {
            "supported_formats": list(settings.ALLOWED_EXTENSIONS),
            "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
            "gemini_model": settings.GEMINI_MODEL,
            "features": {
                "structure_analysis": True,
                "content_extraction": settings.ENABLE_ENHANCED_EXTRACTION,
                "rubric_generation": settings.ENABLE_RUBRIC_GENERATION,
                "image_description": True,
                "formula_extraction": True,
                "table_extraction": True,
                "code_extraction": True,
                "multi_language_support": True,
                "optional_logic_detection": True,
                "marks_allocation_detection": True,
                "real_time_processing": settings.ENABLE_RUBRIC_GENERATION,
                "educational_standards": settings.ENABLE_RUBRIC_GENERATION,
                "bloom_taxonomy": settings.ENABLE_RUBRIC_GENERATION
            },
            "processing": {
                "max_retries": settings.MAX_RETRIES,
                "retry_delay": settings.RETRY_DELAY,
                "max_content_length": settings.MAX_CONTENT_LENGTH,
                "rubric_worker_count": settings.RUBRIC_WORKER_COUNT if settings.ENABLE_RUBRIC_GENERATION else 0,
                "rubric_quality_mode": settings.RUBRIC_QUALITY_MODE if settings.ENABLE_RUBRIC_GENERATION else None
            },
            "question_types_supported": len(question_classifier.question_types.get("question_types", [])),
            "api_version": "3.0.0",
            "websocket_support": settings.ENABLE_RUBRIC_GENERATION
        }
    }

@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the service and its dependencies.
    """
    start_time = time.time()
    
    try:
        # Check if Gemini API key is configured
        if not settings.GEMINI_API_KEY:
            raise Exception("Gemini API key not configured")
        
        # Check if question types are loaded
        question_types_count = len(question_classifier.question_types.get("question_types", []))
        if question_types_count == 0:
            raise Exception("Question types not loaded")
        
        response_time = time.time() - start_time
        
        dependencies = {
            "gemini_api": "configured",
            "question_types": f"{question_types_count} types loaded",
            "enhanced_extraction": "enabled" if settings.ENABLE_ENHANCED_EXTRACTION else "disabled",
            "rubric_generation": "enabled" if settings.ENABLE_RUBRIC_GENERATION else "disabled"
        }
        
        if settings.ENABLE_RUBRIC_GENERATION:
            dependencies["rubric_workers"] = f"{settings.RUBRIC_WORKER_COUNT} workers"
            dependencies["rubric_quality"] = settings.RUBRIC_QUALITY_MODE
        
        return {
            "success": True,
            "status": "healthy",
            "timestamp": time.time(),
            "response_time": response_time,
            "version": "3.0.0",
            "dependencies": dependencies
        }
        
    except Exception as e:
        response_time = time.time() - start_time
        app_logger.error(f"Health check failed: {str(e)}")
        
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "status": "unhealthy",
                "timestamp": time.time(),
                "response_time": response_time,
                                "error": str(e)
            }
        )

@router.get("/stats")
async def get_stats():
    """
    Get service statistics and usage information.
    """
    try:
        question_types = question_classifier.question_types
        
        stats = {
            "success": True,
            "statistics": {
                "question_types": {
                    "total": len(question_types.get("question_types", [])),
                    "categories": list(set([
                        qt.get("category", "uncategorized") 
                        for qt in question_types.get("question_types", [])
                    ]))
                },
                "supported_features": {
                    "structure_analysis": True,
                    "content_extraction": settings.ENABLE_ENHANCED_EXTRACTION,
                    "rubric_generation": settings.ENABLE_RUBRIC_GENERATION,
                    "image_processing": True,
                    "formula_extraction": True,
                    "table_processing": True,
                    "code_extraction": True,
                    "websocket_support": settings.ENABLE_RUBRIC_GENERATION
                },
                "configuration": {
                    "model": settings.GEMINI_MODEL,
                    "max_file_size_mb": settings.MAX_FILE_SIZE_MB,
                    "max_retries": settings.MAX_RETRIES,
                    "enhanced_extraction": settings.ENABLE_ENHANCED_EXTRACTION,
                    "api_version": "3.0.0"
                }
            }
        }
        
        # Add rubric-specific stats if enabled
        if settings.ENABLE_RUBRIC_GENERATION:
            stats["statistics"]["rubric_generation"] = {
                "worker_count": settings.RUBRIC_WORKER_COUNT,
                "quality_mode": settings.RUBRIC_QUALITY_MODE,
                "supported_standards": ["bloom_taxonomy", "custom"],
                "supported_rubric_types": ["analytical", "holistic", "simple_checklist"],
                "performance_levels": ["Excellent", "Proficient", "Developing", "Beginning"]
            }
        
        return stats
        
    except Exception as e:
        app_logger.error(f"Failed to get stats: {str(e)}")
        return ErrorResponse(
            error="Failed to retrieve statistics",
            details={"exception": str(e)}
        )

@router.get("/rubric-info")
async def get_rubric_info():
    """
    Get information about rubric generation capabilities.
    
    Returns details about:
    - Supported rubric standards
    - Available rubric types
    - Quality modes
    - Educational frameworks
    """
    if not settings.ENABLE_RUBRIC_GENERATION:
        raise HTTPException(
            status_code=503,
            detail="Rubric generation is not enabled"
        )
    
    try:
        return {
            "success": True,
            "rubric_capabilities": {
                "supported_standards": {
                    "bloom_taxonomy": {
                        "description": "Based on Bloom's Taxonomy cognitive levels",
                        "levels": ["knowledge", "comprehension", "application", "analysis", "synthesis", "evaluation"]
                    },
                    "custom": {
                        "description": "Custom rubric based on question content and type",
                        "flexible": True
                    }
                },
                "rubric_types": {
                    "analytical": {
                        "description": "Detailed criteria-based rubric with multiple performance levels",
                        "best_for": ["essays", "projects", "complex_problems"]
                    },
                    "holistic": {
                        "description": "Overall performance assessment with single score",
                        "best_for": ["creative_writing", "presentations", "overall_assessment"]
                    },
                    "simple_checklist": {
                        "description": "Basic checklist format for straightforward assessment",
                        "best_for": ["mcq", "short_answer", "basic_problems"]
                    }
                },
                "performance_levels": [
                    {
                        "level": "Excellent",
                        "range": "90-100%",
                        "description": "Exceeds expectations, demonstrates mastery"
                    },
                    {
                        "level": "Proficient", 
                        "range": "75-89%",
                        "description": "Meets expectations, shows competence"
                    },
                    {
                        "level": "Developing",
                        "range": "60-74%", 
                        "description": "Approaching expectations, partial understanding"
                    },
                    {
                        "level": "Beginning",
                        "range": "Below 60%",
                        "description": "Below expectations, minimal understanding"
                    }
                ],
                "quality_modes": {
                    "high": {
                        "description": "Maximum quality with detailed analysis",
                        "processing_time": "Slower but comprehensive"
                    },
                    "balanced": {
                        "description": "Good quality with reasonable speed",
                        "processing_time": "Moderate"
                    },
                    "fast": {
                        "description": "Quick generation with basic quality",
                        "processing_time": "Faster but less detailed"
                    }
                },
                "supported_subjects": [
                    "Mathematics", "Science", "English", "History", "Geography",
                    "Physics", "Chemistry", "Biology", "Computer Science", "Economics"
                ],
                "grade_levels": ["1-12", "undergraduate", "graduate"],
                "websocket_endpoint": f"{settings.API_V1_STR}/ws/rubric-generation"
            }
        }
        
    except Exception as e:
        app_logger.error(f"Failed to get rubric info: {str(e)}")
        return ErrorResponse(
            error="Failed to retrieve rubric information",
            details={"exception": str(e)}
        )

