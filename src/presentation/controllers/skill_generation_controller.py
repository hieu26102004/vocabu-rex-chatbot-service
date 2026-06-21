"""Skill generation controller"""
from fastapi import APIRouter, HTTPException, status

from ...application.dtos.skill_generation_dtos import (
    GenerateSkillRequest,
    GenerateSkillResponse,
)
from ...application.use_cases.skill_generation_use_case import SkillGenerationUseCase
from ...core.exceptions import ProcessingError


class SkillGenerationController:
    """Controller for skill generation API endpoint"""

    def __init__(self, generation_use_case: SkillGenerationUseCase):
        self.generation_use_case = generation_use_case
        self.router = APIRouter(tags=["Skill Generation"])
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post(
            "/generate-skill",
            response_model=GenerateSkillResponse,
            status_code=status.HTTP_200_OK,
            summary="Generate a skill with 19 lessons across 7 levels",
            description="Use AI to create a thematic skill based on milestone context",
        )
        async def generate_skill(request: GenerateSkillRequest):
            """Generate a skill for a milestone"""
            try:
                result = await self.generation_use_case.generate(request)
                return result
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e),
                )


def create_skill_generation_router(
    generation_use_case: SkillGenerationUseCase,
) -> APIRouter:
    """Factory function to create skill generation router"""
    controller = SkillGenerationController(generation_use_case)
    return controller.router
