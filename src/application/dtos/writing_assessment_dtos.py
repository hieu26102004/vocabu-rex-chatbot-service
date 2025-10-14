"""Data Transfer Objects for writing assessment API"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel, Field, validator


# Request DTOs
class WritingAssessmentRequest(BaseModel):
    """Request to assess writing"""
    user_id: str = Field(..., description="User ID submitting the writing")
    writing_text: str = Field(..., min_length=10, max_length=10000, description="The writing text to assess")
    writing_prompt: str = Field(..., min_length=5, max_length=1000, description="The writing prompt or task")
    image_url: Optional[str] = Field(None, description="Optional image URL related to the prompt")
    
    # Scoring configuration
    vocabulary_weight: Optional[float] = Field(0.33, ge=0.0, le=1.0, description="Weight for vocabulary scoring")
    grammar_weight: Optional[float] = Field(0.33, ge=0.0, le=1.0, description="Weight for grammar scoring") 
    structure_weight: Optional[float] = Field(0.34, ge=0.0, le=1.0, description="Weight for structure scoring")
    
    language: str = Field("en", pattern="^(en|vi)$", description="Language code (en/vi)")
    
    @validator('vocabulary_weight', 'grammar_weight', 'structure_weight', always=True)
    def validate_weights(cls, v, values):
        """Ensure weights sum to approximately 1.0"""
        if 'vocabulary_weight' in values and 'grammar_weight' in values:
            vocab = values.get('vocabulary_weight', 0.33)
            grammar = values.get('grammar_weight', 0.33) 
            structure = v
            total = vocab + grammar + structure
            if abs(total - 1.0) > 0.01:
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return v


class FeedbackRequest(BaseModel):
    """Request for detailed feedback on assessment"""
    assessment_id: str = Field(..., description="Assessment ID to get feedback for")
    user_id: str = Field(..., description="User ID requesting feedback")
    include_suggestions: bool = Field(True, description="Include vocabulary suggestions")
    include_corrections: bool = Field(True, description="Include grammar corrections")


# Response DTOs  
class ErrorCorrectionResponse(BaseModel):
    """Grammar/vocabulary error correction response"""
    error_text: str
    corrected_text: str
    explanation: str
    error_type: str
    rule_reference: Optional[str] = None
    line_number: Optional[int] = None


class VocabularyEnhancementResponse(BaseModel):
    """Vocabulary enhancement suggestion response"""
    original: str
    suggestion: str
    context_explanation: str
    example_sentence: str
    formality_level: str = "academic"
    difficulty_level: str = "intermediate"


class CriterionScoreResponse(BaseModel):
    """Individual criterion score response"""
    criterion: str  # vocabulary, grammar, structure
    score: float
    max_score: float
    feedback: str
    strengths: List[str] = []
    weaknesses: List[str] = []


class DetailedFeedbackResponse(BaseModel):
    """Comprehensive feedback response"""
    # Prompt adherence
    prompt_adherence_score: float
    prompt_adherence_feedback: str
    missed_requirements: List[str] = []
    
    # Error corrections
    grammar_corrections: List[ErrorCorrectionResponse] = []
    
    # Vocabulary enhancements  
    vocabulary_enhancements: List[VocabularyEnhancementResponse] = []
    
    # Structure suggestions
    structure_suggestions: Dict[str, str] = {}
    
    # Overall feedback
    overall_strengths: List[str] = []
    areas_for_improvement: List[str] = []
    next_steps: List[str] = []
    
    # Learning recommendations
    recommended_topics: List[str] = []
    difficulty_level: str = "intermediate"


class AssessmentResultResponse(BaseModel):
    """Assessment result response"""
    ai_model_used: str
    overall_score: float
    max_score: float = 10.0
    criterion_scores: List[CriterionScoreResponse] = []
    assessment_time_seconds: float = 0.0


class WritingAssessmentResponse(BaseModel):
    """Complete writing assessment response"""
    assessment_id: str
    status: str  # pending, processing, completed, failed
    
    # Submission info
    word_count: int
    character_count: int
    language: str
    
    # Results (only when completed)
    result: Optional[AssessmentResultResponse] = None
    detailed_feedback: Optional[DetailedFeedbackResponse] = None
    
    # Timestamps
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error info (only when failed)
    error_message: Optional[str] = None


class AssessmentSummaryResponse(BaseModel):
    """Summary of assessment for listing"""
    assessment_id: str
    status: str
    overall_score: Optional[float] = None
    word_count: int
    writing_prompt_preview: str  # First 100 chars
    created_at: datetime
    completed_at: Optional[datetime] = None


class AssessmentHistoryResponse(BaseModel):
    """User's assessment history"""
    user_id: str
    total_assessments: int
    assessments: List[AssessmentSummaryResponse] = []
    
    # Statistics
    average_score: Optional[float] = None
    best_score: Optional[float] = None
    improvement_trend: str = "stable"  # improving, declining, stable
    
    # Pagination
    page: int = 1
    total_pages: int = 1
    per_page: int = 10


# Status DTOs
class AssessmentStatusResponse(BaseModel):
    """Assessment processing status"""
    assessment_id: str
    status: str
    progress_percentage: float = 0.0
    current_step: str = ""
    estimated_completion_seconds: Optional[float] = None
    error_message: Optional[str] = None


# Error DTOs
class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str
    message: str
    invalid_value: Any


class ErrorResponse(BaseModel):
    """Standard error response"""
    error_code: str
    error_message: str
    details: Optional[List[ValidationErrorDetail]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None