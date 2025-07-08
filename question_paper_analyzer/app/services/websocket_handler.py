import asyncio
import json
from typing import Dict, Any, List, Optional
from fastapi import WebSocket, WebSocketDisconnect
from app.services.question_parser import question_parser
from app.services.rubric_workers import rubric_worker_pool
from app.models.rubric_schemas import (
    RubricGenerationRequest, UserPreferences, WebSocketMessage, 
    ProgressUpdate, FinalSummary, RubricResponse
)
from app.utils.logger import app_logger
import time
from datetime import datetime

class RubricWebSocketHandler:
    """Optimized WebSocket handler"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        app_logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        app_logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def handle_rubric_generation(self, websocket: WebSocket, request_data: Dict[str, Any]):
        """Optimized rubric generation with better error handling"""
        
        start_time = time.time()
        
        try:
            request = RubricGenerationRequest(**request_data)
            app_logger.info("Starting optimized rubric generation")
            
            # Check connection before starting
            if not self._is_websocket_connected(websocket):
                app_logger.warning("WebSocket disconnected before processing started")
                return
            
            await self._send_message_safe(websocket, "progress", {
                "status": "started",
                "message": "Starting optimized rubric generation (single API call per question)",
                "timestamp": datetime.now().isoformat()
            })
            
            # Parse questions
            questions_data = question_parser.parse_enhanced_response(request.enhanced_api_response)
            validated_questions = question_parser.validate_questions(questions_data)
            
            if not validated_questions:
                await self._send_message_safe(websocket, "error", {
                    "message": "No valid questions found",
                    "timestamp": datetime.now().isoformat()
                })
                return
            
            await self._send_message_safe(websocket, "progress", {
                "status": "parsing_complete",
                "total_questions": len(validated_questions),
                "message": f"Processing {len(validated_questions)} questions with optimized single-call approach",
                "timestamp": datetime.now().isoformat()
            })
            
            # Process with progress tracking
            results = []
            successful_count = 0
            failed_count = 0
            
            async def progress_callback(question_index: int, question_data: Dict[str, Any], section_data: Dict[str, Any]):
                if not self._is_websocket_connected(websocket):
                    return
                
                progress = ProgressUpdate(
                    current_question=question_index + 1,
                    total_questions=len(validated_questions),
                    section=section_data.get('name', 'Unknown'),
                    status=f"Processing question {question_data.get('number', 'unknown')} (single API call)",
                    estimated_remaining_time=self._estimate_remaining_time(
                        question_index, len(validated_questions), start_time
                    )
                )
                
                await self._send_message_safe(websocket, "progress", progress.dict())
            
            # Process all questions with optimized approach
            processed_results = await rubric_worker_pool.process_questions(
                validated_questions, 
                request.user_preferences, 
                progress_callback
            )
            
            # Stream results
            for i, result in enumerate(processed_results):
                if not self._is_websocket_connected(websocket):
                    app_logger.warning("WebSocket disconnected during result streaming")
                    break
                
                if result.processing_status == "completed":
                    successful_count += 1
                else:
                    failed_count += 1
                
                await self._send_message_safe(websocket, "question_complete", {
                    "question_index": i + 1,
                    "total_questions": len(validated_questions),
                    "result": result.dict(),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.05)
            
            # Send final summary
            if self._is_websocket_connected(websocket):
                total_time = time.time() - start_time
                summary = FinalSummary(
                    total_questions_processed=len(validated_questions),
                    successful_generations=successful_count,
                    failed_generations=failed_count,
                    total_processing_time=total_time,
                    average_time_per_question=total_time / len(validated_questions) if validated_questions else 0,
                    quality_distribution=self._calculate_quality_distribution(processed_results)
                )
                
                await self._send_message_safe(websocket, "final_summary", {
                    "summary": summary.dict(),
                    "message": f"Completed with optimized single-call approach: {successful_count} successful, {failed_count} failed",
                    "timestamp": datetime.now().isoformat()
                })
            
            app_logger.info(f"Optimized rubric generation completed: {successful_count} successful, {failed_count} failed, {total_time:.2f}s total")
            
        except Exception as e:
            app_logger.error(f"Error in rubric generation: {str(e)}")
            if self._is_websocket_connected(websocket):
                await self._send_message_safe(websocket, "error", {
                    "message": f"Processing failed: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
    
    def _is_websocket_connected(self, websocket: WebSocket) -> bool:
        """Check if WebSocket is still connected"""
        try:
            return websocket.client_state.name == "CONNECTED"
        except:
            return False
    
    async def _send_message_safe(self, websocket: WebSocket, message_type: str, data: Dict[str, Any]):
        """Safely send message with connection check"""
        try:
            if not self._is_websocket_connected(websocket):
                return
            
            message = WebSocketMessage(
                type=message_type,
                data=data
            )
            await websocket.send_text(json.dumps(message.dict(), default=str))
        except Exception as e:
            app_logger.warning(f"Failed to send WebSocket message: {str(e)}")
    
    def _estimate_remaining_time(self, current_index: int, total_questions: int, start_time: float) -> Optional[int]:
        if current_index == 0:
            return None
        
        elapsed_time = time.time() - start_time
        avg_time_per_question = elapsed_time / (current_index + 1)
        remaining_questions = total_questions - (current_index + 1)
        
        return int(remaining_questions * avg_time_per_question)
    
    def _calculate_quality_distribution(self, results: List[RubricResponse]) -> Dict[str, int]:
        distribution = {
            "excellent": 0,
            "good": 0,
            "fair": 0,
            "poor": 0
        }
        
        for result in results:
            confidence = result.quality_metrics.confidence_score
            if confidence >= 0.9:
                distribution["excellent"] += 1
            elif confidence >= 0.7:
                distribution["good"] += 1
            elif confidence >= 0.5:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1
        
        return distribution

# Global handler instance
websocket_handler = RubricWebSocketHandler()
