"""Exercise scoring use case for learning service integration"""
from typing import Dict, Any, Tuple
from ..dtos.exercise_scoring_dtos import (
    WritingPromptScoreRequest,
    WritingPromptScoreResponse,
    TranslateScoreRequest,
    TranslateScoreResponse
)
from ...core.exceptions import ValidationError, ProcessingError
from ...domain.services.ai_service import AIService


class ExerciseScoringUseCase:
    """Use case for scoring exercises from learning service"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        
    async def score_writing_prompt(self, request: WritingPromptScoreRequest) -> WritingPromptScoreResponse:
        """Score a writing prompt exercise"""
        try:
            # Validate request
            self._validate_writing_prompt_request(request)
            
            # Extract exercise metadata
            exercise_meta = request.exercise_meta
            min_words = exercise_meta.get('minWords', 30)
            max_words = exercise_meta.get('maxWords', 100)
            prompt = exercise_meta.get('prompt', '')
            
            # Calculate score using AI-powered approach
            score_result = await self._calculate_score(
                request.user_answer,
                exercise_meta
            )
            
            return WritingPromptScoreResponse(
                is_correct=score_result['is_correct'],
                score_percentage=score_result['score_percentage'],
                feedback=score_result['feedback'],
                performance_level=score_result['performance_level'],
                grammar_feedback=score_result.get('grammar_feedback'),
                vocabulary_feedback=score_result.get('vocabulary_feedback'),
                content_feedback=score_result.get('content_feedback'),
                detailed_errors=score_result.get('detailed_errors', [])
            )
            
        except Exception as e:
            raise ProcessingError(f"Failed to score writing prompt: {str(e)}")
    
    async def score_translate(self, request: TranslateScoreRequest) -> TranslateScoreResponse:
        """Score a translate exercise"""
        try:
            # Validate request
            self._validate_translate_request(request)
            
            # Calculate translation accuracy using AI
            score_result = await self._calculate_translation_score(
                request.user_answer,
                request.source_text,
                request.correct_answer
            )
            
            return TranslateScoreResponse(
                is_correct=score_result['is_correct'],
                feedback=score_result['feedback']
            )
            
        except Exception as e:
            raise ProcessingError(f"Failed to score translation: {str(e)}")
    
    def _validate_translate_request(self, request: TranslateScoreRequest):
        """Validate translate request"""
        if not request.user_answer.strip():
            raise ValidationError("User answer cannot be empty")
        
        if not request.source_text.strip():
            raise ValidationError("Source text cannot be empty")
            
        if not request.correct_answer.strip():
            raise ValidationError("Correct answer cannot be empty")
    
    def _validate_writing_prompt_request(self, request: WritingPromptScoreRequest):
        """Validate writing prompt request"""
        if not request.user_answer.strip():
            raise ValidationError("User answer cannot be empty")
        
        if not request.exercise_meta:
            raise ValidationError("Exercise metadata is required")
        
        required_meta_fields = ['prompt', 'minWords', 'maxWords']
        for field in required_meta_fields:
            if field not in request.exercise_meta:
                raise ValidationError(f"Exercise metadata missing required field: {field}")
    
    async def _calculate_score(self, user_answer: str, exercise_meta: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered scoring logic for writing exercises"""
        min_words = exercise_meta.get('minWords', 30)
        max_words = exercise_meta.get('maxWords', 100)
        prompt = exercise_meta.get('prompt', '')
        criteria = exercise_meta.get('criteria', [])
        example_answer = exercise_meta.get('exampleAnswer', '')
        
        # Use AI to score the writing
        ai_result = await self._score_writing_with_ai(user_answer, prompt, criteria, min_words, max_words, example_answer)
        
        return ai_result
    
    def _calculate_content_criteria(self, user_answer: str, exercise_meta: Dict[str, Any]) -> Tuple[int, float]:
        """Calculate content score based on meeting exercise criteria

        Returns a tuple of (content_score_out_of_40, criteria_ratio)
        """
        criteria = exercise_meta.get('criteria', [])
        prompt = exercise_meta.get('prompt', '')
        
        if not criteria:
            # Fallback to basic prompt relevance if no criteria provided
            return self._calculate_prompt_relevance(user_answer, prompt)
        
        criteria_met = 0
        total_criteria = len(criteria)
        
        for criterion in criteria:
            if self._check_criterion(user_answer, criterion.lower()):
                criteria_met += 1
        
        # Calculate ratio and score
        criteria_ratio = criteria_met / total_criteria if total_criteria > 0 else 0.0
        content_score = int(criteria_ratio * 40)
        
        # Bonus for addressing the prompt topic directly
        prompt_words = set(word.lower() for word in prompt.split() if len(word) > 2)
        user_words = set(word.lower() for word in user_answer.split() if len(word) > 2)
        prompt_overlap = len(user_words.intersection(prompt_words))
        
        if prompt_overlap >= 2:  # User mentions key prompt words
            content_score += 5
        
        return min(40, content_score), criteria_ratio
    
    def _check_criterion(self, user_answer: str, criterion: str) -> bool:
        """Check if user answer meets a specific criterion"""
        user_lower = user_answer.lower()
        
        if 'simple sentences' in criterion or 'simple sentence' in criterion:
            # Check for simple sentence structure (short sentences, basic conjunctions)
            sentences = user_answer.split('.')
            sentences = [s.strip() for s in sentences if s.strip()]
            
            # Consider it simple if most sentences are reasonably short
            simple_count = 0
            for sentence in sentences:
                words = sentence.split()
                # Simple sentences: 3-15 words, not too many complex conjunctions
                if 3 <= len(words) <= 15:
                    complex_words = ['however', 'nevertheless', 'furthermore', 'consequently', 'therefore']
                    if not any(word in sentence.lower() for word in complex_words):
                        simple_count += 1
            
            return simple_count >= len(sentences) * 0.5 or len(sentences) <= 2  # At least 50% simple sentences, or just 1-2 sentences total
        
        elif 'basic vocabulary' in criterion or 'simple vocabulary' in criterion:
            # Check for basic/common words (avoid overly complex vocabulary)
            words = user_answer.split()
            # Very basic check: avoid words longer than 10 characters as proxy for complexity
            complex_words = [word for word in words if len(word) > 10]
            return len(complex_words) <= len(words) * 0.2  # Less than 20% complex words (more lenient)
        
        elif 'personal experience' in criterion or 'personal' in criterion:
            # Check for first-person pronouns and personal experience indicators
            personal_indicators = ['i ', 'my ', 'me ', 'myself', 'i\'m', 'i\'ve', 'i\'ll', 'i\'d']
            return any(indicator in user_lower for indicator in personal_indicators)
        
        elif 'opinion' in criterion or 'thoughts' in criterion:
            # Check for opinion expressions
            opinion_indicators = ['i think', 'i believe', 'in my opinion', 'i feel', 'i like', 'i don\'t like', 'i prefer']
            return any(indicator in user_lower for indicator in opinion_indicators)
        
        else:
            # For unknown criteria, check if the criterion words appear in the answer
            criterion_words = criterion.split()
            return any(word in user_lower for word in criterion_words if len(word) > 2)
    
    def _calculate_prompt_relevance(self, user_answer: str, prompt: str) -> Tuple[int, float]:
        """Fallback function for prompt relevance when no criteria provided"""
        prompt_words = set(word.lower() for word in prompt.split() if len(word) > 2)
        user_words = set(word.lower() for word in user_answer.split() if len(word) > 2)
        
        if len(prompt_words) == 0:
            return 20, 0.5  # Default score and ratio
        
        overlap_count = len(user_words.intersection(prompt_words))
        relevance_ratio = overlap_count / len(prompt_words)
        content_score = int(relevance_ratio * 40)
        
        return min(40, content_score), relevance_ratio
    
    async def _score_writing_with_ai(self, user_answer: str, prompt: str, criteria: list, min_words: int, max_words: int, example_answer: str) -> Dict[str, Any]:
        """Use AI to score writing exercise"""
        try:
            # Prepare context for AI
            criteria_text = ", ".join(criteria) if criteria else "general writing quality"
            
            # Create system prompt
            system_prompt = f"""You are a teacher grading writing exercises. Evaluate student responses fairly and encouragingly.

Return your evaluation in JSON format exactly matching this structure:
{{
  "score_percentage": 85,
  "is_correct": true,
  "performance_level": "good",
  "feedback": "Your overall feedback summary...",
  "grammar_feedback": "Feedback on grammar...",
  "vocabulary_feedback": "Feedback on vocabulary...",
  "content_feedback": "Feedback on content...",
  "detailed_errors": [
    {{
      "original": "Incorrect phrase",
      "corrected": "Corrected phrase",
      "explanation": "Why it is wrong"
    }}
  ]
}}

Be lenient and focus on content quality over length. Accept short answers if they demonstrate understanding of the topic."""
            
            # Create user message
            user_message = f"""Evaluate this writing response:

Prompt: {prompt}
Criteria: {criteria_text}
Word range: {min_words}-{max_words} words
Example answer: {example_answer}

Student response: {user_answer}

Please evaluate and provide detailed JSON feedback including overall feedback, grammar, vocabulary, and specific errors."""
            
            message_history = [{"role": "user", "content": user_message}]
            
            # Retry logic for AI calls (same as image description service)
            import asyncio
            max_retries = 3
            ai_response = None
            
            for attempt in range(max_retries):
                try:
                    # Call AI service with system prompt
                    ai_response = await self.ai_service.generate_response_with_system_prompt(
                        message_history=message_history,
                        system_prompt=system_prompt
                    )
                    
                    # Check if response is valid
                    if ai_response and len(ai_response.strip()) > 10:
                        break
                    else:
                        raise ValueError("Empty or too short response from AI")
                        
                except Exception as e:
                    print(f"AI attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        # Last attempt failed, raise the error
                        raise
                    
                    # Wait briefly before retry
                    await asyncio.sleep(0.5)
            # Log the AI response for debugging
            print(f"AI Response: {ai_response}")
            print(f"AI Response type: {type(ai_response)}")
            
            # Handle different response types from AI service
            if isinstance(ai_response, str):
                # Try to parse as JSON if it's a string
                import json
                try:
                    # Find JSON content (look for first { to last })
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx + 1]
                        result = json.loads(json_str)
                    else:
                        # If no JSON found, parse as text
                        result = self._parse_text_response(ai_response)
                except json.JSONDecodeError:
                    # If not valid JSON, extract info from text response
                    result = self._parse_text_response(ai_response)
            elif isinstance(ai_response, dict):
                result = ai_response
            else:
                # Fallback for unexpected response types
                raise ValueError(f"Unexpected AI response type: {type(ai_response)}")
            
            return {
                'is_correct': result.get('is_correct', True),
                'score_percentage': float(result.get('score_percentage', 75)),
                'feedback': result.get('feedback', 'Good effort!'),
                'performance_level': result.get('performance_level', 'satisfactory'),
                'grammar_feedback': result.get('grammar_feedback'),
                'vocabulary_feedback': result.get('vocabulary_feedback'),
                'content_feedback': result.get('content_feedback'),
                'detailed_errors': result.get('detailed_errors', [])
            }
            
        except Exception as e:
            # Log the error for debugging
            print(f"AI Scoring Error: {str(e)}")
            print(f"Error type: {type(e)}")
            
            # Use rule-based fallback scoring when AI completely fails
            return self._create_rule_based_writing_score(user_answer, prompt, criteria, min_words, max_words)
    
    async def _score_translation_with_ai(self, user_answer: str, source_text: str, correct_answer: str) -> Dict[str, Any]:
        """Use AI to score translation exercise"""
        try:
            # Create system prompt
            system_prompt = """You are a teacher grading translation exercises. Evaluate translations fairly and encouragingly.

Return your evaluation in JSON format:
{
  "is_correct": true,
  "feedback": "Your translation captures the meaning well..."
}

Be lenient - accept translations that capture the main meaning even if not perfect."""
            
            # Create user message
            user_message = f"""Evaluate this translation:

Source text: {source_text}
Correct answer: {correct_answer}
Student translation: {user_answer}

Please evaluate:
1. Accuracy of meaning
2. Grammar and structure
3. Overall quality"""
            
            message_history = [{"role": "user", "content": user_message}]
            
            # Call AI service with system prompt
            ai_response = await self.ai_service.generate_response_with_system_prompt(
                message_history=message_history,
                system_prompt=system_prompt
            )
            
            # Log the AI response for debugging
            print(f"Translation AI Response: {ai_response}")
            print(f"Translation AI Response type: {type(ai_response)}")
            
            # Handle different response types from AI service
            if isinstance(ai_response, str):
                # Try to parse as JSON if it's a string
                import json
                try:
                    # Find JSON content (look for first { to last })
                    start_idx = ai_response.find('{')
                    end_idx = ai_response.rfind('}')
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = ai_response[start_idx:end_idx + 1]
                        result = json.loads(json_str)
                    else:
                        # If no JSON found, parse as text
                        result = self._parse_translation_text_response(ai_response)
                except json.JSONDecodeError:
                    # If not valid JSON, extract info from text response
                    result = self._parse_translation_text_response(ai_response)
            elif isinstance(ai_response, dict):
                result = ai_response
            else:
                # Fallback for unexpected response types
                raise ValueError(f"Unexpected AI response type: {type(ai_response)}")
            
            return {
                'is_correct': result.get('is_correct', True),
                'feedback': result.get('feedback', 'Good translation effort!')
            }
            
        except Exception as e:
            # Log the error for debugging
            print(f"Translation AI Scoring Error: {str(e)}")
            print(f"Error type: {type(e)}")
            
            # Simple fallback if AI fails
            return {
                'is_correct': True,  # Be lenient in fallback
                'feedback': 'Good translation effort!'
            }
    
    def _parse_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse AI text response when JSON parsing fails"""
        # Simple text parsing for common patterns
        result = {
            'is_correct': True,  # Default to correct
            'score_percentage': 75.0,  # Default score
            'feedback': 'Good effort!',
            'performance_level': 'satisfactory'
        }
        
        text_lower = text_response.lower()
        
        # Look for score indicators
        if 'excellent' in text_lower:
            result['score_percentage'] = 90.0
            result['performance_level'] = 'excellent'
        elif 'good' in text_lower:
            result['score_percentage'] = 80.0
            result['performance_level'] = 'good'
        elif 'poor' in text_lower or 'incorrect' in text_lower:
            result['score_percentage'] = 50.0
            result['performance_level'] = 'needs_improvement'
            result['is_correct'] = False
        
        # Use the full response as feedback
        result['feedback'] = text_response
        
        return result
    
    def _parse_translation_text_response(self, text_response: str) -> Dict[str, Any]:
        """Parse AI text response for translation when JSON parsing fails"""
        result = {
            'is_correct': True,  # Default to correct
            'feedback': text_response
        }
        
        text_lower = text_response.lower()
        
        # Look for negative indicators
        if any(word in text_lower for word in ['incorrect', 'wrong', 'poor', 'bad']):
            result['is_correct'] = False
        
        return result
    
    def _create_rule_based_writing_score(self, user_answer: str, prompt: str, criteria: list, min_words: int, max_words: int) -> Dict[str, Any]:
        """Create rule-based scoring when AI fails completely"""
        word_count = len(user_answer.split())
        
        # Basic word matching with prompt
        prompt_words = set(word.lower() for word in prompt.split() if len(word) > 3)
        user_words = set(word.lower() for word in user_answer.split() if len(word) > 3)
        word_overlap = len(user_words.intersection(prompt_words))
        
        # Calculate basic scores
        word_score = 0
        if word_count >= max_words:
            word_score = 35
        elif word_count >= min_words:
            word_score = 40
        elif word_count >= min_words * 0.5:
            word_score = 30
        elif word_count >= 5:
            word_score = 25
        else:
            word_score = 20
            
        # Content relevance score
        content_score = 0
        if word_overlap >= 3:
            content_score = 35
        elif word_overlap >= 2:
            content_score = 30
        elif word_overlap >= 1:
            content_score = 25
        else:
            content_score = 15
            
        # Basic criteria check
        criteria_score = 0
        if criteria:
            criteria_met = sum(1 for criterion in criteria if self._check_criterion(user_answer, criterion.lower()))
            criteria_score = (criteria_met / len(criteria)) * 25
        else:
            criteria_score = 20
            
        total_score = word_score + content_score + criteria_score
        
        # Determine result with lenient thresholds
        is_correct = total_score >= 45 or word_overlap >= 1 or word_count >= 3
        
        # Generate feedback
        if total_score >= 80:
            feedback = f"Excellent work! Your {word_count}-word response addresses the prompt well."
            performance_level = "excellent"
        elif total_score >= 60:
            feedback = f"Good job! Your {word_count}-word response shows understanding."
            performance_level = "good"
        elif total_score >= 45:
            feedback = f"Nice effort! Your {word_count}-word response is on the right track."
            performance_level = "satisfactory"
        else:
            feedback = f"Keep practicing! Your response needs more detail to address the prompt fully."
            performance_level = "needs_improvement"
            
        return {
            'is_correct': is_correct,
            'score_percentage': total_score,
            'feedback': feedback,
            'performance_level': performance_level,
            'grammar_feedback': "Cannot provide grammar analysis in offline mode.",
            'vocabulary_feedback': "Cannot provide vocabulary analysis in offline mode.",
            'content_feedback': f"Word count: {word_count}. Matches with prompt: {word_overlap}.",
            'detailed_errors': []
        }
    
    def _get_performance_level(self, score: int) -> str:
        """Get performance level based on score"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "satisfactory"
        elif score >= 40:
            return "needs_improvement"
        else:
            return "poor"
    
    def _get_feedback(self, score: int, word_count: int, min_words: int, max_words: int, 
                     content_score: int) -> str:
        """Generate simple feedback"""
        if score >= 90:
            return f"Excellent work! Good length ({word_count} words) and great content relevance."
        elif score >= 75:
            return f"Good job! Word count: {word_count} words. Content matches well with the topic."
        elif score >= 60:
            return f"Satisfactory work. Word count: {word_count} words. Try to include more relevant content."
        elif score >= 40:
            if word_count < min_words * 0.7:
                return f"Good start! Try writing a bit more (current: {word_count}, suggested: {min_words}+ words) and focus on the topic."
            else:
                return f"Decent length ({word_count} words) but make sure your answer addresses the prompt topic better."
        else:
            if word_count < 10:
                return f"Please write more to fully answer the question. Aim for at least {min_words} words."
            else:
                return f"Your answer needs to be more relevant to the topic. Current length: {word_count} words."
    
    async def _calculate_translation_score(self, user_answer: str, source_text: str, correct_answer: str) -> dict:
        """AI-powered translation scoring"""
        # Use AI to evaluate translation quality
        ai_result = await self._score_translation_with_ai(user_answer, source_text, correct_answer)
        
        return ai_result
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using simple word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _check_translation_meaning(self, user_answer: str, source_text: str, correct_answer: str) -> float:
        """Check if user's translation captures the meaning of source text"""
        # Create a mapping of common translation patterns
        # This is a simplified approach - in production, you might use more sophisticated NLP
        
        source_words = set(word.lower() for word in source_text.split() if len(word) > 2)
        user_words = set(word.lower() for word in user_answer.split() if len(word) > 2)
        correct_words = set(word.lower() for word in correct_answer.split() if len(word) > 2)
        
        # Check if user translation has similar conceptual words as the correct answer
        conceptual_similarity = len(user_words.intersection(correct_words)) / len(correct_words) if correct_words else 0
        
        # Simple semantic checks for common words/concepts
        meaning_score = conceptual_similarity
        
        # Bonus for capturing key semantic elements
        # Check for common translation patterns (this could be expanded)
        if self._has_similar_semantic_structure(user_answer, correct_answer):
            meaning_score += 0.2
            
        # Check if the translation maintains the general meaning direction
        if self._maintains_meaning_direction(source_text, user_answer, correct_answer):
            meaning_score += 0.1
            
        return min(1.0, meaning_score)
    
    def _has_similar_semantic_structure(self, user_answer: str, correct_answer: str) -> bool:
        """Check if translations have similar semantic structure"""
        # Simple checks for common sentence patterns
        user_lower = user_answer.lower()
        correct_lower = correct_answer.lower()
        
        # Check for similar question/statement structure
        if ('?' in user_answer) == ('?' in correct_answer):
            return True
            
        # Check for similar tense indicators (basic check)
        past_indicators = ['was', 'were', 'did', 'had', 'went', 'came', 'said']
        present_indicators = ['is', 'are', 'do', 'does', 'go', 'come', 'say']
        future_indicators = ['will', 'going to', 'shall']
        
        user_has_past = any(word in user_lower for word in past_indicators)
        correct_has_past = any(word in correct_lower for word in past_indicators)
        
        user_has_present = any(word in user_lower for word in present_indicators)
        correct_has_present = any(word in correct_lower for word in present_indicators)
        
        user_has_future = any(word in user_lower for word in future_indicators)
        correct_has_future = any(word in correct_lower for word in future_indicators)
        
        # If both have similar tense, that's good
        if (user_has_past and correct_has_past) or (user_has_present and correct_has_present) or (user_has_future and correct_has_future):
            return True
            
        return False
    
    def _maintains_meaning_direction(self, source_text: str, user_answer: str, correct_answer: str) -> bool:
        """Check if the translation maintains the general meaning direction"""
        # Very basic check - in a real system, this would be more sophisticated
        
        # Check for negation consistency
        source_negative = any(word in source_text.lower() for word in ['not', 'no', 'never', 'none', 'nothing', 'không', 'chưa', 'chẳng'])
        user_negative = any(word in user_answer.lower() for word in ['not', 'no', 'never', 'none', 'nothing', 'không', 'chưa', 'chẳng'])
        correct_negative = any(word in correct_answer.lower() for word in ['not', 'no', 'never', 'none', 'nothing', 'không', 'chưa', 'chẳng'])
        
        # If source and correct answer have same negation, user should too
        if source_negative == correct_negative:
            return user_negative == correct_negative
            
        # Check for question consistency
        source_question = '?' in source_text
        user_question = '?' in user_answer
        correct_question = '?' in correct_answer
        
        if source_question == correct_question:
            return user_question == correct_question
            
        return True  # Default to true if no clear direction indicators