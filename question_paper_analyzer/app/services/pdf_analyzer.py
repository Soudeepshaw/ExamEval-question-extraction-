import os
import tempfile
import time
from typing import Dict, Optional, Any
from fastapi import UploadFile
from app.core.gemini_client import gemini_client
from app.services.question_classifier import question_classifier
from app.models.schemas import (
    QuestionPaperStructure, 
    AnalysisResponse, 
    EnhancedQuestionPaperStructure, 
    EnhancedAnalysisResponse
)
from app.utils.logger import app_logger
from app.core.config import settings

class PDFAnalyzer:
    def __init__(self):
        self.gemini_client = gemini_client
        self.question_classifier = question_classifier
    
    async def analyze_question_paper(self, file: UploadFile, extract_content: bool = False) -> AnalysisResponse:
        """Main method to analyze question paper structure (backward compatibility)"""
        if extract_content:
            enhanced_result = await self.analyze_question_paper_with_content(file)
            # Convert enhanced response to basic response for backward compatibility
            return AnalysisResponse(
                success=enhanced_result.success,
                data=self._convert_enhanced_to_basic(enhanced_result.data) if enhanced_result.data else None,
                error=enhanced_result.error,
                processing_time=enhanced_result.processing_time
            )
        
        start_time = time.time()
        temp_file_path = None
        
        try:
            # Validate file
            self._validate_file(file)
            
            # Save uploaded file temporarily
            temp_file_path = await self._save_temp_file(file)
            
            # Upload to Gemini
            uploaded_file = await self.gemini_client.upload_file(temp_file_path)
            
            # Get question types for analysis
            question_types = self.question_classifier.get_question_types_for_prompt()
            
            # Analyze structure only
            raw_structure = await self.gemini_client.analyze_structure(uploaded_file, question_types)
            
            # Validate and structure response
            structured_data = self._validate_and_structure_response(raw_structure)
            
            processing_time = time.time() - start_time
            
            return AnalysisResponse(
                success=True,
                data=structured_data,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            app_logger.error(f"Analysis failed: {str(e)}")
            
            return AnalysisResponse(
                success=False,
                error=str(e),
                processing_time=processing_time
            )
        
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                app_logger.info(f"Cleaned up temp file: {temp_file_path}")
    
    async def analyze_question_paper_with_content(self, file: UploadFile) -> EnhancedAnalysisResponse:
        """Enhanced method to analyze question paper with full content extraction"""
        start_time = time.time()
        temp_file_path = None
        
        try:
            # Validate file
            self._validate_file(file)
            
            # Save uploaded file temporarily
            temp_file_path = await self._save_temp_file(file)
            
            # Upload to Gemini
            uploaded_file = await self.gemini_client.upload_file(temp_file_path)
            
            # Get question types for analysis
            question_types = self.question_classifier.get_question_types_for_prompt()
            
            # Step 1: Analyze structure
            structure_start = time.time()
            app_logger.info("Step 1: Extracting question paper structure...")
            raw_structure = await self.gemini_client.analyze_structure(uploaded_file, question_types)
            structure_time = time.time() - structure_start
            app_logger.info(f"Structure extraction completed in {structure_time:.2f}s")
            
            # Step 2: Extract content
            content_start = time.time()
            app_logger.info("Step 2: Extracting question content...")
            enhanced_data = await self.gemini_client.extract_content(uploaded_file, raw_structure, question_types)
            content_time = time.time() - content_start
            app_logger.info(f"Content extraction completed in {content_time:.2f}s")
            
            # Preprocess the raw data before validation
            preprocessed_data = self._preprocess_gemini_response(enhanced_data)
            
            # Validate and structure enhanced response
            structured_data = self._validate_and_structure_enhanced_response(preprocessed_data)
            
            processing_time = time.time() - start_time
            
            return EnhancedAnalysisResponse(
                success=True,
                data=structured_data,
                processing_time=processing_time,
                structure_extraction_time=structure_time,
                content_extraction_time=content_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            app_logger.error(f"Enhanced analysis failed: {str(e)}")
            
            return EnhancedAnalysisResponse(
                success=False,
                error=str(e),
                processing_time=processing_time,
                structure_extraction_time=0,
                content_extraction_time=0
            )
        
        finally:
            # Clean up temp file
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                app_logger.info(f"Cleaned up temp file: {temp_file_path}")
    
    def _preprocess_gemini_response(self, raw_data: Dict) -> Dict:
        """Preprocess Gemini response to ensure compatibility with Pydantic models"""
        try:
            app_logger.info("Preprocessing Gemini response for validation...")
            
            # Ensure summary has required fields
            if 'summary' in raw_data:
                summary = raw_data['summary']
                if 'total_subquestions' not in summary:
                    summary['total_subquestions'] = 0
                if 'optional_structures' not in summary:
                    summary['optional_structures'] = []
                if 'question_type_distribution' not in summary:
                    summary['question_type_distribution'] = {}
            
            # Process sections
            if 'sections' in raw_data:
                for section in raw_data['sections']:
                    if 'questions' in section:
                        for question in section['questions']:
                            # Ensure content exists
                            if 'content' not in question:
                                question['content'] = {'text': ''}
                            
                            # Process subquestions
                            if 'subquestions' in question:
                                for subq in question['subquestions']:
                                    if 'content' not in subq:
                                        subq['content'] = {'text': ''}
            
            app_logger.info("Gemini response preprocessing completed")
            return raw_data
            
        except Exception as e:
            app_logger.error(f"Error preprocessing Gemini response: {str(e)}")
            return raw_data
    
    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file extension
        if not file.filename.lower().endswith('.pdf'):
            raise ValueError("Only PDF files are allowed")
        
        # Check file size
        if hasattr(file, 'size') and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
        
        app_logger.info(f"File validation passed: {file.filename}")
    
    async def _save_temp_file(self, file: UploadFile) -> str:
        """Save uploaded file to temporary location"""
        try:
            # Create temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='question_paper_')
            
            # Write file content
            content = await file.read()
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(content)
            
            app_logger.info(f"Saved temp file: {temp_path} ({len(content)} bytes)")
            return temp_path
            
        except Exception as e:
            app_logger.error(f"Failed to save temp file: {str(e)}")
            raise
    
    def _validate_and_structure_response(self, raw_data: Dict) -> QuestionPaperStructure:
        """Validate and structure the basic response from Gemini"""
        try:
            # Basic validation
            if not isinstance(raw_data, dict):
                raise ValueError("Response is not a valid dictionary")
            
            if 'sections' not in raw_data:
                raise ValueError("Response missing 'sections' field")
            
            if 'summary' not in raw_data:
                raise ValueError("Response missing 'summary' field")
            
            # Validate question types
            self._validate_question_types_in_response(raw_data)
            
            # Create Pydantic model for validation
            structured_data = QuestionPaperStructure(**raw_data)
            
            app_logger.info(f"Successfully structured response with {len(structured_data.sections)} sections")
            return structured_data
            
        except Exception as e:
            app_logger.error(f"Failed to validate response: {str(e)}")
            raise ValueError(f"Invalid response structure: {str(e)}")
    
    def _validate_and_structure_enhanced_response(self, raw_data: Dict) -> EnhancedQuestionPaperStructure:
        """Validate and structure the enhanced response from Gemini"""
        try:
            # Basic validation
            if not isinstance(raw_data, dict):
                raise ValueError("Response is not a valid dictionary")
            
            if 'sections' not in raw_data:
                raise ValueError("Response missing 'sections' field")
            
            if 'summary' not in raw_data:
                raise ValueError("Response missing 'summary' field")
            
            # Validate question types
            self._validate_question_types_in_enhanced_response(raw_data)
            
            # Create Pydantic model for validation
            structured_data = EnhancedQuestionPaperStructure(**raw_data)
            
            app_logger.info(f"Successfully structured enhanced response with {len(structured_data.sections)} sections")
            return structured_data
            
        except Exception as e:
            app_logger.error(f"Failed to validate enhanced response: {str(e)}")
            # Log the raw data for debugging
            if settings.LOG_LEVEL == "DEBUG":
                app_logger.debug(f"Raw data that failed validation: {raw_data}")
            raise ValueError(f"Invalid enhanced response structure: {str(e)}")
    
    def _validate_question_types_in_response(self, data: Dict) -> None:
        """Validate that all question types in response are valid"""
        invalid_types = []
        
        for section in data.get('sections', []):
            for question in section.get('questions', []):
                q_type = question.get('type')
                if q_type and not self.question_classifier.validate_question_type(q_type):
                    invalid_types.append(q_type)
                
                for subq in question.get('subquestions', []):
                    sq_type = subq.get('type')
                    if sq_type and not self.question_classifier.validate_question_type(sq_type):
                        invalid_types.append(sq_type)
        
        if invalid_types:
            app_logger.warning(f"Found invalid question types: {set(invalid_types)}")
            # Don't raise error, just log warning as Gemini might use variations
    
    def _validate_question_types_in_enhanced_response(self, data: Dict) -> None:
        """Validate that all question types in enhanced response are valid"""
        invalid_types = []
        
        for section in data.get('sections', []):
            for question in section.get('questions', []):
                q_type = question.get('type')
                if q_type and not self.question_classifier.validate_question_type(q_type):
                                        invalid_types.append(q_type)
                
                for subq in question.get('subquestions', []):
                    sq_type = subq.get('type')
                    if sq_type and not self.question_classifier.validate_question_type(sq_type):
                        invalid_types.append(sq_type)
        
        if invalid_types:
            app_logger.warning(f"Found invalid question types in enhanced response: {set(invalid_types)}")
    
    def _convert_enhanced_to_basic(self, enhanced_data: EnhancedQuestionPaperStructure) -> QuestionPaperStructure:
        """Convert enhanced response to basic response for backward compatibility"""
        try:
            basic_sections = []
            
            for section in enhanced_data.sections:
                basic_questions = []
                
                for question in section.questions:
                    basic_subquestions = []
                    
                    if question.subquestions:
                        for subq in question.subquestions:
                            basic_subquestions.append({
                                "label": subq.label,
                                "type": subq.type,
                                "optional": subq.optional,
                                "optional_group": subq.optional_group
                            })
                    
                    basic_questions.append({
                        "number": question.number,
                        "type": question.type,
                        "optional": question.optional,
                        "optional_with": question.optional_with,
                        "subquestions": basic_subquestions
                    })
                
                basic_sections.append({
                    "name": section.name,
                    "optional_between": section.optional_between,
                    "optional_with": section.optional_with,
                    "instruction": section.instruction,
                    "questions": basic_questions
                })
            
            basic_data = {
                "sections": basic_sections,
                "summary": {
                    "total_sections": enhanced_data.summary.total_sections,
                    "total_questions": enhanced_data.summary.total_questions,
                    "optional_structures": enhanced_data.summary.optional_structures
                }
            }
            
            return QuestionPaperStructure(**basic_data)
            
        except Exception as e:
            app_logger.error(f"Failed to convert enhanced to basic response: {str(e)}")
            raise

pdf_analyzer = PDFAnalyzer()
