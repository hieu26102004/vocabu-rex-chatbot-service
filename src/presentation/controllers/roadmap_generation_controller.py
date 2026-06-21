"""Roadmap generation controller"""
from fastapi import APIRouter, HTTPException, status

from ...application.dtos.roadmap_generation_dtos import (
    GenerateRoadmapRequest,
    GenerateRoadmapResponse,
)
from ...application.use_cases.roadmap_generation_use_case import RoadmapGenerationUseCase
from ...core.exceptions import ProcessingError


class RoadmapGenerationController:
    """Controller for roadmap generation API endpoint"""

    def __init__(self, generation_use_case: RoadmapGenerationUseCase):
        self.generation_use_case = generation_use_case
        self.router = APIRouter(tags=["Roadmap Generation"])
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post(
            "/generate-roadmap",
            response_model=GenerateRoadmapResponse,
            status_code=status.HTTP_200_OK,
            summary="Generate a personalized roadmap with 10 milestones",
            description="Use AI to create a complete learning roadmap based on user profile",
        )
        async def generate_roadmap(request: GenerateRoadmapRequest):
            """Generate a personalized learning roadmap"""
            try:
                result = await self.generation_use_case.generate(request)
                return result
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e),
                )


def create_roadmap_generation_router(
    generation_use_case: RoadmapGenerationUseCase,
) -> APIRouter:
    """Factory function to create roadmap generation router"""
    controller = RoadmapGenerationController(generation_use_case)
    return controller.router
