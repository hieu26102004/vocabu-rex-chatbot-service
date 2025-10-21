"""Factory for exercise scoring components"""
from typing import Any
from fastapi import APIRouter

from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...application.use_cases.exercise_scoring_use_case import ExerciseScoringUseCase
from ...presentation.controllers.exercise_scoring_controller import create_exercise_scoring_router


class ExerciseScoringFactory:
    """Factory to create exercise scoring components with proper dependencies"""
    
    def __init__(self, database: Any):
        self.database = database
        self.ai_service = GeminiAIServiceAdapter()
        
    def create_router(self) -> APIRouter:
        """Create configured exercise scoring router with all dependencies"""
        # Create use case with dependencies
        scoring_use_case = ExerciseScoringUseCase(
            ai_service=self.ai_service
        )
        
        # Create and return router
        return create_exercise_scoring_router(scoring_use_case)