"""Factory for roadmap generation components"""
from typing import Any
from fastapi import APIRouter

from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...application.use_cases.roadmap_generation_use_case import RoadmapGenerationUseCase
from ...presentation.controllers.roadmap_generation_controller import create_roadmap_generation_router


class RoadmapGenerationFactory:
    """Factory to create roadmap generation components with proper dependencies"""

    def __init__(self, database: Any):
        self.database = database
        self.ai_service = GeminiAIServiceAdapter()

    def create_router(self) -> APIRouter:
        """Create configured roadmap generation router with all dependencies"""
        generation_use_case = RoadmapGenerationUseCase(
            ai_service=self.ai_service
        )
        return create_roadmap_generation_router(generation_use_case)
