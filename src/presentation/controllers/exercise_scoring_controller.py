"""Exercise scoring controller for learning service integration"""
from fastapi import APIRouter, HTTPException, status
from typing import Optional

from ...application.dtos.exercise_scoring_dtos import (
    WritingPromptScoreRequest,
    WritingPromptScoreResponse,
    TranslateScoreRequest,
    TranslateScoreResponse
)
from ...application.use_cases.exercise_scoring_use_case import ExerciseScoringUseCase
from ...core.exceptions import ValidationError, ProcessingError


class ExerciseScoringController:
    """Controller for exercise scoring API endpoints"""
    
    def __init__(self, scoring_use_case: ExerciseScoringUseCase):
        self.scoring_use_case = scoring_use_case
        self.router = APIRouter(prefix="/exercise-scoring", tags=["Exercise Scoring"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post(
            "/writing-prompt/score",
            response_model=WritingPromptScoreResponse,
            status_code=status.HTTP_200_OK,
            summary="Score writing prompt exercise",
            description="Score a writing prompt exercise from learning service"
        )
        async def score_writing_prompt(request: WritingPromptScoreRequest):
            """Score writing prompt exercise"""
            try:
                result = await self.scoring_use_case.score_writing_prompt(request)
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
        
        @self.router.post(
            "/translate/score",
            response_model=TranslateScoreResponse,
            status_code=status.HTTP_200_OK,
            summary="Score translate exercise",
            description="Score a translate exercise with user answer, source text, and correct answer"
        )
        async def score_translate(request: TranslateScoreRequest):
            """Score translate exercise"""
            try:
                result = await self.scoring_use_case.score_translate(request)
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


def create_exercise_scoring_router(scoring_use_case: ExerciseScoringUseCase) -> APIRouter:
    """Factory function to create exercise scoring router"""
    controller = ExerciseScoringController(scoring_use_case)
    return controller.router