"""Data Transfer Objects for roadmap recommendation API"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RoadmapInfo(BaseModel):
    """Basic roadmap information for AI context"""
    id: str = Field(..., description="Roadmap ID")
    title: str = Field(..., description="Roadmap title")
    targetGoal: str = Field(..., description="Target learning goal (e.g. CONNECT, CAREER, TRAVEL)")


class RecommendRoadmapRequest(BaseModel):
    """Request to recommend the best roadmap for a user"""
    targetLanguage: Optional[str] = Field(None, description="Target language (e.g. 'en')")
    proficiencyLevel: Optional[str] = Field(None, description="User's proficiency level (e.g. BEGINNER, INTERMEDIATE)")
    learningGoals: Optional[List[str]] = Field(None, description="User's learning goals (e.g. ['CONNECT', 'CAREER'])")
    dailyGoalMinutes: Optional[int] = Field(None, description="Daily study goal in minutes")
    existingRoadmaps: List[RoadmapInfo] = Field(..., description="List of available roadmaps to choose from")


class RecommendRoadmapResponse(BaseModel):
    """Response with the recommended roadmap ID"""
    roadmapId: str = Field(..., description="The ID of the recommended roadmap")
