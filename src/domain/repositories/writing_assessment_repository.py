"""Writing assessment repository interfaces"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from ..entities.writing_assessment import WritingAssessment


class WritingAssessmentRepository(ABC):
    """Repository interface for writing assessments"""
    
    @abstractmethod
    async def save(self, assessment: WritingAssessment) -> None:
        """Save or update an assessment"""
        pass
    
    @abstractmethod
    async def get_by_id(self, assessment_id: str) -> Optional[WritingAssessment]:
        """Get assessment by ID"""
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> List[WritingAssessment]:
        """Get all assessments for a user"""
        pass
    
    @abstractmethod
    async def get_by_user_id_paginated(
        self, 
        user_id: str, 
        page: int, 
        per_page: int
    ) -> Tuple[List[WritingAssessment], int]:
        """Get paginated assessments for a user"""
        pass
    
    @abstractmethod
    async def delete(self, assessment_id: str) -> bool:
        """Delete an assessment"""
        pass
    
    @abstractmethod
    async def get_recent_assessments(
        self, 
        limit: int = 10
    ) -> List[WritingAssessment]:
        """Get recent assessments across all users"""
        pass