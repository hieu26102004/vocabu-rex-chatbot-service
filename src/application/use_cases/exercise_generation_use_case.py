"""Use case for generating exercises using AI"""
import json
import re
import asyncio
import logging
from typing import List, Dict, Any

from ..dtos.exercise_generation_dtos import (
    ExerciseGenerationRequest,
    ExerciseGenerationResponse,
    GeneratedExercise,
)
from ..dtos.exercise_meta_dtos import META_TYPE_MAP
from pydantic import ValidationError
from ...infrastructure.external.ai_service_adapter import GeminiAIServiceAdapter
from ...core.exceptions import ProcessingError

logger = logging.getLogger(__name__)

EXERCISE_GENERATION_PROMPT = """You are an English learning exercise generator. Generate exactly {exercise_count} exercises for the topic "{topic}" at "{difficulty}" difficulty level.

You MUST generate exercises using ONLY these exercise types (choose a good mix):

1. **translate** - Translate a sentence
   Meta format: {{ "sourceText": "Vietnamese sentence", "correctAnswer": "English translation", "hints": ["hint1", "hint2"] }}

2. **listen_choose** - Listen and choose the correct answer
   Meta format: {{ "correctAnswer": "correct option", "options": ["option1", "option2", "option3", "option4"], "sentence": "The full sentence being spoken" }}

3. **fill_blank** - Fill in the blank
   Meta format: {{ "sentences": [{{ "text": "I ___ to school every day", "correctAnswer": "go", "options": ["go", "went", "gone", "going"] }}], "context": "Present simple tense" }}

4. **speak** - Speaking practice
   Meta format: {{ "prompt": "Read the following sentence aloud", "expectedText": "The sentence to speak" }}

5. **match** - Match pairs
   Meta format: {{ "pairs": [{{ "left": "English word", "right": "Vietnamese meaning" }}, {{ "left": "word2", "right": "meaning2" }}] }}
   Generate 4-6 pairs per exercise.

6. **multiple_choice** - Multiple choice question
   Meta format: {{ "question": "What is the correct meaning?", "options": [{{ "text": "Option A", "order": 1 }}, {{ "text": "Option B", "order": 2 }}, {{ "text": "Option C", "order": 3 }}, {{ "text": "Option D", "order": 4 }}], "correctOrder": [2] }}
   correctOrder is an array of 1-based indices of correct options.

7. **compare_words** - Compare two words
   Meta format: {{ "instruction": "Are these words similar in meaning?", "word1": "big", "word2": "large", "correctAnswer": true, "explanation": "Both mean having great size" }}

8. **writing_prompt** - Writing exercise
   Meta format: {{ "prompt": "Write about your daily routine", "minWords": 50, "maxWords": 150, "exampleAnswer": "Example answer text", "criteria": ["Use present simple tense", "Include time expressions"] }}

9. **image_description** - Describe an image
   Meta format: {{ "imageUrl": "https://picsum.photos/400/300", "prompt": "Describe what you see in this image", "expectedResults": "A description of what should be in the answer" }}

10. **podcast** - Podcast-style listening comprehension dialogue
    Meta format: {{
      "title": "Dialogue title",
      "description": "Brief description of the dialogue",
      "showTranscript": true,
      "media": {{ "type": "none", "url": null, "thumbnailUrl": null }},
      "segments": [
        {{
          "order": 1,
          "transcript": "Speaker's dialogue text",
          "voiceGender": "female",
          "questions": null
        }},
        {{
          "order": 2,
          "transcript": "Another speaker's text",
          "voiceGender": "male",
          "questions": [
            {{
              "type": "match",
              "question": "Match instruction text",
              "pairs": [{{ "left": "English", "right": "Vietnamese" }}]
            }}
          ]
        }}
      ]
    }}
    CRITICAL RULES FOR PODCAST:
    You MUST generate EXACTLY 12 segments alternating between 'female' and 'male' speakers (starting with 'female').
    You MUST follow this EXACT sequence of question types for each segment's "questions" field (do not deviate!):
    - Segment 1 (female): questions: null
    - Segment 2 (male): questions: [{{ "type": "match", "question": "...", "pairs": [{{ "left": "Eng", "right": "Viet" }}, ... ] }}] (exactly 4 pairs)
    - Segment 3 (female): questions: [{{ "type": "trueFalse", "statement": "...", "correctAnswer": true/false, "explanation": "..." }}]
    - Segment 4 (male): questions: [{{ "type": "listenChoose", "question": "...", "correctWords": ["a", "b", "c", "d"], "distractorWords": ["e", "f", "g", "h"] }}]
    - Segment 5 (female): questions: [{{ "type": "multipleChoice", "question": "...", "options": ["A", "B", "C", "D"], "correctAnswer": "A" }}]
    - Segment 6 (male): questions: [{{ "type": "trueFalse", "statement": "...", "correctAnswer": true/false, "explanation": "..." }}]
    - Segment 7 (female): questions: [{{ "type": "match", "question": "...", "pairs": [{{ "left": "Eng", "right": "Viet" }}, ... ] }}] (exactly 4 pairs)
    - Segment 8 (male): questions: [{{ "type": "listenChoose", "question": "...", "correctWords": ["a", "b"], "distractorWords": ["c", "d"] }}]
    - Segment 9 (female): questions: [{{ "type": "multipleChoice", "question": "...", "options": ["A", "B", "C", "D"], "correctAnswer": "A" }}]
    - Segment 10 (male): questions: [{{ "type": "trueFalse", "statement": "...", "correctAnswer": true/false, "explanation": "..." }}]
    - Segment 11 (female): questions: null
    - Segment 12 (male): questions: [{{ "type": "match", "question": "...", "pairs": [{{ "left": "Eng", "right": "Viet" }}, ... ] }}] (exactly 4 pairs)

IMPORTANT RULES:
- Generate EXACTLY {exercise_count} exercises
- Use a good MIX of different exercise types (don't repeat the same type consecutively)
- All content must be appropriate for the "{difficulty}" level
- For Vietnamese translations: use natural Vietnamese
- The "prompt" field should be a short instruction for the student
- Respond with ONLY valid strict JSON - NO trailing commas, NO comments, NO single quotes
- Do NOT wrap the response in markdown code blocks

DIFFICULTY GUIDE:
- beginner: Simple words, basic sentences, common topics
- elementary: Short sentences, everyday vocabulary
- intermediate: Moderate complexity, varied vocabulary
- upper_intermediate: Complex sentences, nuanced vocabulary
- advanced: Sophisticated language, idiomatic expressions

You MUST respond with ONLY a raw JSON array (no text before or after). Example:
[
  {{
    "exerciseType": "translate",
    "prompt": "Translate the following sentence",
    "meta": {{ "sourceText": "...", "correctAnswer": "...", "hints": [] }}
  }}
]"""


