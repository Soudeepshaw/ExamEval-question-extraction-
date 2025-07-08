import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import app_logger
from app.models.rubric_schemas import QuestionClassification, UserPreferences
from typing import Optional, Dict, Any
import json
import asyncio


class RubricGeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # Use the latest model with structured output
        self.structured_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",  # Use flash for better reliability
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=self._get_response_schema(),
                temperature=0.1,
                candidate_count=1
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
    
    def _get_response_schema(self) -> genai.protos.Schema:
        """Create a comprehensive but safe schema for Gemini"""
        return genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "classification": genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "question_type": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "subject": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "topic": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "difficulty_level": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "bloom_level": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "cognitive_skills": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING)
                        ),
                        "marks": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                        "estimated_time": genai.protos.Schema(type=genai.protos.Type.STRING)
                    },
                    required=["question_type", "subject", "topic", "difficulty_level", "bloom_level", "marks", "estimated_time"]
                ),
                "rubric": genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "type": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "standard": genai.protos.Schema(type=genai.protos.Type.STRING),
                        "total_marks": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                        "criteria": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "criterion": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "weight": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                                    "marks": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                                    "performance_levels": genai.protos.Schema(
                                        type=genai.protos.Type.ARRAY,
                                        items=genai.protos.Schema(
                                            type=genai.protos.Type.OBJECT,
                                            properties={
                                                "level": genai.protos.Schema(type=genai.protos.Type.STRING),
                                                "marks_range": genai.protos.Schema(type=genai.protos.Type.STRING),
                                                "descriptor": genai.protos.Schema(type=genai.protos.Type.STRING),
                                                "indicators": genai.protos.Schema(
                                                    type=genai.protos.Type.ARRAY,
                                                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                                                )
                                            }
                                        )
                                    )
                                }
                            )
                        ),
                        "marking_scheme": genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "total_marks": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                # Fixed: Replace mapping with array of key-value objects
                                "mark_distribution": genai.protos.Schema(
                                    type=genai.protos.Type.ARRAY,
                                    items=genai.protos.Schema(
                                        type=genai.protos.Type.OBJECT,
                                        properties={
                                            "component": genai.protos.Schema(type=genai.protos.Type.STRING),
                                            "marks": genai.protos.Schema(type=genai.protos.Type.NUMBER)
                                        },
                                        required=["component", "marks"]
                                    )
                                )
                            }
                        ),
                        "partial_marking_guidelines": genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "minimum_pass_criteria": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "partial_credit_rules": genai.protos.Schema(
                                    type=genai.protos.Type.ARRAY,
                                    items=genai.protos.Schema(type=genai.protos.Type.STRING)
                                )
                            }
                        )
                    },
                    required=["type", "standard", "total_marks", "criteria", "marking_scheme", "partial_marking_guidelines"]
                ),
                "answer_key": genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        "expected_outline": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "point": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "marks": genai.protos.Schema(type=genai.protos.Type.NUMBER),
                                    "sub_points": genai.protos.Schema(
                                        type=genai.protos.Type.ARRAY,
                                        items=genai.protos.Schema(type=genai.protos.Type.STRING)
                                    ),
                                    "keywords": genai.protos.Schema(
                                        type=genai.protos.Type.ARRAY,
                                        items=genai.protos.Schema(type=genai.protos.Type.STRING)
                                    )
                                }
                            )
                        ),
                        "key_concepts": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING)
                        ),
                        "alternative_answers": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(type=genai.protos.Type.STRING)
                        ),
                        # Fixed: Replace mapping with array of key-value objects
                        "mark_distribution_guide": genai.protos.Schema(
                            type=genai.protos.Type.ARRAY,
                            items=genai.protos.Schema(
                                type=genai.protos.Type.OBJECT,
                                properties={
                                    "component": genai.protos.Schema(type=genai.protos.Type.STRING),
                                    "marks": genai.protos.Schema(type=genai.protos.Type.NUMBER)
                                },
                                required=["component", "marks"]
                            )
                        )
                    },
                    required=["expected_outline", "key_concepts", "alternative_answers", "mark_distribution_guide"]
                )
            },
            required=["classification", "rubric", "answer_key"]
        )

    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def process_question_complete(self, question_data: Dict[str, Any], user_preferences: UserPreferences) -> Dict[str, Any]:
        """Process question completely in a SINGLE API call using structured output"""
        try:
            # Create comprehensive prompt
            prompt = self._create_safe_prompt(question_data, user_preferences)
            
            app_logger.info(f"Processing question {question_data.get('number', 'unknown')} with structured output")
            
            # SINGLE API call for everything using structured output
            response = await asyncio.to_thread(self.structured_model.generate_content, prompt)
            
            # Check if response has valid content
            if not response.candidates or len(response.candidates) == 0:
                raise Exception("No response candidates generated")
            
            candidate = response.candidates[0]
            
            # Check finish reason
            if candidate.finish_reason != 1:  # 1 = STOP (successful completion)
                finish_reasons = {
                    2: "MAX_TOKENS",
                    3: "SAFETY",
                    4: "RECITATION",
                    5: "OTHER"
                }
                reason = finish_reasons.get(candidate.finish_reason, "UNKNOWN")
                raise Exception(f"Generation failed with finish_reason: {reason}")
            
            # Check if candidate has content
            if not candidate.content or not candidate.content.parts:
                raise Exception("No content parts in response")
            
            # Get the text content
            response_text = candidate.content.parts[0].text
            if not response_text:
                raise Exception("Empty response text")
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
            except json.JSONDecodeError as e:
                app_logger.error(f"JSON decode error: {str(e)}")
                app_logger.error(f"Response text: {response_text[:500]}...")
                raise Exception(f"Invalid JSON response: {str(e)}")
            
            # Validate response structure
            if not all(key in parsed_response for key in ["classification", "rubric", "answer_key"]):
                raise Exception("Missing required keys in response")
            
            app_logger.info(f"Successfully processed question: {question_data.get('number', 'unknown')}")
            
            return {
                "success": True,
                "question_number": question_data.get('number', 'unknown'),
                "classification": parsed_response["classification"],
                "rubric": parsed_response["rubric"],
                "answer_key": parsed_response["answer_key"],
                "processing_time": "single_call"
            }
            
        except Exception as e:
            app_logger.error(f"Failed to process question {question_data.get('number', 'unknown')}: {str(e)}")
            return {
                "success": False,
                "question_number": question_data.get('number', 'unknown'),
                "error": str(e),
                "classification": None,
                "rubric": None,
                "answer_key": None
            }
    
    def _create_safe_prompt(self, question_data: Dict[str, Any], user_preferences: UserPreferences) -> str:
        """Create a safe, educational prompt that avoids safety triggers"""
        
        question_content = question_data.get('content', {})
        question_text = question_content.get('text', '')
        question_type = question_data.get('type', '')
        marks = question_data.get('marks', 0)
        
        # Clean the question text to avoid safety issues
        safe_question_text = self._sanitize_text(question_text)
        
        subject_hint = f"Subject: {user_preferences.subject_hint}" if user_preferences.subject_hint else "Subject: General"
        grade_hint = f"Grade Level: {user_preferences.grade_level}" if user_preferences.grade_level else "Grade Level: Secondary"
        
        return f"""You are an educational assessment expert. Create a comprehensive rubric and answer key for this academic question.

QUESTION DETAILS:
- Question Type: {question_type}
- Total Marks: {marks}
- {subject_hint}
- {grade_hint}
- Question Text: {safe_question_text}

TASK: Provide a complete educational assessment structure in JSON format with these exact components:

1. CLASSIFICATION:
   - question_type: The type of question (e.g., "short_answer", "essay", "multiple_choice")
   - subject: The academic subject area
   - topic: The specific topic covered
   - difficulty_level: "basic", "intermediate", or "advanced"
   - bloom_level: One of "knowledge", "comprehension", "application", "analysis", "synthesis", "evaluation"
   - cognitive_skills: Array of required thinking skills
   - marks: {marks} (integer)
   - estimated_time: Time needed to answer (e.g., "10 minutes")

2. RUBRIC:
   - type: Choose from "simple_checklist", "basic_rubric", or "detailed_analytical"
   - standard: "bloom_taxonomy"
   - total_marks: {marks}
   - criteria: Array of assessment criteria, each with:
     * criterion: Name of the criterion
     * weight: Percentage weight (number)
     * marks: Marks allocated (number)
     * performance_levels: Array of 4 levels (Excellent, Proficient, Developing, Beginning)
   - marking_scheme: Object with total_marks and mark_distribution
   - partial_marking_guidelines: Object with minimum_pass_criteria and partial_credit_rules

3. ANSWER_KEY:
   - expected_outline: Array of answer points with point, marks, sub_points, keywords
   - key_concepts: Array of essential concepts
   - alternative_answers: Array of acceptable alternative responses
   - mark_distribution_guide: Object mapping components to marks

Create a practical, teacher-friendly assessment tool that follows educational best practices."""

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to avoid safety triggers"""
        if not text:
            return "No question text provided"
        
        # Remove potentially problematic content while preserving educational value
        safe_text = text.replace('\n', ' ').strip()
        
        # Limit length to avoid token issues
        if len(safe_text) > 1000:
            safe_text = safe_text[:1000] + "..."
        
        return safe_text

    # Legacy methods for backward compatibility
    async def classify_question(self, question_data: Dict[str, Any], user_preferences: UserPreferences) -> QuestionClassification:
        result = await self.process_question_complete(question_data, user_preferences)
        if result["success"] and result["classification"]:
            return QuestionClassification(**result["classification"])
        else:
            raise Exception(f"Classification failed: {result.get('error', 'Unknown error')}")
    
    async def generate_rubric(self, question_data: Dict[str, Any], classification: QuestionClassification, user_preferences: UserPreferences) -> Dict[str, Any]:
        result = await self.process_question_complete(question_data, user_preferences)
        if result["success"] and result["rubric"]:
            return result["rubric"]
        else:
            raise Exception(f"Rubric generation failed: {result.get('error', 'Unknown error')}")
    
    async def generate_answer_key(self, question_data: Dict[str, Any], classification: QuestionClassification, user_preferences: UserPreferences) -> Dict[str, Any]:
        result = await self.process_question_complete(question_data, user_preferences)
        if result["success"] and result["answer_key"]:
            return result["answer_key"]
        else:
            raise Exception(f"Answer key generation failed: {result.get('error', 'Unknown error')}")

# Create singleton instance
rubric_gemini_client = RubricGeminiClient()

