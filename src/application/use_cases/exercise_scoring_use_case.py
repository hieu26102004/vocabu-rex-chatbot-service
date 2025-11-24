"""Exercise scoring use case for learning service integration"""
from typing import Dict, Any
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
            
            # Calculate score using simple rule-based approach
            score_result = self._calculate_score(
                request.user_answer,
                exercise_meta
            )
            
            return WritingPromptScoreResponse(
                is_correct=score_result['is_correct'],
                score_percentage=score_result['score_percentage'],
                feedback=score_result['feedback'],
                performance_level=score_result['performance_level']
            )
            
        except Exception as e:
            raise ProcessingError(f"Failed to score writing prompt: {str(e)}")
    
    async def score_translate(self, request: TranslateScoreRequest) -> TranslateScoreResponse:
        """Score a translate exercise"""
        try:
            # Validate request
            self._validate_translate_request(request)
            
            # Calculate translation accuracy
            score_result = self._calculate_translation_score(
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
        
        required_meta_fields = ['prompt', 'minWords', 'maxWords', 'exampleAnswer']
        for field in required_meta_fields:
            if field not in request.exercise_meta:
                raise ValidationError(f"Exercise metadata missing required field: {field}")
    
    def _calculate_score(self, user_answer: str, exercise_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Simple scoring logic based on prompt and example answer"""
        min_words = exercise_meta.get('minWords', 30)
        max_words = exercise_meta.get('maxWords', 100)
        example_answer = exercise_meta.get('exampleAnswer', '')
        prompt = exercise_meta.get('prompt', '')
        
        words = user_answer.strip().split()
        word_count = len(words)
        
        # Word count score (40 points) - encourage longer writing but don't require min_words
        if word_count >= max_words:
            word_score = 35  # Slightly penalize for being too long
        elif word_count >= min_words:
            word_score = 40  # Perfect score for meeting target range
        elif word_count >= min_words * 0.7:
            word_score = 35  # Good score for reasonable length
        elif word_count >= min_words * 0.5:
            word_score = 30  # Decent score for moderate length
        elif word_count >= 10:
            word_score = 25  # Basic score for having some content
        else:
            word_score = 15  # Minimum score for very short answers
        
        # Content similarity score (40 points) - compare with example answer
        content_score = self._calculate_content_similarity(user_answer, example_answer, prompt)
        
        # Basic grammar score (20 points)
        grammar_score = 20
        if not user_answer.strip().endswith(('.', '!', '?')):
            grammar_score -= 5
        if not user_answer[0].isupper():
            grammar_score -= 5
            
        # Total score
        total_score = word_score + content_score + grammar_score
        
        # Determine result
        is_correct = total_score >= 60
        performance_level = self._get_performance_level(total_score)
        feedback = self._get_feedback(total_score, word_count, min_words, max_words, content_score)
        
        return {
            'is_correct': is_correct,
            'score_percentage': float(total_score),
            'feedback': feedback,
            'performance_level': performance_level
        }
    
    def _calculate_content_similarity(self, user_answer: str, example_answer: str, prompt: str) -> int:
        """Calculate content similarity based on keywords and topics"""
        # Extract key words from example answer and prompt
        example_words = set(word.lower() for word in example_answer.split() if len(word) > 2)
        prompt_words = set(word.lower() for word in prompt.split() if len(word) > 2)
        user_words = set(word.lower() for word in user_answer.split() if len(word) > 2)
        
        # Combine important words from example and prompt
        important_words = example_words.union(prompt_words)
        
        # Calculate overlap
        if len(important_words) == 0:
            return 20  # Default score if no comparison possible
            
        overlap_count = len(user_words.intersection(important_words))
        similarity_ratio = overlap_count / len(important_words)
        
        # Convert to score out of 40
        content_score = int(similarity_ratio * 40)
        
        # Bonus for addressing the topic directly
        topic_keywords = ['breakfast', 'eat', 'drink', 'food', 'morning', 'meal']
        topic_matches = sum(1 for word in topic_keywords if word in user_answer.lower())
        if topic_matches >= 2:
            content_score += 5
        
        return min(40, content_score)
    
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
    
    def _calculate_translation_score(self, user_answer: str, source_text: str, correct_answer: str) -> dict:
        """Calculate translation score based on similarity to correct answer and understanding of source text"""
        user_answer = user_answer.strip().lower()
        correct_answer = correct_answer.strip().lower()
        source_text = source_text.strip().lower()
        
        # Exact match check
        if user_answer == correct_answer:
            return {
                'is_correct': True,
                'feedback': 'Perfect! Your translation is exactly correct.'
            }
        
        # Calculate similarity score with correct answer
        similarity_score = self._calculate_text_similarity(user_answer, correct_answer)
        
        # Check for key words/phrases from correct answer
        correct_words = set(correct_answer.split())
        user_words = set(user_answer.split())
        
        # Calculate word overlap with correct answer
        overlap = len(correct_words.intersection(user_words))
        total_words = len(correct_words)
        
        if total_words == 0:
            word_overlap_ratio = 0
        else:
            word_overlap_ratio = overlap / total_words
        
        # Additional check: Does the translation make sense for the source text?
        # Extract key concepts from source text that should be reflected in translation
        source_meaning_score = self._check_translation_meaning(user_answer, source_text, correct_answer)
        
        # Combine scores for final decision
        # Lower the threshold since we're considering source context
        is_correct = (
            similarity_score > 0.6 or 
            word_overlap_ratio > 0.7 or
            (similarity_score > 0.4 and source_meaning_score > 0.6)
        )
        
        # Generate feedback based on different aspects
        if similarity_score > 0.9:
            feedback = "Excellent! Your translation is very close to the correct answer."
        elif similarity_score > 0.7:
            feedback = "Good! Your translation captures the main meaning well."
        elif similarity_score > 0.5 and source_meaning_score > 0.6:
            feedback = "Good understanding! Your translation conveys the source meaning correctly."
        elif word_overlap_ratio > 0.6:
            feedback = "Close! You have most of the key words but check the structure."
        elif source_meaning_score > 0.5:
            feedback = "You understand the source text, but try to match the expected translation style."
        else:
            feedback = f"Keep trying! The correct answer is: '{correct_answer.title()}'. Make sure to capture the meaning of: '{source_text}'"
        
        return {
            'is_correct': is_correct,
            'feedback': feedback
        }
    
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