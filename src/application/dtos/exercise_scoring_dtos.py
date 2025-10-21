"""Data Transfer Objects for exercise scoring API"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WritingPromptScoreRequest(BaseModel):
    """Request to score a writing prompt exercise"""
    user_answer: str = Field(..., min_length=1, max_length=5000, description="User's writing answer")
    exercise_meta: Dict[str, Any] = Field(..., description="Exercise metadata (WritingPromptMeta)")
    language: str = Field("en", pattern="^(en|vi)$", description="Language code (en/vi)")


class WritingPromptScoreResponse(BaseModel):
    """Response for writing prompt scoring"""
    is_correct: bool = Field(..., description="Whether the answer is considered correct (score >= 60)")
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Score as percentage (0-100)")
    feedback: str = Field(..., description="Brief feedback comment")
    performance_level: str = Field(..., description="excellent/good/satisfactory/needs_improvement/poor")