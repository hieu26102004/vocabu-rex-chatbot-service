"""Factory for skill generation components"""
from typing import Any
from fastapi import APIRouter

from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...application.use_cases.skill_generation_use_case import SkillGenerationUseCase
from ...presentation.controllers.skill_generation_controller import create_skill_generation_router


class SkillGenerationFactory:
    """Factory to create skill generation components with proper dependencies"""

    def __init__(self, database: Any):
        self.database = database
        self.ai_service = GeminiAIServiceAdapter()

    def create_router(self) -> APIRouter:
        """Create configured skill generation router with all dependencies"""
        generation_use_case = SkillGenerationUseCase(
            ai_service=self.ai_service
        )
        return create_skill_generation_router(generation_use_case)
