"""Data Transfer Objects for skill generation API"""
from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateSkillRequest(BaseModel):
    """Request to generate a skill with lessons"""
    milestoneTitle: str = Field(..., description="Title of the milestone this skill belongs to")
    milestoneTargetLevel: str = Field(..., description="Target proficiency level of the milestone")
    proficiencyLevel: Optional[str] = Field(None, description="User's current proficiency level")
    learningGoals: Optional[List[str]] = Field(None, description="User's learning goals")
    skillIndex: int = Field(0, description="Index of the skill within the milestone (for uniqueness)")


class GeneratedLesson(BaseModel):
    """A single lesson in the generated skill"""
    level: int = Field(..., ge=1, le=7, description="Skill level (1-7)")
    position: int = Field(..., ge=1, description="Position within the level")
    title: str = Field(..., description="Lesson title")


class GenerateSkillResponse(BaseModel):
    """Response with the generated skill structure"""
    title: str = Field(..., description="Skill title")
    description: str = Field(..., description="Skill description")
    lessons: List[GeneratedLesson] = Field(..., description="List of 19 lessons across 7 levels")
