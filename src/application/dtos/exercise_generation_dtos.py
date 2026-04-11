"""DTOs for exercise generation"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any


class ExerciseGenerationRequest(BaseModel):
    """Request to generate exercises using AI"""
    topic: str = Field(default="General English", description="Topic for exercises")
    difficulty: str = Field(default="intermediate", description="Difficulty level")
    exercise_count: int = Field(default=8, ge=1, le=20, description="Number of exercises to generate")


class GeneratedExercise(BaseModel):
    """A single generated exercise"""
    exerciseType: str
    prompt: str
    meta: dict[str, Any]


class ExerciseGenerationResponse(BaseModel):
    """Response with generated exercises"""
    exercises: List[GeneratedExercise]
    topic: str
    difficulty: str
