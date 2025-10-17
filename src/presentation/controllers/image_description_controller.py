"""Image description scoring controller for REST API endpoints"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from ...application.dtos.image_description_dtos import (
    ImageDescriptionScoreRequest,
    ImageDescriptionScoreResponse
)
from ...application.use_cases.image_description_scoring_use_case import ImageDescriptionScoringUseCase
from ...core.exceptions import ValidationError, ProcessingError


class ImageDescriptionScoringController:
    """Controller for image description scoring API endpoints"""
    
    def __init__(self, scoring_use_case: ImageDescriptionScoringUseCase):
        self.scoring_use_case = scoring_use_case
        self.router = APIRouter(prefix="/image-description", tags=["Image Description Scoring"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post(
            "/score",
            response_model=ImageDescriptionScoreResponse,
            status_code=status.HTTP_200_OK,
            summary="Score image description",
            description="Score a user's image description against expected results"
        )
        async def score_image_description(request: ImageDescriptionScoreRequest):
            """Score image description"""
            try:
                result = await self.scoring_use_case.score_image_description(request)
                return result
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )


def create_image_description_scoring_router(scoring_use_case: ImageDescriptionScoringUseCase) -> APIRouter:
    """Factory function to create image description scoring router"""
    controller = ImageDescriptionScoringController(scoring_use_case)
    return controller.router