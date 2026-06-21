"""Use case for generating a skill with lessons using AI"""
import json
import asyncio
import logging

from ...domain.services.ai_service import AIService
from ..dtos.skill_generation_dtos import (
    GenerateSkillRequest,
    GenerateSkillResponse,
    GeneratedLesson,
)
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)

# Fixed lesson structure: level -> (count, focus_description)
LESSON_STRUCTURE = {
    1: (5, "vocabulary exercises"),
    2: (3, "grammar exercises"),
    3: (3, "mixed practice (writing & translation)"),
    4: (1, "podcast listening comprehension"),
    5: (3, "beginner-friendly practice"),
    6: (3, "image description & writing"),
    7: (1, "final comprehensive assessment"),
}

SKILL_GENERATION_PROMPT = """You are VocabuRex's skill content generation engine.

Generate a thematic English learning skill for the following milestone:

MILESTONE: {milestone_title}
TARGET LEVEL: {milestone_target_level}
USER PROFICIENCY: {proficiency_level}
LEARNING GOALS: {learning_goals}

The skill must have EXACTLY 19 lessons distributed across 7 levels as follows:
- Level 1: 5 lessons focused on vocabulary exercises (positions 1-5)
- Level 2: 3 lessons focused on grammar exercises (positions 1-3)
- Level 3: 3 lessons focused on mixed practice - writing & translation (positions 1-3)
- Level 4: 1 lesson focused on podcast listening comprehension (position 1)
- Level 5: 3 lessons focused on beginner-friendly practice (positions 1-3)
- Level 6: 3 lessons focused on image description & writing (positions 1-3)
- Level 7: 1 lesson as final comprehensive assessment (position 1)

RULES:
1. The skill title should be thematic and relevant to the milestone (e.g. "Daily Conversations", "Travel English", "Business Communication").
2. The description should explain what the learner will achieve.
3. Each lesson title should be descriptive and indicate what the learner will practice.
4. Lessons within the same level should cover different subtopics but stay within the level's focus.
5. Content difficulty should match the TARGET LEVEL.

You MUST respond with ONLY a valid JSON object:
{{
  "title": "Skill title",
  "description": "What the learner will master in this skill",
  "lessons": [
    {{ "level": 1, "position": 1, "title": "Lesson title for vocabulary topic 1" }},
    {{ "level": 1, "position": 2, "title": "Lesson title for vocabulary topic 2" }},
    {{ "level": 1, "position": 3, "title": "Lesson title for vocabulary topic 3" }},
    {{ "level": 1, "position": 4, "title": "Lesson title for vocabulary topic 4" }},
    {{ "level": 1, "position": 5, "title": "Lesson title for vocabulary topic 5" }},
    {{ "level": 2, "position": 1, "title": "Grammar lesson 1" }},
    {{ "level": 2, "position": 2, "title": "Grammar lesson 2" }},
    {{ "level": 2, "position": 3, "title": "Grammar lesson 3" }},
    {{ "level": 3, "position": 1, "title": "Mixed practice 1" }},
    {{ "level": 3, "position": 2, "title": "Mixed practice 2" }},
    {{ "level": 3, "position": 3, "title": "Mixed practice 3" }},
    {{ "level": 4, "position": 1, "title": "Podcast listening lesson" }},
    {{ "level": 5, "position": 1, "title": "Practice lesson 1" }},
    {{ "level": 5, "position": 2, "title": "Practice lesson 2" }},
    {{ "level": 5, "position": 3, "title": "Practice lesson 3" }},
    {{ "level": 6, "position": 1, "title": "Image & writing 1" }},
    {{ "level": 6, "position": 2, "title": "Image & writing 2" }},
    {{ "level": 6, "position": 3, "title": "Image & writing 3" }},
    {{ "level": 7, "position": 1, "title": "Comprehensive assessment" }}
  ]
}}

Do NOT include any other text. Only the JSON object."""


class SkillGenerationUseCase:
    """Use case that asks AI to generate a skill with 19 lessons across 7 levels"""

    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service

    async def generate(self, request: GenerateSkillRequest) -> GenerateSkillResponse:
        """Generate a skill with lessons"""

        prompt = SKILL_GENERATION_PROMPT.format(
            milestone_title=request.milestoneTitle,
            milestone_target_level=request.milestoneTargetLevel,
            proficiency_level=request.proficiencyLevel or "BEGINNER",
            learning_goals=", ".join(request.learningGoals) if request.learningGoals else "General English",
        )

        try:
            response_text = await self.ai_service.generate_response_with_system_prompt(
                message_history=[{"role": "user", "parts": ["Generate a skill for my learning milestone."]}],
                system_prompt=prompt,
            )

            result = self._parse_response(response_text)
            logger.info(f"AI generated skill: '{result.title}' with {len(result.lessons)} lessons")
            return result

        except ProcessingError:
            raise
        except Exception as e:
            logger.error(f"AI skill generation failed: {e}")
            raise ProcessingError(f"Failed to generate skill: {str(e)}")

    def _parse_response(self, response_text: str) -> GenerateSkillResponse:
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
            logger.error(f"Could not parse AI response: {response_text[:300]}")
            raise ProcessingError("AI returned invalid JSON for skill generation")

        lessons_data = data.get("lessons", [])

        # Validate lesson structure
        lessons = []
        for item in lessons_data:
            level = item.get("level", 1)
            position = item.get("position", 1)
            title = item.get("title", f"Lesson {level}-{position}")

            if 1 <= level <= 7 and position >= 1:
                lessons.append(GeneratedLesson(
                    level=level,
                    position=position,
                    title=title,
                ))

        # Ensure we have all 19 lessons; fill in missing ones
        expected_lessons = []
        for level, (count, focus) in LESSON_STRUCTURE.items():
            existing = [l for l in lessons if l.level == level]
            for pos in range(1, count + 1):
                match = next((l for l in existing if l.position == pos), None)
                if match:
                    expected_lessons.append(match)
                else:
                    expected_lessons.append(GeneratedLesson(
                        level=level,
                        position=pos,
                        title=f"{focus.capitalize()} - Part {pos}",
                    ))

        return GenerateSkillResponse(
            title=data.get("title", "English Learning Skill"),
            description=data.get("description", "A comprehensive learning skill"),
            lessons=expected_lessons,
        )
