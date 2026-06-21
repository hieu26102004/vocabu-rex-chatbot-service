"""Use case for generating a personalized roadmap using AI"""
import json
import asyncio
import logging

from ...domain.services.ai_service import AIService
from ..dtos.roadmap_generation_dtos import (
    GenerateRoadmapRequest,
    GenerateRoadmapResponse,
    GeneratedMilestone,
)
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)

VALID_LEARNING_GOALS = ["CONNECT", "TRAVEL", "STUDY", "ENTERTAINMENT", "CAREER", "HOBBY"]
VALID_PROFICIENCY_LEVELS = [
    "BEGINNER", "ELEMENTARY", "INTERMEDIATE",
    "UPPER_INTERMEDIATE", "ADVANCED", "PROFICIENT",
]

ROADMAP_GENERATION_PROMPT = """You are VocabuRex's roadmap generation engine.

Create a personalized English learning roadmap with EXACTLY 10 milestones for a user with the following profile:

USER PROFILE:
{user_profile}

RULES:
1. The roadmap must have a clear, descriptive title in English.
2. targetGoal MUST be one of: {valid_goals}
   Pick the one that best matches the user's learning goals.
3. Each milestone must have:
   - A descriptive title (e.g. "Foundation Building - Basic Greetings & Introductions")
   - A targetLevel from this list IN ASCENDING ORDER: {valid_levels}
   - Milestones should progress from easier to harder levels
   - Early milestones can share the same level, but overall trend must be ascending
4. Generate EXACTLY 10 milestones with order from 0 to 9.
5. The description should summarize the roadmap's learning journey.

You MUST respond with ONLY a valid JSON object in this exact format:
{{
  "title": "Roadmap title",
  "targetGoal": "CAREER",
  "description": "Description of the learning journey",
  "milestones": [
    {{ "title": "Milestone 1 title", "targetLevel": "BEGINNER", "order": 0 }},
    {{ "title": "Milestone 2 title", "targetLevel": "BEGINNER", "order": 1 }},
    {{ "title": "Milestone 3 title", "targetLevel": "ELEMENTARY", "order": 2 }},
    ...
  ]
}}

Do NOT include any other text, explanation, or formatting. Only the JSON object."""


class RoadmapGenerationUseCase:
    """Use case that asks AI to generate a full roadmap with 10 milestones"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def generate(self, request: GenerateRoadmapRequest) -> GenerateRoadmapResponse:
        """Generate a personalized roadmap"""

        user_profile_parts = []
        if request.targetLanguage:
            user_profile_parts.append(f"- Target Language: {request.targetLanguage}")
        if request.proficiencyLevel:
            user_profile_parts.append(f"- Current Proficiency: {request.proficiencyLevel}")
        if request.learningGoals:
            user_profile_parts.append(f"- Learning Goals: {', '.join(request.learningGoals)}")
        if request.dailyGoalMinutes is not None:
            user_profile_parts.append(f"- Daily Study Goal: {request.dailyGoalMinutes} minutes")

        user_profile_str = "\n".join(user_profile_parts) if user_profile_parts else "- General English learner"

        prompt = ROADMAP_GENERATION_PROMPT.format(
            user_profile=user_profile_str,
            valid_goals=", ".join(VALID_LEARNING_GOALS),
            valid_levels=", ".join(VALID_PROFICIENCY_LEVELS),
        )

        try:
            response_text = await self.ai_service.generate_response_with_system_prompt(
                message_history=[{"role": "user", "parts": ["Generate a personalized learning roadmap for me."]}],
                system_prompt=prompt,
            )

            result = self._parse_response(response_text)
            logger.info(f"AI generated roadmap: '{result.title}' with {len(result.milestones)} milestones")
            return result

        except Exception as e:
            logger.error(f"AI roadmap generation failed: {e}")
            raise ProcessingError(f"Failed to generate roadmap: {str(e)}")

    def _parse_response(self, response_text: str) -> GenerateRoadmapResponse:
        """Parse and validate AI response"""
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error(f"Could not parse AI response as JSON: {response_text[:300]}")
            raise ProcessingError("AI returned invalid JSON for roadmap generation")

        # Validate targetGoal
        target_goal = data.get("targetGoal", "CONNECT")
        if target_goal not in VALID_LEARNING_GOALS:
            logger.warning(f"AI returned invalid targetGoal '{target_goal}', defaulting to CONNECT")
            target_goal = "CONNECT"

        # Validate milestones
        milestones_data = data.get("milestones", [])
        if len(milestones_data) != 10:
            logger.warning(f"AI returned {len(milestones_data)} milestones instead of 10")
            if len(milestones_data) < 10:
                raise ProcessingError(f"AI generated only {len(milestones_data)} milestones, expected 10")
            milestones_data = milestones_data[:10]

        milestones = []
        for i, m in enumerate(milestones_data):
            target_level = m.get("targetLevel", "BEGINNER")
            if target_level not in VALID_PROFICIENCY_LEVELS:
                target_level = "BEGINNER"
            milestones.append(GeneratedMilestone(
                title=m.get("title", f"Milestone {i + 1}"),
                targetLevel=target_level,
                order=i,
            ))

        return GenerateRoadmapResponse(
            title=data.get("title", "Personalized English Learning Roadmap"),
            targetGoal=target_goal,
            description=data.get("description", "A personalized learning journey"),
            milestones=milestones,
        )
