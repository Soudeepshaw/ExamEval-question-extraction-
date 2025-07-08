from typing import Dict, Any, List, Tuple
from app.models.rubric_schemas import RubricResponse, QualityMetrics
from app.utils.logger import app_logger

class RubricValidator:
    """Fast validator for optimized processing"""
    
    def __init__(self):
        # Simplified validation rules for speed
        self.validation_rules = {
            'marks_consistency': self._validate_marks_consistency,
            'basic_completeness': self._validate_basic_completeness,
            'performance_levels': self._validate_performance_levels
        }
    
    def validate_rubric_response(self, response: RubricResponse) -> Tuple[bool, List[str], float]:
        """Fast validation with essential checks only"""
        
        validation_errors = []
        quality_score = 1.0
        
        try:
            # Quick essential validations only
            for rule_name, rule_func in self.validation_rules.items():
                try:
                    is_valid, errors, score_penalty = rule_func(response)
                    
                    if not is_valid:
                        validation_errors.extend(errors)
                        quality_score -= score_penalty
                        
                except Exception as e:
                    app_logger.warning(f"Validation rule {rule_name} failed: {str(e)}")
                    quality_score -= 0.05  # Minor penalty for validation errors
            
            quality_score = max(0.0, min(1.0, quality_score))
            is_valid = len(validation_errors) == 0
            
            return is_valid, validation_errors, quality_score
            
        except Exception as e:
            app_logger.error(f"Validation error: {str(e)}")
            return False, [f"Validation error: {str(e)}"], 0.5
    
    def _validate_marks_consistency(self, response: RubricResponse) -> Tuple[bool, List[str], float]:
        """Quick marks validation"""
        errors = []
        
        try:
            total_marks = response.classification.marks
            rubric_marks = response.rubric.marking_scheme.total_marks
            
            if abs(total_marks - rubric_marks) > 0.1:
                errors.append(f"Mark mismatch: {total_marks} vs {rubric_marks}")
            
            return len(errors) == 0, errors, 0.2 if errors else 0.0
            
        except Exception as e:
            return False, [f"Marks validation error: {str(e)}"], 0.1
    
    def _validate_basic_completeness(self, response: RubricResponse) -> Tuple[bool, List[str], float]:
        """Quick completeness check"""
        errors = []
        
        try:
            if not response.rubric.criteria:
                errors.append("No rubric criteria")
            
            if not response.answer_key.expected_outline:
                errors.append("No answer key points")
            
            return len(errors) == 0, errors, 0.1 if errors else 0.0
            
        except Exception as e:
            return False, [f"Completeness validation error: {str(e)}"], 0.1
    
    def _validate_performance_levels(self, response: RubricResponse) -> Tuple[bool, List[str], float]:
        """Validate performance levels structure"""
        errors = []
        
        try:
            required_levels = {"Excellent", "Proficient", "Developing", "Beginning"}
            
            for criterion in response.rubric.criteria:
                existing_levels = {level.level for level in criterion.performance_levels}
                missing_levels = required_levels - existing_levels
                
                if missing_levels:
                    errors.append(f"Missing performance levels in {criterion.criterion}: {missing_levels}")
            
            return len(errors) == 0, errors, 0.1 if errors else 0.0
            
        except Exception as e:
            return False, [f"Performance levels validation error: {str(e)}"], 0.1

# Global validator instance
rubric_validator = RubricValidator()
