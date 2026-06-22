"""Use case for AI-driven roadmap recommendation"""
import json
import asyncio
import logging
from typing import Optional

from ...domain.services.ai_service import AIService
from ..dtos.roadmap_recommendation_dtos import RecommendRoadmapRequest, RecommendRoadmapResponse

logger = logging.getLogger(__name__)


class RoadmapRecommendationUseCase:
    """Use case that asks AI to select the best roadmap for a user based on their profile"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def recommend(self, request: RecommendRoadmapRequest) -> RecommendRoadmapResponse:
        """Recommend the best roadmap for a user"""

        if not request.existingRoadmaps:
            raise ValueError("No roadmaps available to recommend from")

        # If only one roadmap exists, we still want to check if it's a good fit.
        # So we don't automatically return it anymore unless it's a fallback match.

        # Build the prompt for AI
        roadmaps_description = "\n".join(
            f"  - ID: {r.id}, Title: \"{r.title}\", Target Goal: {r.targetGoal}"
            for r in request.existingRoadmaps
        )

        user_profile = []
        if request.targetLanguage:
            user_profile.append(f"- Target Language: {request.targetLanguage}")
        if request.proficiencyLevel:
            user_profile.append(f"- Proficiency Level: {request.proficiencyLevel}")
        if request.learningGoals:
            user_profile.append(f"- Learning Goals: {', '.join(request.learningGoals)}")
        if request.dailyGoalMinutes is not None:
            user_profile.append(f"- Daily Study Goal: {request.dailyGoalMinutes} minutes")

        user_profile_str = "\n".join(user_profile) if user_profile else "- No specific preferences provided"

        system_prompt = f"""You are VocabuRex's intelligent roadmap recommendation engine.

Your task is to select the BEST learning roadmap for a new user based on their profile and the available roadmaps.

AVAILABLE ROADMAPS:
{roadmaps_description}

USER PROFILE:
{user_profile_str}

INSTRUCTIONS:
1. Analyze the user's learning goals, proficiency level, and daily study commitment.
2. Match these against the available roadmaps' target goals and titles.
3. Select the single best roadmap ID for this user.
4. If the user's learning goals directly match a roadmap's targetGoal, prefer that roadmap.
5. If NO existing roadmap is a suitable fit for the user's specific learning goals and profile, you MUST return an empty string for the roadmapId.

You MUST respond with ONLY a valid JSON object in this exact format:
{{"roadmapId": "<the selected roadmap ID, or empty string if none are suitable>"}}

Do NOT include any other text, explanation, or formatting. Only the JSON object."""

        try:
            # Call AI with the system prompt
            response_text = await self.ai_service.generate_response_with_system_prompt(
                message_history=[{"role": "user", "parts": ["Please recommend the best roadmap for this user."]}],
                system_prompt=system_prompt,
            )

            # Parse the AI response
            roadmap_id = self._parse_response(response_text, request)
            logger.info(f"AI recommended roadmap: {roadmap_id}")
            return RecommendRoadmapResponse(roadmapId=roadmap_id)

        except Exception as e:
            logger.error(f"AI roadmap recommendation failed: {e}")
            # Fallback: try to match learning goals to roadmap targetGoal
            fallback_id = self._fallback_match(request)
            logger.info(f"Using fallback roadmap: {fallback_id}")
            return RecommendRoadmapResponse(roadmapId=fallback_id)

    def _parse_response(self, response_text: str, request: RecommendRoadmapRequest) -> str:
        """Parse AI response and extract roadmap ID, with validation"""
        # Strip markdown code fences if present
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            # Remove opening fence (```json or ```)
            cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
            roadmap_id = data.get("roadmapId", "")
        except (json.JSONDecodeError, AttributeError):
            logger.warning(f"Could not parse AI response as JSON: {response_text[:200]}")
            return self._fallback_match(request)

        # Validate the roadmap ID exists in the available roadmaps
        if roadmap_id == "":
            return ""

        valid_ids = {r.id for r in request.existingRoadmaps}
        if roadmap_id in valid_ids:
            return roadmap_id

        logger.warning(f"AI returned invalid roadmap ID '{roadmap_id}'. Valid IDs: {valid_ids}")
        return self._fallback_match(request)

    def _fallback_match(self, request: RecommendRoadmapRequest) -> str:
        """Simple deterministic fallback: match learning goals to targetGoal, or return empty"""
        if request.learningGoals:
            for roadmap in request.existingRoadmaps:
                if roadmap.targetGoal in request.learningGoals:
                    return roadmap.id

        # Last resort: return empty string so a new roadmap is generated
        return ""
