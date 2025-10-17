"""Dependency injection factory for image description scoring"""
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...application.use_cases.image_description_scoring_use_case import ImageDescriptionScoringUseCase
from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...presentation.controllers.image_description_controller import create_image_description_scoring_router


class ImageDescriptionScoringFactory:
    """Factory for creating image description scoring components"""
    
    def __init__(self, database):
        self.database = database
        
        # Initialize AI service (shared with writing assessment)
        self.ai_service = GeminiAIServiceAdapter()
        
        # Initialize use case
        self.scoring_use_case = ImageDescriptionScoringUseCase(
            self.ai_service
        )
    
    def create_router(self):
        """Create image description scoring router"""
        return create_image_description_scoring_router(self.scoring_use_case)