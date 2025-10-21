"""Exercise scoring use case for learning service integration"""
from typing import Dict, Any
from ..dtos.exercise_scoring_dtos import (
    WritingPromptScoreRequest,
    WritingPromptScoreResponse
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