class ExerciseGenerationUseCase:
    """Use case to generate exercises using Gemini AI"""

    def __init__(self, ai_service: GeminiAIServiceAdapter):
        self.ai_service = ai_service
        # Create a dedicated model with higher token limit for exercise generation
        import google.generativeai as genai
        self._exercise_model = genai.GenerativeModel(
            model_name=ai_service.gemini_service.model.model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
        )

    def _generate_exercises_sync(self, prompt: str) -> str:
        """Synchronous call to Gemini API with high token limit, JSON output, and retry logic"""
        try:
            return self.ai_service.gemini_service.generate_content_with_retry(self._exercise_model, prompt)
        except ProcessingError:
            raise
        except Exception as e:
            raise ProcessingError(f"Gemini API call failed: {str(e)}")

    async def generate(self, request: ExerciseGenerationRequest) -> ExerciseGenerationResponse:
        """Generate exercises using AI"""
        try:
            allowed_types_str = ""
            if request.allowed_types:
                allowed_types_str = f"\n\nCRITICAL RESTRICTION: You MUST ONLY generate exercises from the following types: {', '.join(request.allowed_types)}. DO NOT generate any other exercise types!"

            prompt = EXERCISE_GENERATION_PROMPT.format(
                exercise_count=request.exercise_count,
                topic=request.topic,
                difficulty=request.difficulty,
            ) + allowed_types_str

            logger.info(
                f"Generating {request.exercise_count} exercises: "
                f"topic='{request.topic}', difficulty='{request.difficulty}'"
            )

            # Call Gemini API with higher token limit for JSON exercises
            loop = asyncio.get_event_loop()
            raw_response = await loop.run_in_executor(
                None,
                self._generate_exercises_sync,
                prompt,
            )

            # Parse the JSON response
            exercises = self._parse_response(raw_response)

            logger.info(f"Successfully generated {len(exercises)} exercises")

            return ExerciseGenerationResponse(
                exercises=exercises,
                topic=request.topic,
                difficulty=request.difficulty,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            raise ProcessingError(f"AI returned invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Exercise generation failed: {e}")
            raise ProcessingError(f"Failed to generate exercises: {str(e)}")

    def _parse_response(self, raw_response: str) -> List[GeneratedExercise]:
        """Parse the raw AI response into exercise objects"""
        # Clean up response - remove markdown code blocks if present
        cleaned = raw_response.strip()
        if cleaned.startswith("```"):
            # Remove ```json or ``` prefix and trailing ```
            cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned)
            cleaned = re.sub(r'\n?```\s*$', '', cleaned)

        # Fix common AI JSON issues
        cleaned = self._fix_json(cleaned)

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            # Log the problematic response for debugging
            logger.error(f"Raw AI response (first 500 chars): {cleaned[:500]}")
            raise

        if not isinstance(parsed, list):
            raise ProcessingError("AI response is not a JSON array")

        exercises = []
        valid_types = {
            "translate", "listen_choose", "fill_blank", "speak",
            "match", "multiple_choice", "writing_prompt",
            "image_description", "compare_words", "podcast"
        }

        for item in parsed:
            exercise_type = item.get("exerciseType", "")
            if exercise_type not in valid_types:
                logger.warning(f"Skipping invalid exercise type: {exercise_type}")
                continue
                
            meta_data = item.get("meta", {})
            # Validate meta against Pydantic schema
            try:
                meta_model_class = META_TYPE_MAP.get(exercise_type)
                if meta_model_class:
                    meta_model_class(**meta_data)
                else:
                    logger.warning(f"No Pydantic model found for {exercise_type}, skipping validation")
            except ValidationError as ve:
                logger.warning(f"Validation failed for {exercise_type} exercise. Error: {ve}")
                continue # Skip this exercise as it doesn't match the required schema

            exercises.append(GeneratedExercise(
                exerciseType=exercise_type,
                prompt=item.get("prompt", ""),
                meta=meta_data,
            ))

        if not exercises:
            raise ProcessingError("No valid exercises were generated")

        return exercises

    def _fix_json(self, text: str) -> str:
        """Fix common JSON issues from AI responses"""
        # Remove single-line comments (// ...)
        text = re.sub(r'//[^\n]*', '', text)
        # Remove multi-line comments (/* ... */)
        text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
        # Remove trailing commas before } or ]
        text = re.sub(r',\s*([}\]])', r'\1', text)
        # Fix single quotes to double quotes (but not inside strings)
        # This is a simple heuristic - replace 'key': with "key":
        text = re.sub(r"(?<=[{\[,\s])'([^']+?)'(?=\s*:)", r'"\1"', text)
        return text

