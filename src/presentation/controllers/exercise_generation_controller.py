"""Exercise generation controller"""
from fastapi import APIRouter, HTTPException, status
import logging

from ...application.dtos.exercise_generation_dtos import (
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
)
from ...application.use_cases.exercise_generation_use_case import ExerciseGenerationUseCase
from ...core.exceptions import ValidationError, ProcessingError

logger = logging.getLogger(__name__)


class ExerciseGenerationController:
    """Controller for exercise generation API endpoints"""

    def __init__(self, generation_use_case: ExerciseGenerationUseCase):
        self.generation_use_case = generation_use_case
        self.router = APIRouter(prefix="/exercises", tags=["Exercise Generation"])
        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        @self.router.post(
            "/generate",
            response_model=ExerciseGenerationResponse,
            status_code=status.HTTP_200_OK,
            summary="Generate exercises using AI",
            description="Generate English learning exercises using Gemini AI based on topic and difficulty",
        )
        async def generate_exercises(request: ExerciseGenerationRequest):
            """Generate exercises using AI"""
            try:
                result = await self.generation_use_case.generate(request)
                return result
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
            except Exception as e:
                logger.error(f"Unexpected error in exercise generation: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate exercises: {str(e)}",
                )


def create_exercise_generation_router(
    generation_use_case: ExerciseGenerationUseCase,
) -> APIRouter:
    """Factory function to create exercise generation router"""
    controller = ExerciseGenerationController(generation_use_case)
    return controller.router
