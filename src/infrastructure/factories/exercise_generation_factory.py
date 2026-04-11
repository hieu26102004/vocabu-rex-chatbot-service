"""Factory for exercise generation components"""
from typing import Any
from fastapi import APIRouter

from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...application.use_cases.exercise_generation_use_case import ExerciseGenerationUseCase
from ...presentation.controllers.exercise_generation_controller import create_exercise_generation_router


class ExerciseGenerationFactory:
    """Factory to create exercise generation components with proper dependencies"""

    def __init__(self, database: Any):
        self.database = database
        self.ai_service = GeminiAIServiceAdapter()

    def create_router(self) -> APIRouter:
        """Create configured exercise generation router with all dependencies"""
        # Create use case with dependencies
        generation_use_case = ExerciseGenerationUseCase(
            ai_service=self.ai_service
        )

        # Create and return router
        return create_exercise_generation_router(generation_use_case)
