from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime

class UserPreferences(BaseModel):
    subject_hint: Optional[str] = Field(None, description="Optional subject hint from user")
    grade_level: Optional[str] = Field(None, description="Grade/class level")
    quality_mode: Literal["high", "fast"] = Field("high", description="Processing quality mode")
    rubric_standard: Literal["bloom_taxonomy", "basic"] = Field("bloom_taxonomy", description="Educational standard to follow")

class QuestionClassification(BaseModel):
    question_type: str = Field(..., description="Type of question")
    subject: str = Field(..., description="Subject area")
    topic: str = Field(..., description="Specific topic")
    subtopic: Optional[str] = Field(None, description="Specific subtopic")
    difficulty_level: str = Field(..., description="Difficulty level")
    bloom_level: Literal['knowledge', 'comprehension', 'application', 'analysis', 'synthesis', 'evaluation'] = Field(..., description="Bloom's taxonomy level")
    cognitive_skills: List[str] = Field(default_factory=list, description="Required cognitive skills")
    grade_level: Optional[str] = Field(None, description="Appropriate grade level")
    marks: int = Field(..., description="Marks allocated")
    estimated_time: str = Field(..., description="Estimated time to complete")

    @validator('bloom_level', pre=True)
    def normalize_bloom_level(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('difficulty_level', pre=True)
    def normalize_difficulty_level(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @validator('question_type', pre=True)
    def normalize_question_type(cls, v):
        if isinstance(v, str):
            return v.lower().replace(' ', '_').replace('-', '_')
        return v

    @validator('cognitive_skills', pre=True)
    def ensure_cognitive_skills_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return v

class AnswerPoint(BaseModel):
    point: str = Field(..., description="Answer key point")
    marks: float = Field(..., description="Marks for this point")
    sub_points: List[str] = Field(default_factory=list, description="Sub-points")
    keywords: List[str] = Field(..., description="Key terms/concepts")

class PerformanceLevel(BaseModel):
    level: Literal["Excellent", "Proficient", "Developing", "Beginning"] = Field(..., description="Performance level")
    marks_range: str = Field(..., description="Mark range for this level")
    descriptor: str = Field(..., description="Performance descriptor")
    indicators: List[str] = Field(default_factory=list, description="Performance indicators")

class RubricCriterion(BaseModel):
    criterion: str = Field(..., description="Criterion name")
    weight: float = Field(..., description="Weight percentage")
    marks: float = Field(..., description="Marks allocated")
    performance_levels: List[PerformanceLevel] = Field(..., description="Performance levels")

class MarkingScheme(BaseModel):
    total_marks: int = Field(..., description="Total marks")
    mark_distribution: Union[Dict[str, float], List[Dict[str, Any]]] = Field(..., description="Mark distribution by component")
    
    @validator('mark_distribution', pre=True)
    def convert_mark_distribution(cls, v):
        """Convert array format to dict format if needed"""
        if isinstance(v, list):
            # Convert array of {component, marks} to dict
            result = {}
            for item in v:
                if isinstance(item, dict) and 'component' in item and 'marks' in item:
                    result[item['component']] = float(item['marks'])
            return result
        return v

class PartialMarkingGuidelines(BaseModel):
    minimum_pass_criteria: str = Field(..., description="Minimum criteria for passing")
    partial_credit_rules: List[str] = Field(..., description="Rules for partial credit")

class Rubric(BaseModel):
    type: Literal["simple_checklist", "basic_rubric", "detailed_analytical", "comprehensive"] = Field(..., description="Rubric type")
    standard: str = Field(..., description="Educational standard used")
    criteria: List[RubricCriterion] = Field(..., description="Rubric criteria")
    marking_scheme: MarkingScheme = Field(..., description="Marking scheme")
    partial_marking_guidelines: PartialMarkingGuidelines = Field(..., description="Partial marking guidelines")

class WordCountExpectation(BaseModel):
    minimum: int = Field(..., description="Minimum word count")
    optimal: int = Field(..., description="Optimal word count")
    maximum: int = Field(..., description="Maximum word count")

class AnswerKey(BaseModel):
    expected_outline: List[AnswerPoint] = Field(..., description="Expected answer outline")
    key_concepts: List[str] = Field(..., description="Key concepts that must be mentioned")
    alternative_answers: List[str] = Field(default_factory=list, description="Alternative acceptable answers")
    word_count_expectation: Optional[WordCountExpectation] = Field(None, description="Word count expectations")
    mark_distribution_guide: Union[Dict[str, float], List[Dict[str, Any]]] = Field(..., description="Mark distribution guide")
    
    @validator('mark_distribution_guide', pre=True)
    def convert_mark_distribution_guide(cls, v):
        """Convert array format to dict format if needed"""
        if isinstance(v, list):
            # Convert array of {component, marks} to dict
            result = {}
            for item in v:
                if isinstance(item, dict) and 'component' in item and 'marks' in item:
                    result[item['component']] = float(item['marks'])
            return result
        return v

class TimeAllocation(BaseModel):
    reading_question: str = Field(..., description="Time to read question")
    evaluation_time: str = Field(..., description="Time to evaluate answer")
    feedback_writing: str = Field(..., description="Time to write feedback")

class EvaluationGuidelines(BaseModel):
    common_mistakes: List[str] = Field(..., description="Common student mistakes")
    evaluation_tips: List[str] = Field(..., description="Tips for evaluation")
    time_allocation: TimeAllocation = Field(..., description="Time allocation for evaluation")
    red_flags: List[str] = Field(..., description="Red flags to watch for")

class QualityMetrics(BaseModel):
    rubric_completeness: int = Field(..., description="Rubric completeness percentage")
    standard_compliance: str = Field(..., description="Educational standard compliance")
    validation_status: Literal["passed", "failed", "warning"] = Field(..., description="Validation status")
    processing_time: float = Field(..., description="Processing time in seconds")
    confidence_score: float = Field(..., description="AI confidence score")

class SectionMetadata(BaseModel):
    section_name: str = Field(..., description="Section name")
    section_instruction: Optional[str] = Field(None, description="Section instructions")
    section_marks: Optional[int] = Field(None, description="Total section marks")
    section_time_allocation: Optional[str] = Field(None, description="Section time allocation")

class QuestionMetadata(BaseModel):
    question_number: str = Field(..., description="Question number")
    question_id: str = Field(..., description="Unique question identifier")
    is_optional: bool = Field(default=False, description="Whether question is optional")
    optional_group: Optional[str] = Field(None, description="Optional group if applicable")
    subquestion_label: Optional[str] = Field(None, description="Subquestion label if applicable")

class RubricResponse(BaseModel):
    section_metadata: SectionMetadata = Field(..., description="Section metadata")
    question_metadata: QuestionMetadata = Field(..., description="Question metadata")
    classification: QuestionClassification = Field(..., description="Question classification")
    rubric: Rubric = Field(..., description="Generated rubric")
    answer_key: AnswerKey = Field(..., description="Answer key")
    evaluation_guidelines: EvaluationGuidelines = Field(..., description="Evaluation guidelines")
    quality_metrics: QualityMetrics = Field(..., description="Quality metrics")
    processing_status: Literal["completed", "failed", "partial"] = Field(..., description="Processing status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

class WebSocketMessage(BaseModel):
    type: Literal["progress", "question_complete", "section_complete", "error", "final_summary"] = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")

class ProgressUpdate(BaseModel):
    current_question: int = Field(..., description="Current question number")
    total_questions: int = Field(..., description="Total questions")
    section: str = Field(..., description="Current section")
    status: str = Field(..., description="Current processing status")
    estimated_remaining_time: Optional[int] = Field(None, description="Estimated remaining time in seconds")

class RubricGenerationRequest(BaseModel):
    enhanced_api_response: Dict[str, Any] = Field(..., description="Enhanced API response")
    user_preferences: UserPreferences = Field(default_factory=UserPreferences, description="User preferences")

class FinalSummary(BaseModel):
    total_questions_processed: int = Field(..., description="Total questions processed")
    successful_generations: int = Field(..., description="Successful rubric generations")
    failed_generations: int = Field(..., description="Failed generations")
    total_processing_time: float = Field(..., description="Total processing time")
    average_time_per_question: float = Field(..., description="Average time per question")
    quality_distribution: Dict[str, int] = Field(..., description="Quality score distribution")
