"""Writing assessment controller for REST API endpoints"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from typing import Optional

from ...application.dtos.writing_assessment_dtos import (
    WritingAssessmentRequest,
    WritingAssessmentResponse,
    DetailedFeedbackResponse,
    AssessmentHistoryResponse,
    AssessmentStatusResponse,
    ErrorResponse
)
from ...application.use_cases.writing_assessment_use_case import WritingAssessmentUseCase
from ...core.exceptions import ValidationError, ProcessingError, NotFoundError


class WritingAssessmentController:
    """Controller for writing assessment API endpoints"""
    
    def __init__(self, assessment_use_case: WritingAssessmentUseCase):
        self.assessment_use_case = assessment_use_case
        self.router = APIRouter(prefix="/writing-assessment", tags=["Writing Assessment"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.router.post(
            "/submit",
            response_model=WritingAssessmentResponse,
            status_code=status.HTTP_202_ACCEPTED,
            summary="Submit writing for assessment",
            description="Submit a piece of writing for AI-powered assessment and scoring"
        )
        async def submit_writing_assessment(request: WritingAssessmentRequest):
            """Submit writing for assessment"""
            try:
                result = await self.assessment_use_case.submit_writing_for_assessment(request)
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
        
        @self.router.get(
            "/{assessment_id}/status",
            response_model=AssessmentStatusResponse,
            summary="Get assessment status",
            description="Get the current processing status of an assessment"
        )
        async def get_assessment_status(
            assessment_id: str,
            user_id: str
        ):
            """Get assessment processing status"""
            try:
                result = await self.assessment_use_case.get_assessment_status(assessment_id, user_id)
                return result
            except NotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
        
        @self.router.get(
            "/{assessment_id}",
            response_model=WritingAssessmentResponse,
            summary="Get assessment result",
            description="Get the complete assessment result including scores"
        )
        async def get_assessment_result(
            assessment_id: str,
            user_id: str
        ):
            """Get complete assessment result"""
            try:
                result = await self.assessment_use_case.get_assessment_result(assessment_id, user_id)
                return result
            except NotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
        
        @self.router.get(
            "/{assessment_id}/feedback",
            response_model=DetailedFeedbackResponse,
            summary="Get detailed feedback",
            description="Get comprehensive feedback including error corrections and suggestions"
        )
        async def get_detailed_feedback(
            assessment_id: str,
            user_id: str
        ):
            """Get detailed feedback for assessment"""
            try:
                result = await self.assessment_use_case.get_detailed_feedback(assessment_id, user_id)
                return result
            except NotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
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
        
        @self.router.get(
            "/users/{user_id}/history",
            response_model=AssessmentHistoryResponse,
            summary="Get user assessment history",
            description="Get paginated history of user's writing assessments with statistics"
        )
        async def get_user_assessment_history(
            user_id: str,
            page: int = 1,
            per_page: int = 10
        ):
            """Get user's assessment history"""
            try:
                # Validate pagination parameters
                if page < 1:
                    raise ValidationError("Page number must be greater than 0")
                if per_page < 1 or per_page > 100:
                    raise ValidationError("Per page must be between 1 and 100")
                
                result = await self.assessment_use_case.get_user_assessment_history(
                    user_id, page, per_page
                )
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
        
        @self.router.delete(
            "/{assessment_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            summary="Delete assessment",
            description="Delete an assessment and all its associated data"
        )
        async def delete_assessment(
            assessment_id: str,
            user_id: str
        ):
            """Delete assessment"""
            try:
                # First check if assessment exists and belongs to user
                await self.assessment_use_case.get_assessment_result(assessment_id, user_id)
                
                # Delete the assessment
                success = await self.assessment_use_case.assessment_repository.delete(assessment_id)
                if not success:
                    raise ProcessingError("Failed to delete assessment")
                
                return None
            except NotFoundError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=str(e)
                )
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=str(e)
                )
            except ProcessingError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=str(e)
                )
        
        @self.router.post(
            "/{assessment_id}/retry",
            response_model=WritingAssessmentResponse,
            summary="Retry failed assessment",
            description="Retry processing a failed assessment"
        )
        async def retry_assessment(
            assessment_id: str,
            user_id: str,
            background_tasks: BackgroundTasks
        ):
            """Retry failed assessment"""
            try:
                # Get existing assessment
                assessment = await self.assessment_use_case.assessment_repository.get_by_id(assessment_id)
                if not assessment:
                    raise NotFoundError(f"Assessment {assessment_id} not found")
                
                # Check user permission
                if assessment.submission.user_id != user_id:
                    raise ValidationError("Access denied to this assessment")
                
                # Check if assessment can be retried
                if assessment.status not in ["failed"]:
                    raise ValidationError("Only failed assessments can be retried")
                
                # Reset assessment status
                assessment.status = "pending"
                assessment.error_message = None
                assessment.started_at = None
                assessment.completed_at = None
                assessment.result = None
                
                # Save updated assessment
                await self.assessment_use_case.assessment_repository.save(assessment)
                
                # Start processing in background
                background_tasks.add_task(
                    self.assessment_use_case._process_assessment_async,
                    assessment_id
                )
                
                return self.assessment_use_case._map_assessment_to_response(assessment)
                
            except (NotFoundError, ValidationError):
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to retry assessment: {str(e)}"
                )


def create_writing_assessment_router(assessment_use_case: WritingAssessmentUseCase) -> APIRouter:
    """Factory function to create writing assessment router"""
    controller = WritingAssessmentController(assessment_use_case)
    return controller.router