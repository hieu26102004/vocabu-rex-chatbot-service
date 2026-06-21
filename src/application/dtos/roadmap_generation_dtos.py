"""Data Transfer Objects for roadmap generation API"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateRoadmapRequest(BaseModel):
    """Request to generate a personalized roadmap"""
    targetLanguage: Optional[str] = Field(None, description="Target language (e.g. 'en')")
    proficiencyLevel: Optional[str] = Field(None, description="User's proficiency level")
    learningGoals: Optional[List[str]] = Field(None, description="User's learning goals")
    dailyGoalMinutes: Optional[int] = Field(None, description="Daily study goal in minutes")


class GeneratedMilestone(BaseModel):
    """A single milestone in the generated roadmap"""
    title: str = Field(..., description="Milestone title")
    targetLevel: str = Field(..., description="Target proficiency level for this milestone")
    order: int = Field(..., description="Order of this milestone (0-based)")


class GenerateRoadmapResponse(BaseModel):
    """Response with the generated roadmap structure"""
    title: str = Field(..., description="Roadmap title")
    targetGoal: str = Field(..., description="Target learning goal enum value")
    description: str = Field(..., description="Roadmap description")
    milestones: List[GeneratedMilestone] = Field(..., description="List of 10 milestones")
