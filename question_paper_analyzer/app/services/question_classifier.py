import json
from typing import Dict, List
from app.utils.logger import app_logger
from pathlib import Path

class QuestionClassifier:
    def __init__(self):
        self.question_types = self._load_question_types()
    
    def _load_question_types(self) -> Dict:
        """Load question types from JSON file"""
        try:
            types_file = Path(__file__).parent.parent.parent / "data" / "question_types.json"
            with open(types_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            app_logger.info(f"Loaded {len(data['question_types'])} question types")
            return data
        except Exception as e:
            app_logger.error(f"Failed to load question types: {str(e)}")
            raise
    
    def get_question_types_for_prompt(self) -> Dict:
        """Get question types formatted for Gemini prompt"""
        return self.question_types
    
    def validate_question_type(self, question_type: str) -> bool:
        """Validate if a question type exists in our definitions"""
        valid_types = [qt["type"] for qt in self.question_types["question_types"]]
        return question_type in valid_types
    
    def get_type_description(self, question_type: str) -> str:
        """Get description for a specific question type"""
        for qt in self.question_types["question_types"]:
            if qt["type"] == question_type:
                return qt["identify"]
        return "Unknown question type"

question_classifier = QuestionClassifier()
