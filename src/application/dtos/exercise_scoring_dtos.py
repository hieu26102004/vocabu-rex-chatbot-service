"""Data Transfer Objects for exercise scoring API"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    """Specific error in the user's text"""
    original: str = Field(..., description="The original incorrect text")
    corrected: str = Field(..., description="The corrected text")
    explanation: str = Field(..., description="Explanation of why it was wrong")


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
    grammar_feedback: Optional[str] = Field(None, description="Feedback specific to grammar")
    vocabulary_feedback: Optional[str] = Field(None, description="Feedback specific to vocabulary usage")
    content_feedback: Optional[str] = Field(None, description="Feedback specific to content and prompt adherence")
    detailed_errors: List[ErrorDetail] = Field(default_factory=list, description="List of specific errors found")


class TranslateScoreRequest(BaseModel):
    """Request to score a translate exercise"""
    user_answer: str = Field(..., min_length=1, max_length=500, description="User's translation answer")
    source_text: str = Field(..., min_length=1, max_length=500, description="Original text to translate")
    correct_answer: str = Field(..., min_length=1, max_length=500, description="Correct translation")
    language: str = Field("en", pattern="^(en|vi)$", description="Target language code (en/vi)")


class TranslateScoreResponse(BaseModel):
    """Response for translate scoring"""
    is_correct: bool = Field(..., description="Whether the translation is correct")
    feedback: str = Field(..., description="Short feedback comment")