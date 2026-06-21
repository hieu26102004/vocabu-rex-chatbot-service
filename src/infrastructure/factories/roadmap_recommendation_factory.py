"""Factory for roadmap recommendation components"""
from typing import Any
from fastapi import APIRouter

from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...application.use_cases.roadmap_recommendation_use_case import RoadmapRecommendationUseCase
from ...presentation.controllers.roadmap_recommendation_controller import create_roadmap_recommendation_router


class RoadmapRecommendationFactory:
    """Factory to create roadmap recommendation components with proper dependencies"""

    def __init__(self, database: Any):
        self.database = database
        self.ai_service = GeminiAIServiceAdapter()

    def create_router(self) -> APIRouter:
        """Create configured roadmap recommendation router with all dependencies"""
        # Create use case with dependencies
        recommendation_use_case = RoadmapRecommendationUseCase(
            ai_service=self.ai_service
        )

        # Create and return router
        return create_roadmap_recommendation_router(recommendation_use_case)
