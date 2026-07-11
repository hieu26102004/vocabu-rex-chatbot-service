"""Data Transfer Objects for image description scoring API"""
from typing import Optional
from pydantic import BaseModel, Field


class ImageDescriptionScoreRequest(BaseModel):
    """Request to score image description"""
    user_content: str = Field(..., max_length=2000, description="User's description of the image")
    expected_results: str = Field(..., max_length=2000, description="Expected description or answer")
    language: str = Field("en", pattern="^(en|vi)$", description="Language code (en/vi)")


class ImageDescriptionScoreResponse(BaseModel):
    """Response for image description scoring"""
    is_correct: bool = Field(..., description="Whether the description is considered correct")
    score_percentage: float = Field(..., ge=0.0, le=100.0, description="Score as percentage (0-100)")
    feedback: str = Field(..., description="Brief feedback comment")
    similarity_level: str = Field(..., description="Level of similarity (high/medium/low)")