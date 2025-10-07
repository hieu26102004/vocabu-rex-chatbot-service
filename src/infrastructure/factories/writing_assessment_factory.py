"""Dependency injection factory for writing assessment"""
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...application.use_cases.writing_assessment_use_case import WritingAssessmentUseCase
from ..repositories.mongo_writing_assessment_repository import MongoWritingAssessmentRepository
from ..external.ai_service_adapter import GeminiAIServiceAdapter
from ...presentation.controllers.writing_assessment_controller import create_writing_assessment_router


class WritingAssessmentFactory:
    """Factory for creating writing assessment components"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        
        # Initialize repository
        self.assessment_repository = MongoWritingAssessmentRepository(
            database.writing_assessments
        )
        
        # Initialize AI service
        self.ai_service = GeminiAIServiceAdapter()
        
        # Initialize use case
        self.assessment_use_case = WritingAssessmentUseCase(
            self.assessment_repository,
            self.ai_service
        )
    
    def create_router(self):
        """Create writing assessment router"""
        return create_writing_assessment_router(self.assessment_use_case)