"""Writing assessment entities for scoring and feedback"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class ScoreCriterion(Enum):
    """Available scoring criteria"""
    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar" 
    STRUCTURE = "structure"


class AssessmentStatus(Enum):
    """Assessment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScoringCriteria:
    """Scoring criteria configuration"""
    vocabulary_weight: float = 0.33
    grammar_weight: float = 0.33
    structure_weight: float = 0.34
    max_score: float = 10.0
    min_score: float = 0.0
    
    def __post_init__(self):
        # Ensure weights sum to 1.0
        total = self.vocabulary_weight + self.grammar_weight + self.structure_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


@dataclass
class ErrorCorrection:
    """Grammar/vocabulary error correction"""
    error_text: str
    corrected_text: str
    explanation: str
    error_type: str
    rule_reference: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class VocabularyEnhancement:
    """Advanced vocabulary suggestion"""
    original: str
    suggestion: str
    context_explanation: str
    example_sentence: str
    formality_level: str = "academic"  # academic, professional, casual
    difficulty_level: str = "intermediate"  # beginner, intermediate, advanced


@dataclass
class CriterionScore:
    """Score for individual criterion"""
    criterion: ScoreCriterion
    score: float
    max_score: float
    feedback: str
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)


@dataclass
class DetailedFeedback:
    """Comprehensive feedback for writing assessment"""
    
    # Prompt adherence analysis
    prompt_adherence_score: float
    prompt_adherence_feedback: str
    missed_requirements: List[str] = field(default_factory=list)
    
    # Error corrections
    grammar_corrections: List[ErrorCorrection] = field(default_factory=list)
    
    # Vocabulary enhancements
    vocabulary_enhancements: List[VocabularyEnhancement] = field(default_factory=list)
    
    # Structure suggestions
    structure_suggestions: Dict[str, str] = field(default_factory=dict)
    
    # Overall feedback
    overall_strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    
    # Learning recommendations
    recommended_topics: List[str] = field(default_factory=list)
    difficulty_level: str = "intermediate"


@dataclass
class AssessmentResult:
    """Complete assessment result"""
    
    # Scores
    overall_score: float
    ai_model_used: str
    criterion_scores: List[CriterionScore] = field(default_factory=list)
    
    # Detailed feedback
    detailed_feedback: Optional[DetailedFeedback] = None
    
    # Metadata
    assessment_time_seconds: float = 0.0
    
    def get_score_by_criterion(self, criterion: ScoreCriterion) -> Optional[CriterionScore]:
        """Get score for specific criterion"""
        for score in self.criterion_scores:
            if score.criterion == criterion:
                return score
        return None


@dataclass
class WritingSubmission:
    """User's writing submission for assessment"""
    
    user_id: str
    writing_text: str
    writing_prompt: str
    image_url: Optional[str] = None
    image_description: Optional[str] = None
    
    # Assessment configuration
    scoring_criteria: ScoringCriteria = field(default_factory=ScoringCriteria)
    language: str = "en"  # en, vi
    
    # Metadata
    word_count: int = 0
    character_count: int = 0
    
    def __post_init__(self):
        if not self.word_count:
            self.word_count = len(self.writing_text.split())
        if not self.character_count:
            self.character_count = len(self.writing_text)


@dataclass
class WritingAssessment:
    """Main writing assessment entity"""
    
    id: str
    submission: WritingSubmission
    result: Optional[AssessmentResult] = None
    
    # Status tracking
    status: AssessmentStatus = AssessmentStatus.PENDING
    error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Processing metadata
    processing_steps: List[str] = field(default_factory=list)
    ai_interactions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def start_processing(self) -> None:
        """Mark assessment as started"""
        self.status = AssessmentStatus.PROCESSING
        self.started_at = datetime.utcnow()
        self.processing_steps.append(f"Processing started at {self.started_at}")
    
    def complete_processing(self, result: AssessmentResult) -> None:
        """Mark assessment as completed"""
        self.status = AssessmentStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        self.processing_steps.append(f"Processing completed at {self.completed_at}")
    
    def fail_processing(self, error_message: str) -> None:
        """Mark assessment as failed"""
        self.status = AssessmentStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.processing_steps.append(f"Processing failed at {self.completed_at}: {error_message}")
    
    def add_processing_step(self, step: str) -> None:
        """Add a processing step for debugging"""
        timestamp = datetime.utcnow()
        self.processing_steps.append(f"{timestamp}: {step}")
    
    def add_ai_interaction(self, prompt: str, response: str, model: str) -> None:
        """Track AI interactions for debugging"""
        self.ai_interactions.append({
            "timestamp": datetime.utcnow(),
            "model": model,
            "prompt": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "response": response[:1000] + "..." if len(response) > 1000 else response
        })