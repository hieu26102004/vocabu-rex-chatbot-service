"""Roadmap recommendation controller"""
from fastapi import APIRouter, HTTPException, status

from ...application.dtos.roadmap_recommendation_dtos import (
    RecommendRoadmapRequest,
    RecommendRoadmapResponse,
)
from ...application.use_cases.roadmap_recommendation_use_case import RoadmapRecommendationUseCase
from ...core.exceptions import ValidationError, ProcessingError


class RoadmapRecommendationController:
    """Controller for roadmap recommendation API endpoint"""

    def __init__(self, recommendation_use_case: RoadmapRecommendationUseCase):
        self.recommendation_use_case = recommendation_use_case
        self.router = APIRouter(tags=["Roadmap Recommendation"])
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post(
            "/recommend-roadmap",
            response_model=RecommendRoadmapResponse,
            status_code=status.HTTP_200_OK,
            summary="Recommend the best roadmap for a user",
            description="Use AI to select the most suitable learning roadmap based on the user's profile and available roadmaps",
        )
        async def recommend_roadmap(request: RecommendRoadmapRequest):
            """Recommend the best roadmap for a new user"""
            try:
                result = await self.recommendation_use_case.recommend(request)
                return result
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e),
                )


def create_roadmap_recommendation_router(
    recommendation_use_case: RoadmapRecommendationUseCase,
) -> APIRouter:
    """Factory function to create roadmap recommendation router"""
    controller = RoadmapRecommendationController(recommendation_use_case)
    return controller.router
