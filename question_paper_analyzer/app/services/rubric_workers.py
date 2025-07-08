import asyncio
from typing import Dict, Any, List, Optional
from app.core.rubric_gemini_client import rubric_gemini_client
from app.models.rubric_schemas import (
    QuestionClassification, RubricResponse, UserPreferences,
    SectionMetadata, QuestionMetadata, Rubric, AnswerKey,
    EvaluationGuidelines, QualityMetrics, AnswerPoint,
    PerformanceLevel, RubricCriterion, MarkingScheme, PartialMarkingGuidelines,
    TimeAllocation
)
from app.utils.logger import app_logger
import time
from datetime import datetime

class RubricWorker:
    """Optimized worker for single API call processing"""
    
    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        self.gemini_client = rubric_gemini_client
    
    async def process_question(self, question_data: Dict[str, Any], section_data: Dict[str, Any], user_preferences: UserPreferences) -> RubricResponse:
        """Process question with SINGLE API call and proper error handling"""
        start_time = time.time()
        
        try:
            app_logger.info(f"Worker {self.worker_id} processing question {question_data.get('number')} with single API call")
            
            # SINGLE API call for everything
            result = await self.gemini_client.process_question_complete(question_data, user_preferences)
            
            if not result["success"]:
                raise Exception(result.get("error", "Processing failed"))
            
            # Safely create objects with validation
            classification = self._create_classification_safe(result["classification"], question_data)
            rubric = self._create_rubric_safe(result["rubric"], question_data)
            answer_key = self._create_answer_key_safe(result["answer_key"], question_data)
            
            # Generate evaluation guidelines (local processing - no API call)
            evaluation_guidelines = self._generate_evaluation_guidelines_fast(
                classification, result["rubric"], result["answer_key"]
            )
            
            processing_time = time.time() - start_time
            
            response = RubricResponse(
                section_metadata=self._create_section_metadata(section_data),
                question_metadata=self._create_question_metadata(question_data),
                classification=classification,
                rubric=rubric,
                answer_key=answer_key,
                evaluation_guidelines=evaluation_guidelines,
                quality_metrics=QualityMetrics(
                    rubric_completeness=100,
                    standard_compliance=user_preferences.rubric_standard,
                    validation_status="passed",
                    processing_time=processing_time,
                    confidence_score=0.95
                ),
                processing_status="completed"
            )
            
            app_logger.info(f"Worker {self.worker_id} completed question {question_data.get('number')} in {processing_time:.2f}s")
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            app_logger.error(f"Worker {self.worker_id} failed to process question {question_data.get('number')}: {str(e)}")
            return self._create_error_response(question_data, section_data, str(e), processing_time)
    
    def _create_classification_safe(self, classification_data: Dict[str, Any], question_data: Dict[str, Any]) -> QuestionClassification:
        """Safely create classification with defaults"""
        try:
            # Ensure all required fields are present
            safe_data = {
                "question_type": classification_data.get("question_type", question_data.get("type", "unknown")),
                "subject": classification_data.get("subject", "Unknown"),
                "topic": classification_data.get("topic", "Unknown"),
                "difficulty_level": classification_data.get("difficulty_level", "basic"),
                "bloom_level": classification_data.get("bloom_level", "knowledge"),
                "cognitive_skills": classification_data.get("cognitive_skills", ["recall"]),
                "marks": classification_data.get("marks", question_data.get("marks", 0)),
                "estimated_time": classification_data.get("estimated_time", "5 minutes")
            }
            return QuestionClassification(**safe_data)
        except Exception as e:
            app_logger.warning(f"Failed to create classification, using defaults: {str(e)}")
            return QuestionClassification(
                question_type=question_data.get("type", "unknown"),
                subject="Unknown",
                topic="Unknown",
                difficulty_level="basic",
                bloom_level="knowledge",
                cognitive_skills=["recall"],
                marks=question_data.get("marks", 0),
                estimated_time="5 minutes"
            )
    
    def _create_rubric_safe(self, rubric_data: Dict[str, Any], question_data: Dict[str, Any]) -> Rubric:
        """Safely create rubric with proper validation"""
        try:
            # Convert array format to dict format for mark_distribution
            if "marking_scheme" in rubric_data:
                marking_scheme = rubric_data["marking_scheme"]
                if "mark_distribution" in marking_scheme and isinstance(marking_scheme["mark_distribution"], list):
                    # Convert array to dict
                    mark_dist_dict = {}
                    for item in marking_scheme["mark_distribution"]:
                        if isinstance(item, dict) and "component" in item and "marks" in item:
                            mark_dist_dict[item["component"]] = float(item["marks"])
                    marking_scheme["mark_distribution"] = mark_dist_dict
            
            # Validate and fix rubric data structure
            validated_rubric_data = self._validate_rubric_structure(rubric_data, question_data)
            return Rubric(**validated_rubric_data)
        except Exception as e:
            app_logger.warning(f"Failed to create rubric from API response, creating default: {str(e)}")
            return self._create_default_rubric(question_data)
    
    def _validate_rubric_structure(self, rubric_data: Dict[str, Any], question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix rubric structure"""
        marks = question_data.get("marks", 0)
        
        # Ensure all required fields exist
        validated_data = {
            "type": rubric_data.get("type", "basic_rubric"),
            "standard": rubric_data.get("standard", "bloom_taxonomy"),
            "criteria": [],
            "marking_scheme": {
                "total_marks": rubric_data.get("total_marks", marks),
                "mark_distribution": {}
            },
            "partial_marking_guidelines": {
                "minimum_pass_criteria": rubric_data.get("partial_marking_guidelines", {}).get("minimum_pass_criteria", "Must attempt to answer the question"),
                "partial_credit_rules": rubric_data.get("partial_marking_guidelines", {}).get("partial_credit_rules", ["Partial credit for incomplete but correct information"])
            }
        }
        
        # Handle marking scheme
        marking_scheme_data = rubric_data.get("marking_scheme", {})
        mark_distribution = marking_scheme_data.get("mark_distribution", {})
        
        # Convert array format to dict if needed
        if isinstance(mark_distribution, list):
            mark_dist_dict = {}
            for item in mark_distribution:
                if isinstance(item, dict) and "component" in item and "marks" in item:
                    mark_dist_dict[item["component"]] = float(item["marks"])
            validated_data["marking_scheme"]["mark_distribution"] = mark_dist_dict
        elif isinstance(mark_distribution, dict):
            validated_data["marking_scheme"]["mark_distribution"] = mark_distribution
        else:
            # Default mark distribution
            validated_data["marking_scheme"]["mark_distribution"] = {"total": float(marks)}
        
        # Validate criteria
        criteria_list = rubric_data.get("criteria", [])
        if not criteria_list:
            # Create default criterion if none provided
            criteria_list = [{
                "criterion": "Answer Quality",
                "weight": 100.0,
                "marks": float(marks),
                "performance_levels": []
            }]
        
        for criterion in criteria_list:
            validated_criterion = {
                "criterion": criterion.get("criterion", "Assessment Criterion"),
                "weight": float(criterion.get("weight", 100.0 / len(criteria_list))),
                "marks": float(criterion.get("marks", marks / len(criteria_list))),
                "performance_levels": []
            }
            
            # Validate performance levels
            performance_levels = criterion.get("performance_levels", [])
            required_levels = ["Excellent", "Proficient", "Developing", "Beginning"]
            
            # Create performance levels if missing
            if not performance_levels:
                performance_levels = [
                    {
                        "level": "Excellent",
                        "marks_range": "90-100%",
                        "descriptor": "Outstanding performance",
                        "indicators": ["Exceeds expectations", "Complete understanding"]
                    },
                    {
                        "level": "Proficient",
                        "marks_range": "70-89%",
                        "descriptor": "Good performance",
                        "indicators": ["Meets expectations", "Good understanding"]
                    },
                    {
                        "level": "Developing",
                        "marks_range": "50-69%",
                        "descriptor": "Satisfactory performance",
                        "indicators": ["Partially meets expectations", "Basic understanding"]
                    },
                    {
                        "level": "Beginning",
                        "marks_range": "0-49%",
                        "descriptor": "Needs improvement",
                        "indicators": ["Below expectations", "Limited understanding"]
                    }
                ]
            
            # Ensure all required levels exist
            existing_levels = {level.get("level") for level in performance_levels}
            for req_level in required_levels:
                if req_level not in existing_levels:
                    performance_levels.append({
                        "level": req_level,
                        "marks_range": "0-100%",
                        "descriptor": f"{req_level} performance level",
                        "indicators": [f"{req_level} level indicators"]
                    })
            
            # Validate each performance level
            for level in performance_levels:
                validated_level = {
                    "level": level.get("level", "Proficient"),
                    "marks_range": level.get("marks_range", "0-100%"),
                    "descriptor": level.get("descriptor", "Performance descriptor"),
                    "indicators": level.get("indicators", ["Performance indicator"])
                }
                
                # Ensure indicators is a list
                if isinstance(validated_level["indicators"], str):
                    validated_level["indicators"] = [validated_level["indicators"]]
                elif not validated_level["indicators"]:
                    validated_level["indicators"] = ["Performance indicator"]
                
                validated_criterion["performance_levels"].append(validated_level)
            
            validated_data["criteria"].append(validated_criterion)
        
        return validated_data
    
    def _create_answer_key_safe(self, answer_key_data: Dict[str, Any], question_data: Dict[str, Any]) -> AnswerKey:
        """Safely create answer key with proper validation"""
        try:
            # Convert array format to dict format for mark_distribution_guide
            if "mark_distribution_guide" in answer_key_data and isinstance(answer_key_data["mark_distribution_guide"], list):
                mark_dist_dict = {}
                for item in answer_key_data["mark_distribution_guide"]:
                    if isinstance(item, dict) and "component" in item and "marks" in item:
                        mark_dist_dict[item["component"]] = float(item["marks"])
                answer_key_data["mark_distribution_guide"] = mark_dist_dict
            
            validated_answer_key = self._validate_answer_key_structure(answer_key_data, question_data)
            return AnswerKey(**validated_answer_key)
        except Exception as e:
            app_logger.warning(f"Failed to create answer key from API response, creating default: {str(e)}")
            return self._create_default_answer_key(question_data)
    
    def _validate_answer_key_structure(self, answer_key_data: Dict[str, Any], question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix answer key structure"""
        marks = question_data.get("marks", 0)
        
        # Validate expected_outline
        expected_outline = answer_key_data.get("expected_outline", [])
        if not expected_outline:
            expected_outline = [{
                "point": "Key answer point (requires manual review)",
                "marks": float(marks),
                "sub_points": [],
                "keywords": ["manual", "review"]
            }]
        
        validated_outline = []
        for point in expected_outline:
            validated_point = {
                "point": point.get("point", "Answer point"),
                "marks": float(point.get("marks", 0)),
                "sub_points": point.get("sub_points", []),
                "keywords": point.get("keywords", [])
            }
            
            # Ensure sub_points and keywords are lists
            if isinstance(validated_point["sub_points"], str):
                validated_point["sub_points"] = [validated_point["sub_points"]]
            if isinstance(validated_point["keywords"], str):
                validated_point["keywords"] = [validated_point["keywords"]]
            
            validated_outline.append(validated_point)
        
        # Handle mark_distribution_guide
        mark_distribution_guide = answer_key_data.get("mark_distribution_guide", {})
        if isinstance(mark_distribution_guide, list):
            # Convert array to dict
            mark_dist_dict = {}
            for item in mark_distribution_guide:
                if isinstance(item, dict) and "component" in item and "marks" in item:
                    mark_dist_dict[item["component"]] = float(item["marks"])
            mark_distribution_guide = mark_dist_dict
        elif not isinstance(mark_distribution_guide, dict):
            mark_distribution_guide = {"total": float(marks)}
        
        return {
            "expected_outline": validated_outline,
            "key_concepts": answer_key_data.get("key_concepts", ["Key concept requires manual review"]),
            "alternative_answers": answer_key_data.get("alternative_answers", []),
            "mark_distribution_guide": mark_distribution_guide
        }
    
    def _create_default_rubric(self, question_data: Dict[str, Any]) -> Rubric:
        """Create a default rubric when API response fails"""
        marks = question_data.get("marks", 0)
        
        # Create default criterion with proper performance levels
        criterion = RubricCriterion(
            criterion="Answer Quality",
            weight=100.0,
            marks=float(marks),
            performance_levels=[
                PerformanceLevel(
                    level="Excellent",
                    marks_range="90-100%",
                    descriptor="Complete and accurate answer with excellent understanding",
                    indicators=["All key points covered", "Clear explanation", "Excellent use of terminology"]
                ),
                PerformanceLevel(
                    level="Proficient",
                    marks_range="70-89%",
                    descriptor="Good answer with minor gaps",
                    indicators=["Most key points covered", "Generally clear explanation", "Good use of terminology"]
                ),
                PerformanceLevel(
                    level="Developing",
                    marks_range="50-69%",
                    descriptor="Partial answer with some understanding",
                    indicators=["Some key points covered", "Basic explanation", "Limited use of terminology"]
                ),
                PerformanceLevel(
                    level="Beginning",
                    marks_range="0-49%",
                    descriptor="Incomplete or incorrect answer",
                    indicators=["Few or no key points", "Unclear explanation", "Poor use of terminology"]
                )
            ]
        )
        
        return Rubric(
            type="basic_rubric" if marks <= 5 else "detailed_analytical",
            standard="bloom_taxonomy",
            criteria=[criterion],
            marking_scheme=MarkingScheme(
                total_marks=marks,
                mark_distribution={"answer_quality": float(marks)}
            ),
            partial_marking_guidelines=PartialMarkingGuidelines(
                minimum_pass_criteria="Must attempt to answer the question",
                partial_credit_rules=["Partial credit for incomplete but correct information", "Credit for showing working/reasoning"]
            )
        )
    
    def _create_default_answer_key(self, question_data: Dict[str, Any]) -> AnswerKey:
        """Create a default answer key when API response fails"""
        marks = question_data.get("marks", 0)
        
        return AnswerKey(
            expected_outline=[
                AnswerPoint(
                    point="Key answer point (manual evaluation required)",
                    marks=float(marks),
                    sub_points=["Requires manual review by teacher"],
                    keywords=["manual", "evaluation", "required"]
                )
            ],
            key_concepts=["Manual evaluation required due to processing error"],
            alternative_answers=[],
            mark_distribution_guide={"manual_evaluation": float(marks)}
        )
    
    def _generate_evaluation_guidelines_fast(self, classification: QuestionClassification, rubric_data: Dict[str, Any], answer_key_data: Dict[str, Any]) -> EvaluationGuidelines:
        """Fast local generation of evaluation guidelines"""
        
        # Generate context-aware guidelines based on classification
        subject = classification.subject.lower()
        bloom_level = classification.bloom_level.lower()
        question_type = classification.question_type.lower()
        
        # Context-aware common mistakes
        common_mistakes = self._generate_common_mistakes(subject, question_type, bloom_level)
        
        # Context-aware evaluation tips
        evaluation_tips = self._generate_evaluation_tips(subject, question_type, bloom_level)
        
        # Time allocation based on marks and complexity
        time_allocation = TimeAllocation(
            reading_question=f"{max(30, classification.marks * 10)} seconds",
            evaluation_time=f"{max(1, classification.marks // 2)} minutes",
            feedback_writing=f"{max(30, classification.marks * 15)} seconds"
        )
        
        # Context-aware red flags
        red_flags = self._generate_red_flags(subject, question_type, bloom_level)
        
        return EvaluationGuidelines(
            common_mistakes=common_mistakes,
            evaluation_tips=evaluation_tips,
            time_allocation=time_allocation,
            red_flags=red_flags
        )
    
    def _generate_common_mistakes(self, subject: str, question_type: str, bloom_level: str) -> List[str]:
        """Generate context-aware common mistakes"""
        base_mistakes = [
            "Incomplete answer missing key components",
            "Misunderstanding of the question requirements",
            "Poor organization of response",
            "Lack of supporting evidence or examples"
        ]
        
        # Add subject-specific mistakes
        if "math" in subject or "science" in subject:
            base_mistakes.extend([
                "Calculation errors or wrong formulas",
                "Missing units in final answers",
                "Not showing working steps"
            ])
        elif "english" in subject or "literature" in subject:
            base_mistakes.extend([
                "Poor grammar and spelling",
                "Lack of textual evidence",
                "Weak thesis statement"
            ])
        elif "history" in subject or "social" in subject:
            base_mistakes.extend([
                "Incorrect dates or facts",
                "Lack of historical context",
                "Bias without acknowledgment"
            ])
        
        # Add bloom-level specific mistakes
        if bloom_level in ["analysis", "synthesis", "evaluation"]:
            base_mistakes.extend([
                "Superficial analysis without depth",
                "Failure to make connections",
                "Lack of critical thinking"
            ])
        
        return base_mistakes[:6]  # Limit to 6 most relevant
    
    def _generate_evaluation_tips(self, subject: str, question_type: str, bloom_level: str) -> List[str]:
        """Generate context-aware evaluation tips"""
        base_tips = [
            f"Focus on {bloom_level} level thinking skills",
            "Check for understanding of key concepts",
            "Look for proper reasoning and explanation",
            "Verify use of appropriate terminology"
        ]
        
        # Add subject-specific tips
        if "math" in subject or "science" in subject:
            base_tips.extend([
                "Verify calculations and formulas used",
                "Check for correct units and significant figures",
                "Look for logical problem-solving approach"
            ])
        elif "english" in subject or "literature" in subject:
            base_tips.extend([
                "Assess clarity and coherence of writing",
                "Check for proper use of literary devices",
                "Evaluate strength of arguments"
            ])
        
        return base_tips[:6]  # Limit to 6 most relevant
    
    def _generate_red_flags(self, subject: str, question_type: str, bloom_level: str) -> List[str]:
        """Generate context-aware red flags"""
        base_flags = [
            "Completely off-topic response",
            "No attempt at answering the question",
            "Copied content without understanding",
            "Major factual errors or misconceptions"
        ]
        
        # Add subject-specific red flags
        if "math" in subject or "science" in subject:
            base_flags.extend([
                "Fundamental calculation errors",
                "Wrong scientific principles applied"
            ])
        elif "english" in subject or "literature" in subject:
            base_flags.extend([
                "Plagiarism or copied text",
                "Completely irrelevant literary analysis"
            ])
        
        return base_flags[:5]  # Limit to 5 most critical
    
    def _create_section_metadata(self, section_data: Dict[str, Any]) -> SectionMetadata:
        return SectionMetadata(
            section_name=section_data.get('name', 'Unknown Section'),
            section_instruction=section_data.get('instruction'),
            section_marks=section_data.get('total_marks'),
            section_time_allocation=section_data.get('time_allocation')
        )
    
    def _create_question_metadata(self, question_data: Dict[str, Any]) -> QuestionMetadata:
        return QuestionMetadata(
            question_number=question_data.get('number', 'Unknown'),
            question_id=f"q_{question_data.get('number', 'unknown')}",
            is_optional=question_data.get('optional', False),
            optional_group=question_data.get('optional_with'),
            subquestion_label=question_data.get('subquestion_label')
        )
        
    def _create_error_response(self, question_data: Dict[str, Any], section_data: Dict[str, Any], error_message: str, processing_time: float) -> RubricResponse:
        """Create proper error response with valid performance levels"""
        
        classification = QuestionClassification(
            question_type=question_data.get('type', 'unknown'),
            subject="Unknown",
            topic="Unknown",
            difficulty_level="basic",
            bloom_level="knowledge",
            cognitive_skills=["recall"],
            marks=question_data.get('marks', 0),
            estimated_time="Unknown"
        )
        
        # Create rubric with proper performance levels
        rubric = Rubric(
            type="simple_checklist",
            standard="basic",
            criteria=[
                RubricCriterion(
                    criterion="Manual Evaluation Required",
                    weight=100.0,
                    marks=float(question_data.get('marks', 0)),
                    performance_levels=[
                        PerformanceLevel(
                            level="Excellent",
                            marks_range="90-100%",
                            descriptor="Processing failed - requires manual evaluation",
                            indicators=["Review question manually", "Apply appropriate rubric"]
                        ),
                        PerformanceLevel(
                            level="Proficient",
                            marks_range="70-89%",
                            descriptor="Processing failed - requires manual evaluation",
                            indicators=["Review question manually", "Apply appropriate rubric"]
                        ),
                        PerformanceLevel(
                            level="Developing",
                            marks_range="50-69%",
                            descriptor="Processing failed - requires manual evaluation",
                            indicators=["Review question manually", "Apply appropriate rubric"]
                        ),
                        PerformanceLevel(
                            level="Beginning",
                            marks_range="0-49%",
                            descriptor="Processing failed - requires manual evaluation",
                            indicators=["Review question manually", "Apply appropriate rubric"]
                        )
                    ]
                )
            ],
            marking_scheme=MarkingScheme(
                total_marks=question_data.get('marks', 0),
                mark_distribution={"manual": float(question_data.get('marks', 0))}
            ),
            partial_marking_guidelines=PartialMarkingGuidelines(
                minimum_pass_criteria="Manual evaluation required",
                partial_credit_rules=["Evaluate manually due to processing error"]
            )
        )
        
        answer_key = AnswerKey(
            expected_outline=[
                AnswerPoint(
                    point="Manual evaluation required",
                    marks=float(question_data.get('marks', 0)),
                    sub_points=["Processing failed", "Requires teacher review"],
                    keywords=["manual", "evaluation"]
                )
            ],
            key_concepts=["Manual evaluation required"],
            alternative_answers=[],
            mark_distribution_guide={"manual": float(question_data.get('marks', 0))}
        )
        
        evaluation_guidelines = EvaluationGuidelines(
            common_mistakes=["Processing error occurred"],
            evaluation_tips=["Manual evaluation required", "Review question carefully"],
            time_allocation=TimeAllocation(
                reading_question="1 minute",
                evaluation_time="Manual",
                feedback_writing="1 minute"
            ),
            red_flags=["Automated processing failed"]
        )
        
        return RubricResponse(
            section_metadata=self._create_section_metadata(section_data),
            question_metadata=self._create_question_metadata(question_data),
            classification=classification,
            rubric=rubric,
            answer_key=answer_key,
            evaluation_guidelines=evaluation_guidelines,
            quality_metrics=QualityMetrics(
                rubric_completeness=0,
                standard_compliance="error",
                validation_status="failed",
                processing_time=processing_time,
                confidence_score=0.0
            ),
            processing_status="failed"
        )


class RubricWorkerPool:
    """Optimized worker pool with controlled concurrency"""
    
    def __init__(self, worker_count: int = 2):
        self.worker_count = worker_count
        self.workers = [RubricWorker(f"worker_{i}") for i in range(worker_count)]
        self.semaphore = asyncio.Semaphore(worker_count)
        self.request_delay = 2.0  # Increased delay to avoid rate limits
    
    async def process_questions(self, questions_data: List[Dict[str, Any]], user_preferences: UserPreferences, progress_callback=None) -> List[RubricResponse]:
        """Process questions with controlled rate limiting and proper error handling"""
        
        app_logger.info(f"Starting optimized processing of {len(questions_data)} questions with {self.worker_count} workers")
        
        results = []
        
        # Process questions sequentially to avoid rate limits and safety issues
        for i, (question_data, section_data) in enumerate(questions_data):
            try:
                app_logger.info(f"Processing question {i+1}/{len(questions_data)}: {question_data.get('number', 'unknown')}")
                
                # Progress callback
                if progress_callback:
                    await progress_callback(i, question_data, section_data)
                
                # Process single question
                worker = self.workers[i % self.worker_count]
                result = await worker.process_question(question_data, section_data, user_preferences)
                results.append(result)
                
                # Log result
                if result.processing_status == "completed":
                    app_logger.info(f"Successfully processed question {question_data.get('number', 'unknown')}")
                else:
                    app_logger.warning(f"Failed to process question {question_data.get('number', 'unknown')}")
                
                # Delay between requests to respect rate limits
                if i < len(questions_data) - 1:
                    app_logger.info(f"Waiting {self.request_delay} seconds before next question...")
                    await asyncio.sleep(self.request_delay)
                    
            except Exception as e:
                app_logger.error(f"Question {i} processing failed: {str(e)}")
                # Create error response
                error_response = self.workers[0]._create_error_response(
                    question_data, section_data, str(e), 0.0
                )
                results.append(error_response)
        
        successful_count = sum(1 for r in results if r.processing_status == "completed")
        failed_count = len(results) - successful_count
        
        app_logger.info(f"Completed processing: {successful_count} successful, {failed_count} failed")
        return results
    
    async def _process_question_with_delay(self, question_data: Dict[str, Any], section_data: Dict[str, Any], user_preferences: UserPreferences, question_index: int, progress_callback=None, batch_index: int = 0) -> RubricResponse:
        """Process question with delay and proper error handling"""
        
        # Add delay based on batch position to stagger requests
        if batch_index > 0:
            await asyncio.sleep(batch_index * 1.0)
        
        async with self.semaphore:
            try:
                worker = self.workers[question_index % self.worker_count]
                
                if progress_callback:
                    await progress_callback(question_index, question_data, section_data)
                
                return await worker.process_question(question_data, section_data, user_preferences)
                
            except Exception as e:
                app_logger.error(f"Worker processing failed for question {question_data.get('number')}: {str(e)}")
                # Return error response instead of raising exception
                return self.workers[0]._create_error_response(
                    question_data, section_data, str(e), 0.0
                )

# Global worker pool instance with reduced concurrency for stability
rubric_worker_pool = RubricWorkerPool(worker_count=1)  # Reduced to 1 for better stability


