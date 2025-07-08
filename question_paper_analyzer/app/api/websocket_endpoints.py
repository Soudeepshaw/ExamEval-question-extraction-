from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_handler import websocket_handler
from app.utils.logger import app_logger
import json
import asyncio

router = APIRouter()

@router.websocket("/ws/rubric-generation")
async def websocket_rubric_generation(websocket: WebSocket):
    """
    Optimized WebSocket endpoint for fast rubric generation.
    
    Expected message format:
    {
        "enhanced_api_response": { ... },
        "user_preferences": {
            "subject_hint": "Mathematics",
            "grade_level": "10",
            "quality_mode": "fast",
            "rubric_standard": "bloom_taxonomy"
        }
    }
    
    Features:
    - Single API call per question
    - Structured output for consistency
    - Better connection management
    - Optimized rate limiting
    """
    
    connection_id = id(websocket)
    app_logger.info(f"New WebSocket connection: {connection_id}")
    
    try:
        # Accept connection
        await websocket_handler.connect(websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "data": {
                "message": "Connected to optimized rubric generation service",
                "features": [
                    "Single API call per question",
                    "Structured output",
                    "Real-time progress updates",
                    "Optimized rate limiting"
                ],
                "connection_id": connection_id
            }
        }))
        
        while True:
            try:
                # Receive message with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)  # 5 minute timeout
                
                try:
                    request_data = json.loads(data)
                    app_logger.info(f"Processing rubric generation request from connection {connection_id}")
                    
                    # Validate request structure
                    if not request_data.get("enhanced_api_response"):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "data": {
                                "message": "Missing enhanced_api_response in request",
                                "timestamp": "now"
                            }
                        }))
                        continue
                    
                    if not request_data.get("user_preferences"):
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "data": {
                                "message": "Missing user_preferences in request",
                                "timestamp": "now"
                            }
                        }))
                        continue
                    
                    # Process the request
                    await websocket_handler.handle_rubric_generation(websocket, request_data)
                    
                except json.JSONDecodeError:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "message": "Invalid JSON format",
                            "timestamp": "now"
                        }
                    }))
                except Exception as e:
                    app_logger.error(f"Error processing request from connection {connection_id}: {str(e)}")
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "data": {
                            "message": f"Processing error: {str(e)}",
                            "timestamp": "now"
                        }
                    }))
                    
            except asyncio.TimeoutError:
                app_logger.info(f"WebSocket connection {connection_id} timed out")
                await websocket.send_text(json.dumps({
                    "type": "timeout",
                    "data": {
                        "message": "Connection timeout - please reconnect if needed",
                        "timestamp": "now"
                    }
                }))
                break
                
    except WebSocketDisconnect:
        app_logger.info(f"WebSocket connection {connection_id} disconnected normally")
    except Exception as e:
        app_logger.error(f"WebSocket connection {connection_id} error: {str(e)}")
    finally:
        websocket_handler.disconnect(websocket)
        app_logger.info(f"Cleaned up WebSocket connection {connection_id}")
