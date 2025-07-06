import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.utils.logger import app_logger
from typing import Optional, Dict, Any
import json
import re

class GeminiClient:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Use the latest model that supports structured output
        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config={
                "response_mime_type": "application/json"
            }
        )
        
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10)
    )
    async def upload_file(self, file_path: str, mime_type: str = "application/pdf") -> Optional[object]:
        """Upload file to Gemini and return file object"""
        try:
            app_logger.info(f"Uploading file to Gemini: {file_path}")
            uploaded_file = genai.upload_file(file_path, mime_type=mime_type)
            
            # Wait for file processing to complete
            import time
            while uploaded_file.state.name == "PROCESSING":
                app_logger.info("File is still processing...")
                time.sleep(2)
                uploaded_file = genai.get_file(uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                raise Exception(f"File processing failed: {uploaded_file.state}")
                
            app_logger.info(f"File uploaded and processed successfully: {uploaded_file.uri}")
            return uploaded_file
        except Exception as e:
            app_logger.error(f"Failed to upload file to Gemini: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10)
    )
    async def analyze_structure(self, uploaded_file: object, question_types: dict) -> dict:
        """Analyze question paper structure using Gemini with structured output"""
        try:
            prompt = self._create_structure_analysis_prompt(question_types)
            
            app_logger.info("Sending structure analysis request to Gemini")
            
            response = self.model.generate_content([
                uploaded_file,
                prompt
            ])
            
            app_logger.info("Received structure response from Gemini")
            
            return self._parse_json_response(response)
            
        except Exception as e:
            app_logger.error(f"Failed to analyze structure: {str(e)}")
            raise
    
    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=settings.RETRY_DELAY, max=10)
    )
    async def extract_content(self, uploaded_file: object, structure: dict, question_types: dict) -> dict:
        """Extract question content and merge with structure"""
        try:
            prompt = self._create_content_extraction_prompt(structure, question_types)
            
            app_logger.info("Sending content extraction request to Gemini")
            
            response = self.model.generate_content([
                uploaded_file,
                prompt
            ])
            
            app_logger.info("Received content response from Gemini")
            
            parsed_response = self._parse_json_response(response)
            
            # Post-process the response to ensure data integrity
            processed_response = self._post_process_content_response(parsed_response)
            
            return processed_response
            
        except Exception as e:
            app_logger.error(f"Failed to extract content: {str(e)}")
            raise
    
    def _post_process_content_response(self, response: dict) -> dict:
        """Post-process content response to ensure data integrity"""
        try:
            app_logger.info("Post-processing content response...")
            
            # Ensure summary has required fields
            if 'summary' in response:
                summary = response['summary']
                
                # Calculate total_subquestions if missing
                if 'total_subquestions' not in summary:
                    total_subquestions = 0
                    for section in response.get('sections', []):
                        for question in section.get('questions', []):
                            subquestions = question.get('subquestions', [])
                            total_subquestions += len(subquestions)
                    summary['total_subquestions'] = total_subquestions
                
                # Ensure optional_structures exists
                if 'optional_structures' not in summary:
                    summary['optional_structures'] = []
                
                # Ensure question_type_distribution exists
                if 'question_type_distribution' not in summary:
                    summary['question_type_distribution'] = {}
            
            # Process sections to ensure data consistency
            if 'sections' in response:
                for section in response['sections']:
                    if 'questions' in section:
                        for question in section['questions']:
                            # Ensure content field exists
                            if 'content' not in question:
                                question['content'] = {'text': ''}
                            elif question['content'] is None:
                                question['content'] = {'text': ''}
                            
                            # Process subquestions
                            if 'subquestions' in question:
                                for subq in question['subquestions']:
                                    if 'content' not in subq:
                                        subq['content'] = {'text': ''}
                                    elif subq['content'] is None:
                                        subq['content'] = {'text': ''}
            
            app_logger.info("Content response post-processing completed")
            return response
            
        except Exception as e:
            app_logger.error(f"Error in post-processing content response: {str(e)}")
            return response
    
    def _parse_json_response(self, response) -> dict:
        """Parse JSON response from Gemini"""
        try:
            response_text = response.text.strip()
            
            if settings.LOG_LEVEL == "DEBUG":
                app_logger.debug(f"Raw Gemini response: {response_text[:1000]}...")
            
            # Clean up markdown formatting if present
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            
            try:
                parsed_json = json.loads(response_text)
                app_logger.info("Successfully parsed JSON response from Gemini")
                return parsed_json
            except json.JSONDecodeError as json_error:
                app_logger.warning(f"Direct JSON parsing failed: {str(json_error)}")
                
                # Try to extract JSON from the response using regex
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group())
                        app_logger.info("Successfully extracted and parsed JSON from response")
                        return parsed_json
                    except json.JSONDecodeError:
                        pass
                
                # Try to fix common JSON issues
                fixed_json = self._fix_common_json_issues(response_text)
                if fixed_json:
                    try:
                        parsed_json = json.loads(fixed_json)
                        app_logger.info("Successfully parsed JSON after fixing common issues")
                        return parsed_json
                    except json.JSONDecodeError:
                        pass
                
                # If all else fails, raise the original error
                raise json.JSONDecodeError("No valid JSON found in response", response_text, 0)
                    
        except json.JSONDecodeError as e:
            app_logger.error(f"Failed to parse JSON response: {str(e)}")
            app_logger.error(f"Raw response: {response.text}")
            raise
        except Exception as e:
            app_logger.error(f"Unexpected error parsing response: {str(e)}")
            raise
    
    def _fix_common_json_issues(self, json_text: str) -> Optional[str]:
        """Attempt to fix common JSON formatting issues"""
        try:
            # Remove trailing commas
            json_text = re.sub(r',\s*}', '}', json_text)
            json_text = re.sub(r',\s*]', ']', json_text)
            
            # Fix unescaped quotes in strings
            json_text = re.sub(r'(?<!\\)"(?=.*")', '\\"', json_text)
            
            return json_text
        except Exception:
            return None
    
    def _create_structure_analysis_prompt(self, question_types: dict) -> str:
        """Create structured prompt for question paper structure analysis"""
        
        question_types_str = json.dumps(question_types, indent=2)
        
        return f"""
You are an expert at analyzing question paper structures. Analyze this PDF question paper and extract ONLY the structural metadata - do not include any question text content.

QUESTION TYPES REFERENCE:
{question_types_str}

ANALYSIS REQUIREMENTS:
1. Identify all sections (Section A, Section B, etc.)
2. Extract question numbering patterns (1, 2, 3 or Q1, Q2, etc.)
3. Identify subquestions (a, b, c or i, ii, iii, etc.)
4. Detect optional logic at ALL levels:
   - Section level: "Attempt Section A OR Section B"
   - Question level: "Answer any 5 out of 7 questions"
   - Subquestion level: "Attempt any 2 out of 3 parts"
5. Classify each question/subquestion type using the provided question types reference
6. Extract section-level instructions
7. Identify marks allocation if visible
8. Note exam duration and other metadata

IMPORTANT RULES:
- DO NOT extract question text content
- Focus only on structure, numbering, and metadata
- Classify question types based on visual layout and instruction patterns
- Pay attention to optional choice indicators like "OR", "any X out of Y", "choose", "select"
- Look for section headers, question numbers, and subquestion labels
- Return ONLY valid JSON without any markdown formatting

JSON SCHEMA:
{{
  "sections": [
    {{
      "name": "string",
      "optional_between": "boolean",
      "optional_with": "string or null",
      "instruction": "string",
      "questions": [
        {{
          "number": "string",
          "type": "string",
          "optional": "boolean",
          "optional_with": "string or null",
          "marks": "number or null",
          "subquestions": [
            {{
              "label": "string",
              "type": "string",
              "optional": "boolean",
              "optional_group": "string or null",
              "marks": "number or null"
            }}
          ]
        }}
      ],
      "total_marks": "number or null",
      "time_allocation": "string or null"
    }}
  ],
  "summary": {{
    "total_sections": "number",
    "total_questions": "number",
    "total_subquestions": "number",
    "optional_structures": ["array of strings"],
    "question_type_distribution": {{}},
    "total_marks": "number or null",
    "exam_duration": "string or null"
  }},
  "metadata": {{
    "exam_board": "string or null",
    "subject": "string or null",
    "class_grade": "string or null",
    "exam_type": "string or null",
    "date": "string or null"
  }}
}}

Analyze the uploaded PDF and return the structured JSON response following the exact schema above.
"""

    def _create_content_extraction_prompt(self, structure: dict, question_types: dict) -> str:
        """Create prompt for extracting question content based on structure"""
        
        structure_str = json.dumps(structure, indent=2)
        question_types_str = json.dumps(question_types, indent=2)
        
        return f"""
You are an expert at extracting question content from question papers. Based on the provided structure, extract ALL the textual content, images, diagrams, and other elements for each question and subquestion.

STRUCTURE TO FOLLOW:
{structure_str}

QUESTION TYPES REFERENCE:
{question_types_str}

CONTENT EXTRACTION REQUIREMENTS:
1. Extract the complete question text for each question and subquestion
2. For Multiple Choice Questions: Extract all options (A, B, C, D, etc.)
3. For Matching Questions: Extract both columns with all items
4. For Fill in the Blanks: Extract the sentence with blanks and count them
5. For Comprehension: Extract the passage and all related questions
6. For Case Studies: Extract the scenario text and all questions
7. For Image-based questions: Provide detailed descriptions of images, diagrams, charts
8. For Mathematical questions: Extract formulas, equations, and mathematical expressions
9. For Code-based questions: Extract code snippets and programming content
10. Extract any tables, data, or additional context

SPECIAL HANDLING:
- Images: Provide detailed descriptions of what's shown
- Diagrams: Describe the diagram structure and labels
- Charts/Graphs: Describe data representation and axes
- Tables: Extract table content in structured format
- Mathematical formulas: Preserve mathematical notation
- Code snippets: Preserve code formatting and syntax

IMPORTANT RULES:
- Extract COMPLETE question text, not summaries
- Maintain the exact structure provided
- For each question/subquestion, provide comprehensive content
- Describe images and diagrams in detail
- Preserve formatting for mathematical expressions
- Return ONLY valid JSON without markdown formatting
- Ensure all required fields are present with appropriate default values

JSON SCHEMA:
{{
  "sections": [
    {{
      "name": "string",
      "optional_between": "boolean",
      "optional_with": "string or null",
      "instruction": "string",
      "questions": [
        {{
          "number": "string",
          "type": "string",
          "optional": "boolean",
          "optional_with": "string or null",
          "content": {{
            "text": "string",
            "images": [
              {{
                "description": "string",
                "position": "string",
                "alt_text": "string or null"
              }}
            ],
            "diagrams": ["array of diagram descriptions"],
            "tables": ["array of table content"],
            "formulas": ["array of mathematical formulas"],
            "code_snippets": ["array of code blocks"],
            "additional_context": "string or null"
          }},
          "options": ["array of options for MCQ"],
          "column_a": ["array for matching questions"],
          "column_b": ["array for matching questions"],
          "blanks_count": "number for fill in blanks",
          "items_to_order": ["array for ordering questions"],
          "passage": "string for comprehension",
          "case_study_text": "string for case studies",
          "marks": "number or null",
          "time_suggested": "string or null",
          "subquestions": [
            {{
              "label": "string",
              "type": "string",
              "optional": "boolean",
              "optional_group": "string or null",
              "content": {{
                "text": "string",
                "images": [{{...}}],
                "diagrams": ["array"],
                "tables": ["array"],
                "formulas": ["array"],
                "code_snippets": ["array"],
                "additional_context": "string or null"
              }},
              "options": ["array or null"],
              "column_a": ["array or null"],
              "column_b": ["array or null"],
              "blanks_count": "number or null",
              "items_to_order": ["array or null"],
              "marks": "number or null"
            }}
          ]
        }}
      ],
      "total_marks": "number or null",
      "time_allocation": "string or null"
    }}
  ],
  "summary": {{
    "total_sections": "number",
    "total_questions": "number",
    "total_subquestions": "number",
    "optional_structures": ["array"],
    "question_type_distribution": {{}},
    "total_marks": "number or null",
    "exam_duration": "string or null",
    "difficulty_level": "string or null"
  }},
  "metadata": {{
    "exam_board": "string or null",
    "subject": "string or null",
    "class_grade": "string or null",
    "exam_type": "string or null",
    "date": "string or null"
  }}
}}

Extract all content from the uploaded PDF following the structure and return the complete JSON response.
"""

gemini_client = GeminiClient()

