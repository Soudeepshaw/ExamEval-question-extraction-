from typing import List, Dict, Any, Tuple
from app.utils.logger import app_logger
from app.models.rubric_schemas import UserPreferences

class QuestionParser:
    """Parses enhanced API response and prepares questions for rubric generation"""
    
    def __init__(self):
        pass
    
    def parse_enhanced_response(self, enhanced_response: Dict[str, Any]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Parse enhanced API response and extract questions with section context"""
        
        try:
            questions_with_sections = []
            
            sections = enhanced_response.get('sections', [])
            app_logger.info(f"Parsing {len(sections)} sections from enhanced response")
            
            for section in sections:
                section_data = {
                    'name': section.get('name', 'Unknown Section'),
                    'instruction': section.get('instruction'),
                    'total_marks': section.get('total_marks'),
                    'time_allocation': section.get('time_allocation'),
                    'optional_between': section.get('optional_between', False),
                    'optional_with': section.get('optional_with')
                }
                
                questions = section.get('questions', [])
                app_logger.info(f"Processing {len(questions)} questions in section {section_data['name']}")
                
                for question in questions:
                    # Process main question
                    question_data = self._prepare_question_data(question, section_data)
                    questions_with_sections.append((question_data, section_data))
                    
                    # Process subquestions if any
                    subquestions = question.get('subquestions', [])
                    for subquestion in subquestions:
                        subquestion_data = self._prepare_subquestion_data(subquestion, question, section_data)
                        questions_with_sections.append((subquestion_data, section_data))
            
            app_logger.info(f"Parsed total of {len(questions_with_sections)} questions/subquestions")
            return questions_with_sections
            
        except Exception as e:
            app_logger.error(f"Failed to parse enhanced response: {str(e)}")
            raise
    
    def _prepare_question_data(self, question: Dict[str, Any], section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare question data for processing"""
        
        return {
            'number': question.get('number', 'Unknown'),
            'type': question.get('type', 'unknown'),
            'content': question.get('content', {}),
            'marks': question.get('marks', 0),
            'optional': question.get('optional', False),
            'optional_with': question.get('optional_with'),
            'options': question.get('options'),
            'column_a': question.get('column_a'),
            'column_b': question.get('column_b'),
            'blanks_count': question.get('blanks_count'),
            'items_to_order': question.get('items_to_order'),
            'passage': question.get('passage'),
            'case_study_text': question.get('case_study_text'),
            'time_suggested': question.get('time_suggested'),
            'is_subquestion': False,
            'parent_question': None,
            'section_name': section_data['name']
        }
    
    def _prepare_subquestion_data(self, subquestion: Dict[str, Any], parent_question: Dict[str, Any], section_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare subquestion data for processing"""
        
        return {
            'number': f"{parent_question.get('number', 'Unknown')}{subquestion.get('label', '')}",
            'type': subquestion.get('type', 'unknown'),
            'content': subquestion.get('content', {}),
            'marks': subquestion.get('marks', 0),
            'optional': subquestion.get('optional', False),
            'optional_group': subquestion.get('optional_group'),
            'options': subquestion.get('options'),
            'column_a': subquestion.get('column_a'),
            'column_b': subquestion.get('column_b'),
            'blanks_count': subquestion.get('blanks_count'),
            'items_to_order': subquestion.get('items_to_order'),
            'is_subquestion': True,
            'parent_question': parent_question.get('number', 'Unknown'),
            'subquestion_label': subquestion.get('label', ''),
            'section_name': section_data['name']
        }
    
    def validate_questions(self, questions_data: List[Tuple[Dict[str, Any], Dict[str, Any]]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Validate and filter questions for processing"""
        
        valid_questions = []
        
        for question_data, section_data in questions_data:
            try:
                # Basic validation
                if not question_data.get('content', {}).get('text', '').strip():
                    app_logger.warning(f"Skipping question {question_data.get('number')} - no content text")
                    continue
                
                if question_data.get('marks', 0) <= 0:
                    app_logger.warning(f"Skipping question {question_data.get('number')} - no marks allocated")
                    continue
                
                valid_questions.append((question_data, section_data))
                
            except Exception as e:
                app_logger.error(f"Error validating question {question_data.get('number', 'unknown')}: {str(e)}")
                continue
        
        app_logger.info(f"Validated {len(valid_questions)} out of {len(questions_data)} questions")
        return valid_questions

# Global parser instance
question_parser = QuestionParser()
