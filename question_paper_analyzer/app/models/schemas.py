from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator

class ImageDescription(BaseModel):
    description: str = Field(..., description="Description of the image content")
    position: str = Field(..., description="Position of image relative to question (before/after/inline)")
    alt_text: Optional[str] = Field(None, description="Alternative text if available")

class QuestionContent(BaseModel):
    text: Optional[str] = Field(None, description="The actual question text")
    images: Optional[List[ImageDescription]] = Field(None, description="Images associated with the question")
    diagrams: Optional[List[str]] = Field(None, description="Descriptions of diagrams or charts")
    tables: Optional[List[str]] = Field(None, description="Table content if present")
    formulas: Optional[List[str]] = Field(None, description="Mathematical formulas or equations")
    code_snippets: Optional[List[str]] = Field(None, description="Code blocks if present")
    additional_context: Optional[str] = Field(None, description="Any additional context or instructions")

    @validator('text', pre=True, always=True)
    def validate_text(cls, v):
        if v is None:
            return ""
        if isinstance(v, dict):
            return str(v.get('text', '')) or str(v)
        return str(v)

    @validator('diagrams', pre=True, always=True)
    def validate_diagrams(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract description from dict structure
                    result.append(item.get('description', str(item)))
                else:
                    result.append(str(item))
            return result
        elif isinstance(v, dict):
            return [v.get('description', str(v))]
        return [str(v)]

    @validator('tables', pre=True, always=True)
    def validate_tables(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Convert table dict to string representation
                    if 'headers' in item:
                        headers = item.get('headers', [])
                        rows = item.get('rows', [])
                        table_str = f"Headers: {', '.join(map(str, headers))}"
                        if rows:
                            row_strings = []
                            for row in rows:
                                if isinstance(row, list):
                                    row_strings.append(', '.join(map(str, row)))
                                else:
                                    row_strings.append(str(row))
                            table_str += f"\nRows: {'; '.join(row_strings)}"
                        result.append(table_str)
                    else:
                        result.append(str(item))
                else:
                    result.append(str(item))
            return result
        elif isinstance(v, dict):
            if 'headers' in v:
                headers = v.get('headers', [])
                rows = v.get('rows', [])
                table_str = f"Headers: {', '.join(map(str, headers))}"
                if rows:
                    row_strings = []
                    for row in rows:
                        if isinstance(row, list):
                            row_strings.append(', '.join(map(str, row)))
                        else:
                            row_strings.append(str(row))
                    table_str += f"\nRows: {'; '.join(row_strings)}"
                return [table_str]
            return [str(v)]
        return [str(v)]

    @validator('additional_context', pre=True, always=True)
    def validate_additional_context(cls, v):
        if v is None:
            return None
        if isinstance(v, dict):
            # Handle assertion-reason type questions
            if 'assertion' in v and 'reason' in v:
                return f"Assertion: {v['assertion']}\nReason: {v['reason']}"
            return str(v)
        return str(v)

    @validator('images', pre=True, always=True)
    def validate_images(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Ensure required fields are present
                    description = item.get('description', 'Image description not available')
                    position = item.get('position', 'inline')
                    alt_text = item.get('alt_text')
                    result.append(ImageDescription(
                        description=description,
                        position=position,
                        alt_text=alt_text
                    ))
                else:
                    result.append(ImageDescription(
                        description=str(item),
                        position='inline'
                    ))
            return result
        return []

    @validator('formulas', pre=True, always=True)
    def validate_formulas(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]

    @validator('code_snippets', pre=True, always=True)
    def validate_code_snippets(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]

class SubQuestionContent(BaseModel):
    label: str = Field(..., description="Subquestion label like (a), (i), etc.")
    type: str = Field(..., description="Question type classification")
    optional: bool = Field(default=False, description="Whether this subquestion is optional")
    optional_group: Optional[str] = Field(None, description="Optional group description")
    content: QuestionContent = Field(..., description="The actual content of the subquestion")
    # For multiple choice questions
    options: Optional[List[str]] = Field(None, description="Answer options for MCQ")
    # For matching questions
    column_a: Optional[List[str]] = Field(None, description="Left column items for matching")
    column_b: Optional[List[str]] = Field(None, description="Right column items for matching")
    # For fill in the blanks
    blanks_count: Optional[int] = Field(None, description="Number of blanks to fill")
    # For ordering questions
    items_to_order: Optional[List[str]] = Field(None, description="Items to be arranged in order")

    @validator('content', pre=True, always=True)
    def ensure_content(cls, v):
        if v is None:
            return QuestionContent(text="")
        if isinstance(v, dict):
            return QuestionContent(**v)
        return v

    @validator('options', pre=True, always=True)
    def validate_options(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract option text from structured format
                    if 'label' in item and 'text' in item:
                        result.append(f"{item['label']}) {item['text']}")
                    elif 'label' in item and 'content' in item:
                        content_text = item['content'].get('text', '') if isinstance(item['content'], dict) else str(item['content'])
                        result.append(f"{item['label']}) {content_text}")
                    else:
                        result.append(str(item))
                else:
                    result.append(str(item))
            return result
        return [str(v)]

class QuestionWithContent(BaseModel):
    number: str = Field(..., description="Question number")
    type: str = Field(..., description="Question type classification")
    optional: bool = Field(default=False, description="Whether this question is optional")
    optional_with: Optional[str] = Field(None, description="Optional relationship description")
    content: Optional[QuestionContent] = Field(None, description="The actual content of the question")
    subquestions: Optional[List[SubQuestionContent]] = Field(None, description="List of subquestions with content")
    # Question-specific fields
    options: Optional[List[str]] = Field(None, description="Answer options for MCQ")
    column_a: Optional[List[str]] = Field(None, description="Left column for matching")
    column_b: Optional[List[str]] = Field(None, description="Right column for matching")
    blanks_count: Optional[int] = Field(None, description="Number of blanks")
    items_to_order: Optional[List[str]] = Field(None, description="Items to order")
    passage: Optional[str] = Field(None, description="Reading passage for comprehension questions")
    case_study_text: Optional[str] = Field(None, description="Case study scenario text")
    marks: Optional[int] = Field(None, description="Marks allocated to this question")
    time_suggested: Optional[str] = Field(None, description="Suggested time for this question")

    @validator('content', pre=True, always=True)
    def ensure_content(cls, v):
        if v is None:
            return QuestionContent(text="")
        if isinstance(v, dict):
            return QuestionContent(**v)
        return v

    @validator('options', pre=True, always=True)
    def validate_options(cls, v):
        if v is None:
            return None
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Extract option text from structured format
                    if 'label' in item and 'text' in item:
                        result.append(f"{item['label']}) {item['text']}")
                    elif 'label' in item and 'content' in item:
                        content_text = item['content'].get('text', '') if isinstance(item['content'], dict) else str(item['content'])
                        result.append(f"{item['label']}) {content_text}")
                    else:
                        result.append(str(item))
                else:
                    result.append(str(item))
            return result
        return [str(v)]

    @validator('subquestions', pre=True, always=True)
    def validate_subquestions(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Ensure content exists
                    if 'content' not in item:
                        item['content'] = QuestionContent(text="")
                    result.append(SubQuestionContent(**item))
                else:
                    result.append(item)
            return result
        return []

class SectionWithContent(BaseModel):
    name: str = Field(..., description="Section name like 'Section A'")
    optional_between: bool = Field(default=False, description="Whether this section has optional choice")
    optional_with: Optional[str] = Field(None, description="Optional relationship description")
    instruction: Optional[str] = Field(None, description="Section-level instructions")
    questions: List[QuestionWithContent] = Field(..., description="List of questions with content")
    total_marks: Optional[int] = Field(None, description="Total marks for this section")
    time_allocation: Optional[str] = Field(None, description="Suggested time for this section")

    @validator('questions', pre=True, always=True)
    def validate_questions(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    # Ensure content exists
                    if 'content' not in item:
                        item['content'] = QuestionContent(text="")
                    result.append(QuestionWithContent(**item))
                else:
                    result.append(item)
            return result
        return []

class EnhancedSummary(BaseModel):
    total_sections: int = Field(..., description="Total number of sections")
    total_questions: int = Field(..., description="Total number of questions")
    total_subquestions: int = Field(default=0, description="Total number of subquestions")
    optional_structures: List[str] = Field(default=[], description="List of optional structure descriptions")
    question_type_distribution: Dict[str, int] = Field(..., description="Count of each question type")
    total_marks: Optional[int] = Field(None, description="Total marks for the paper")
    exam_duration: Optional[str] = Field(None, description="Total exam duration")
    difficulty_level: Optional[str] = Field(None, description="Estimated difficulty level")

    @validator('optional_structures', pre=True, always=True)
    def validate_optional_structures(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v]
        return [str(v)]

    @validator('question_type_distribution', pre=True, always=True)
    def validate_question_type_distribution(cls, v):
        if v is None:
            return {}
        if isinstance(v, dict):
            return {str(k): int(val) if isinstance(val, (int, float)) else 0 for k, val in v.items()}
        return {}

class EnhancedQuestionPaperStructure(BaseModel):
    sections: List[SectionWithContent] = Field(..., description="List of sections with content")
    summary: EnhancedSummary = Field(..., description="Enhanced summary statistics")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata like exam board, subject, etc.")

    @validator('sections', pre=True, always=True)
    def validate_sections(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, dict):
                    result.append(SectionWithContent(**item))
                else:
                    result.append(item)
            return result
        return []

    @validator('summary', pre=True, always=True)
    def validate_summary(cls, v):
        if v is None:
            return EnhancedSummary(
                total_sections=0,
                                total_subquestions=0,
                optional_structures=[],
                question_type_distribution={}
            )
        if isinstance(v, dict):
            return EnhancedSummary(**v)
        return v

class EnhancedAnalysisResponse(BaseModel):
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[EnhancedQuestionPaperStructure] = Field(None, description="Enhanced question paper data with content")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    processing_time: float = Field(..., description="Time taken for analysis in seconds")
    structure_extraction_time: float = Field(..., description="Time taken for structure extraction")
    content_extraction_time: float = Field(..., description="Time taken for content extraction")

# Keep original schemas for backward compatibility
class SubQuestion(BaseModel):
    label: str = Field(..., description="Subquestion label like (a), (i), etc.")
    type: str = Field(..., description="Question type classification")
    optional: bool = Field(default=False, description="Whether this subquestion is optional")
    optional_group: Optional[str] = Field(None, description="Optional group description")

class Question(BaseModel):
    number: str = Field(..., description="Question number")
    type: str = Field(..., description="Question type classification")
    optional: bool = Field(default=False, description="Whether this question is optional")
    optional_with: Optional[str] = Field(None, description="Optional relationship description")
    subquestions: Optional[List[SubQuestion]] = Field(None, description="List of subquestions")

class Section(BaseModel):
    name: str = Field(..., description="Section name like 'Section A'")
    optional_between: bool = Field(default=False, description="Whether this section has optional choice")
    optional_with: Optional[str] = Field(None, description="Optional relationship description")
    instruction: Optional[str] = Field(None, description="Section-level instructions")
    questions: List[Question] = Field(..., description="List of questions in this section")

class Summary(BaseModel):
    total_sections: int = Field(..., description="Total number of sections")
    total_questions: int = Field(..., description="Total number of questions")
    optional_structures: List[str] = Field(..., description="List of optional structure descriptions")

class QuestionPaperStructure(BaseModel):
    sections: List[Section] = Field(..., description="List of sections in the question paper")
    summary: Summary = Field(..., description="Summary statistics")

class AnalysisResponse(BaseModel):
    success: bool = Field(..., description="Whether the analysis was successful")
    data: Optional[QuestionPaperStructure] = Field(None, description="Structured question paper data")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    processing_time: float = Field(..., description="Time taken for analysis in seconds")

class ErrorResponse(BaseModel):
    success: bool = Field(default=False)
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

