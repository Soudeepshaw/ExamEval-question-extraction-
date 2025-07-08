# Rubric Generation Usage Guide

## Overview

The Question Paper Analyzer now includes comprehensive rubric generation capabilities using AI. This feature allows educators to automatically generate detailed rubrics and answer keys for any question paper.

## Features

- **Real-time Processing**: WebSocket-based streaming for live progress updates
- **Parallel Processing**: Multiple workers process questions simultaneously
- **Educational Standards**: Bloom's Taxonomy compliance and grade-level assessment
- **Multiple Rubric Types**: Analytical, holistic, and checklist formats
- **Comprehensive Answer Keys**: Detailed marking schemes and evaluation guidelines
- **Quality Validation**: Automated quality checks and consistency validation

## Quick Start

### 1. Upload and Analyze Question Paper

First, use the enhanced analysis endpoint to extract complete question content:

```bash
curl -X POST "http://localhost:8000/api/v1/upload-enhanced" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@question_paper.pdf"
```

### 2. Generate Rubrics via WebSocket

Connect to the WebSocket endpoint and send the enhanced response:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/rubric-generation');

ws.onopen = function() {
    const request = {
        enhanced_api_response: enhancedResponse, // From step 1
        user_preferences: {
            subject_hint: "Mathematics",
            grade_level: "10",
            quality_mode: "high",
            rubric_standard: "bloom_taxonomy"
        }
    };
    
    ws.send(JSON.stringify(request));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'progress':
            console.log('Progress:', message.data);
            break;
        case 'question_complete':
            console.log('Question completed:', message.data);
            break;
        case 'final_summary':
            console.log('All done:', message.data);
            break;
        case 'error':
            console.error('Error:', message.data);
            break;
    }
};
```

## Message Types

### Progress Updates
```json
{
    "type": "progress",
    "data": {
        "status": "processing",
        "current_question": 3,
        "total_questions": 10,
        "section": "Section A",
        "estimated_remaining_time": 45
    }
}
```

### Question Complete
```json
{
    "type": "question_complete",
    "data": {
        "question_index": 3,
        "result": {
            "classification": {
                "question_type": "essay",
                "subject": "Mathematics",
                "bloom_level": "analysis",
                "marks": 10
            },
            "rubric": {
                "type": "analytical",
                "criteria": [
                    {
                        "criterion": "Problem Understanding",
                        "marks": 3,
                        "performance_levels": [...]
                    }
                ]
            },
            "answer_key": {
                "expected_outline": [...],
                "key_concepts": [...],
                "mark_distribution_guide": {...}
            }
        }
    }
}
```

### Final Summary
```json
{
    "type": "final_summary",
    "data": {
        "summary": {
            "total_questions_processed": 10,
            "successful_generations": 9,
            "failed_generations": 1,
            "total_processing_time": 120.5,
            "quality_distribution": {
                "excellent": 7,
                "good": 2,
                "fair": 0,
                "poor": 1
            }
        }
    }
}
```

## User Preferences

### Subject Hint
Helps the AI understand the subject context:
- "Mathematics"
- "Science" 
- "English"
- "History"
- etc.

### Grade Level
Adjusts complexity and expectations:
- "1-5" (Elementary)
- "6-8" (Middle School)
- "9-12" (High School)
- "undergraduate"
- "graduate"

### Quality Mode
Balances speed vs. quality:
- **"high"**: Maximum quality, slower processing
- **"balanced"**: Good quality, moderate speed
- **"fast"**: Basic quality, faster processing

### Rubric Standard
Educational framework to follow:
- **"bloom_taxonomy"**: Based on Bloom's Taxonomy
- **"custom"**: Flexible custom rubrics

## Rubric Types

### Analytical Rubric
Best for complex questions requiring detailed evaluation:
- Multiple criteria (e.g., Content, Method, Communication)
- 4 performance levels each
- Detailed descriptors and indicators
- Suitable for essays, projects, problem-solving

### Holistic Rubric
Best for overall assessment:
- Single overall score
- General performance descriptors
- Suitable for creative work, presentations

### Simple Checklist
Best for straightforward questions:
- Basic yes/no or present/absent criteria
- Quick evaluation
- Suitable for MCQ, short answers, basic problems

## Performance Levels

All rubrics include 4 standard performance levels:

1. **Excellent (90-100%)**: Exceeds expectations, demonstrates mastery
2. **Proficient (75-89%)**: Meets expectations, shows competence  
3. **Developing (60-74%)**: Approaching expectations, partial understanding
4. **Beginning (Below 60%)**: Below expectations, minimal understanding

## Example Output

### Question Classification
```json
{
    "question_type": "case_study",
    "subject": "Business Studies",
    "topic": "Marketing Strategy",
    "difficulty_level": "intermediate",
    "bloom_level": "analysis",
    "marks": 15,
    "estimated_time": "20-25 minutes"
}
```

### Generated Rubric
```json
{
    "type": "analytical",
    "standard": "bloom_taxonomy",
    "criteria": [
        {
            "criterion": "Problem Analysis",
            "weight": 40,
            "marks": 6,
            "performance_levels": [
                {
                    "level": "Excellent",
                    "marks_range": "5.4-6",
                    "descriptor": "Demonstrates comprehensive analysis of the marketing problem",
                    "indicators": [
                        "Identifies all key issues",
                        "Shows deep understanding of market dynamics",
                        "Connects multiple factors effectively"
                    ]
                }
            ]
        }
    ]
}
```

### Answer Key
```json
{
    "expected_outline": [
        {
            "point": "Identify target market segments",
            "marks": 3,
            "keywords": ["demographics", "psychographics", "segmentation"],
            "detail_level": "Must identify at least 2 distinct segments with characteristics"
        },
        {
            "point": "Analyze competitive landscape",
            "marks": 4,
            "keywords": ["competitors", "market share", "positioning"],
            "detail_level": "Should include direct and indirect competitors"
        },
        {
            "point": "Recommend marketing strategy",
            "marks": 8,
            "keywords": ["4Ps", "strategy", "implementation"],
            "detail_level": "Must provide specific, actionable recommendations"
        }
    ],
    "key_concepts": [
        "Market segmentation",
        "Competitive analysis", 
        "Marketing mix",
        "Strategic positioning"
    ],
    "alternative_answers": [
        "Digital marketing focus acceptable if well-justified",
        "International expansion strategy acceptable for advanced students"
    ],
    "mark_distribution_guide": {
        "analysis": 7,
        "recommendations": 6,
        "presentation": 2
    }
}
```

## Error Handling

The system handles various error scenarios gracefully:

### Connection Errors
```json
{
    "type": "error",
    "data": {
        "message": "WebSocket connection failed",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

### Processing Errors
```json
{
    "type": "error", 
    "data": {
        "message": "Failed to generate rubric for question 5: insufficient content",
        "question_number": "5",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}
```

### Validation Errors
Questions that fail validation will still receive a basic rubric with manual evaluation guidelines.

## Best Practices

### 1. Question Paper Quality
- Ensure clear question text
- Include mark allocations
- Provide sufficient context for complex questions

### 2. User Preferences
- Be specific with subject hints
- Choose appropriate grade level
- Select quality mode based on your needs

### 3. Processing Management
- Monitor WebSocket connection status
- Handle progress updates for user feedback
- Implement retry logic for failed connections

### 4. Result Handling
- Save individual question results as they arrive
- Validate rubric quality scores
- Review failed generations manually

## Integration Examples

### React Component
```jsx
import React, { useState, useEffect } from 'react';

const RubricGenerator = ({ enhancedResponse }) => {
    const [ws, setWs] = useState(null);
    const [progress, setProgress] = useState(null);
    const [results, setResults] = useState([]);
    const [summary, setSummary] = useState(null);

    useEffect(() => {
        const websocket = new WebSocket('ws://localhost:8000/api/v1/ws/rubric-generation');
        
        websocket.onopen = () => {
            const request = {
                enhanced_api_response: enhancedResponse,
                user_preferences: {
                    subject_hint: "Mathematics",
                    grade_level: "10",
                    quality_mode: "high",
                    rubric_standard: "bloom_taxonomy"
                }
            };
            websocket.send(JSON.stringify(request));
        };

        websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            switch(message.type) {
                case 'progress':
                    setProgress(message.data);
                    break;
                case 'question_complete':
                    setResults(prev => [...prev, message.data.result]);
                    break;
                case 'final_summary':
                    setSummary(message.data.summary);
                    break;
                case 'error':
                    console.error('Rubric generation error:', message.data);
                    break;
            }
        };

        setWs(websocket);
        
        return () => websocket.close();
    }, [enhancedResponse]);

    return (
        <div>
            {progress && (
                <div>
                    Progress: {progress.current_question}/{progress.total_questions}
                    <div>Status: {progress.status}</div>
                </div>
            )}
            
            {results.map((result, index) => (
                <div key={index}>
                    <h3>Question {result.question_metadata.question_number}</h3>
                    <div>Type: {result.classification.question_type}</div>
                    <div>Marks: {result.classification.marks}</div>
                    {/* Render rubric details */}
                </div>
            ))}
            
            {summary && (
                <div>
                    <h2>Generation Complete</h2>
                    <div>Successful: {summary.successful_generations}</div>
                    <div>Failed: {summary.failed_generations}</div>
                    <div>Total Time: {summary.total_processing_time}s</div>
                </div>
            )}
        </div>
    );
};
```

### Python Client
```python
import asyncio
import websockets
import json

async def generate_rubrics(enhanced_response):
    uri = "ws://localhost:8000/api/v1/ws/rubric-generation"
    
    async with websockets.connect(uri) as websocket:
        # Send request
        request = {
            "enhanced_api_response": enhanced_response,
            "user_preferences": {
                "subject_hint": "Mathematics",
                "grade_level": "10", 
                "quality_mode": "high",
                "rubric_standard": "bloom_taxonomy"
            }
        }
        
        await websocket.send(json.dumps(request))
        
        results = []
        
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "progress":
                print(f"Progress: {data['data']['status']}")
                
            elif data["type"] == "question_complete":
                results.append(data["data"]["result"])
                print(f"Completed question {len(results)}")
                
            elif data["type"] == "final_summary":
                print("Generation complete!")
                print(f"Summary: {data['data']['summary']}")
                break
                
            elif data["type"] == "error":
                print(f"Error: {data['data']['message']}")
                break
        
        return results

# Usage
# results = asyncio.run(generate_rubrics(enhanced_response))
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Fails**
   - Check if rubric generation is enabled in config
   - Verify WebSocket endpoint URL
   - Ensure proper CORS configuration

2. **No Questions Processed**
   - Verify enhanced response contains question content
   - Check if questions have mark allocations
   - Ensure question text is not empty

3. **Low Quality Scores**
   - Try higher quality mode
   - Provide more specific subject hints
   - Check if question content is clear and complete

4. **Slow Processing**
   - Reduce quality mode to "balanced" or "fast"
   - Check worker count configuration
   - Monitor system resources

### Configuration Issues

1. **GEMINI_API_KEY not set**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Rubric generation disabled**
   ```bash
   export ENABLE_RUBRIC_GENERATION="true"
   ```

3. **Insufficient workers**
   ```bash
   export RUBRIC_WORKER_COUNT="8"
   ```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/upload` | POST | Basic structure analysis |
| `/upload-enhanced` | POST | Complete content extraction |
| `/ws/rubric-generation` | WebSocket | Real-time rubric generation |
| `/question-types` | GET | Supported question types |
| `/capabilities` | GET | Service capabilities |
| `/rubric-info` | GET | Rubric generation details |
| `/health` | GET | Health check |
| `/stats` | GET | Usage statistics |

## Conclusion

The rubric generation feature provides a comprehensive solution for automated assessment creation. By combining AI-powered content analysis with educational standards, it helps educators create consistent, high-quality rubrics efficiently.

For additional support or feature requests, please refer to the API documentation at `/docs`.
```

## 14. Create Docker Configuration

```dockerfile:question_paper_analyzer/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml:question_paper_analyzer/docker-compose.yml
version: '3.8'

services:
  question-paper-analyzer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
      - ENABLE_ENHANCED_EXTRACTION=true
      - ENABLE_RUBRIC_GENERATION=true
      - RUBRIC_WORKER_COUNT=4
      - RUBRIC_QUALITY_MODE=balanced
      - MAX_FILE_SIZE_MB=20
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## 15. Environment Configuration

```env:question_paper_analyzer/.env.example
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Application Configuration
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=20

# Feature Toggles
ENABLE_ENHANCED_EXTRACTION=true
ENABLE_RUBRIC_GENERATION=true

# Rubric Generation Settings
RUBRIC_WORKER_COUNT=4
RUBRIC_QUALITY_MODE=balanced
RUBRIC_MAX_CRITERIA=6
RUBRIC_TIMEOUT_SECONDS=300

# WebSocket Configuration
WEBSOCKET_HEARTBEAT_INTERVAL=30
WEBSOCKET_MAX_CONNECTIONS=10

# Performance Settings
MAX_RETRIES=3
RETRY_DELAY=2
MAX_CONTENT_LENGTH=50000

