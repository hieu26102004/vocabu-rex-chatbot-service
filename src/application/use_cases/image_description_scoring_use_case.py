"""Use case for image description scoring"""
from typing import Dict, Any
import asyncio
import json

from ..dtos.image_description_dtos import (
    ImageDescriptionScoreRequest,
    ImageDescriptionScoreResponse
)
from ...domain.services.ai_service import AIService
from ...core.exceptions import ValidationError, ProcessingError


class ImageDescriptionScoringUseCase:
    """Use case for scoring image descriptions"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
    
    async def score_image_description(self, request: ImageDescriptionScoreRequest) -> ImageDescriptionScoreResponse:
        """Score user's image description against expected results"""
        try:
            # Validate input
            await self._validate_request(request)
            
            try:
                # Create AI prompt for scoring
                scoring_result = await self._score_with_ai(
                    user_content=request.user_content,
                    expected_results=request.expected_results,
                    language=request.language
                )
                
                # Parse AI response and return structured result
                return self._parse_scoring_result(scoring_result)
                
            except ProcessingError:
                # If AI completely fails, use rule-based fallback
                return self._create_rule_based_fallback(
                    request.user_content, 
                    request.expected_results,
                    request.language
                )
            
        except ValidationError:
            raise
        except Exception as e:
            raise ProcessingError(f"Failed to score image description: {str(e)}")
    
    async def _validate_request(self, request: ImageDescriptionScoreRequest) -> None:
        """Validate the scoring request"""
        if len(request.user_content.strip()) < 5:
            raise ValidationError("User content is too short")
        
        if len(request.expected_results.strip()) < 5:
            raise ValidationError("Expected results is too short")
    
    async def _score_with_ai(self, user_content: str, expected_results: str, language: str) -> str:
        """Use AI to score the image description with retry logic"""
        
        # Create system prompt for scoring
        system_prompt = self._create_scoring_prompt(language)
        
        # Create user message with content to score
        user_message = f"""
        Expected Answer: {expected_results}
        
        Student's Answer: {user_content}
        
        Please evaluate if the student's description captures the key elements mentioned in the expected answer. The student doesn't need to use identical words, but should convey similar meaning and identify the main subjects and actions.
        """
        
        message_history = [
            {"role": "user", "content": user_message}
        ]
        
        # Retry logic for AI calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get AI response
                response = await self.ai_service.generate_response_with_system_prompt(
                    message_history=message_history,
                    system_prompt=system_prompt
                )
                
                # Check if response is valid
                if response and len(response.strip()) > 10:
                    return response
                else:
                    raise ValueError("Empty or too short response from AI")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed, raise the error
                    raise ProcessingError(f"AI service failed after {max_retries} attempts: {str(e)}")
                
                # Wait briefly before retry
                await asyncio.sleep(0.5)
        
        # Should never reach here, but just in case
        raise ProcessingError("Unexpected error in AI scoring")
    
    def _create_scoring_prompt(self, language: str) -> str:
        """Create system prompt for AI scoring"""
        if language == "vi":
            return """
            Bạn là một giáo viên chấm điểm bài mô tả hình ảnh. Hãy so sánh câu trả lời của học sinh với đáp án mong đợi và đưa ra đánh giá.

            Hãy trả về kết quả theo định dạng JSON sau:
            {
                "is_correct": true/false,
                "score_percentage": 0-100,
                "feedback": "Nhận xét ngắn gọn bằng tiếng Việt",
                "similarity_level": "high/medium/low"
            }

            Tiêu chí chấm điểm (dễ dàng và khuyến khích):
            - Nếu học sinh nhận diện được ít nhất 1-2 yếu tố quan trọng: điểm cao (70-100%)
            - Nếu học sinh có nỗ lực mô tả, dù chưa chính xác hoàn toàn: điểm trung bình (50-69%)
            - Chỉ khi học sinh mô tả hoàn toàn sai hoặc không liên quan: điểm thấp (30-49%)
            
            Hãy khuyến khích học sinh và tập trung vào những gì họ làm đúng thay vì sai sót.
            Học sinh không cần dùng từ hoàn toàn giống nhau, miễn là có liên quan đến nội dung.
            """
        else:
            return """
            You are a teacher grading image description exercises. Compare the student's answer with the expected answer and provide an evaluation.

            Return the result in the following JSON format:
            {
                "is_correct": true/false,
                "score_percentage": 0-100,
                "feedback": "Brief feedback comment in English",
                "similarity_level": "high/medium/low"
            }

            Scoring criteria (encouraging and lenient):
            - If student identifies at least 1-2 key elements (people, actions, objects): high score (70-100%)
            - If student makes an effort to describe, even if not completely accurate: medium score (50-69%)
            - Only if student's description is completely wrong or unrelated: low score (30-49%)
            
            Focus on what students do right rather than their mistakes. Encourage their efforts.
            Students don't need to use identical words, as long as they show understanding of the content.
            """
    
    def _parse_scoring_result(self, ai_response: str) -> ImageDescriptionScoreResponse:
        """Parse AI response and return structured result"""
        try:
            # Try to extract JSON from AI response
            response_text = ai_response.strip()
            
            # Find JSON content (look for first { to last })
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("No JSON found in AI response")
            
            json_str = response_text[start_idx:end_idx + 1]
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["is_correct", "score_percentage", "feedback", "similarity_level"]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure correct types
            is_correct = bool(result["is_correct"])
            score_percentage = float(result["score_percentage"])
            feedback = str(result["feedback"])
            similarity_level = str(result["similarity_level"])
            
            # Validate score range
            if not (0 <= score_percentage <= 100):
                score_percentage = max(0, min(100, score_percentage))
            
            # Validate similarity level
            if similarity_level not in ["high", "medium", "low"]:
                similarity_level = "medium"
            
            return ImageDescriptionScoreResponse(
                is_correct=is_correct,
                score_percentage=score_percentage,
                feedback=feedback,
                similarity_level=similarity_level
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            # Fallback: create response based on keywords
            return self._create_fallback_response(ai_response)
    
    def _create_fallback_response(self, ai_response: str) -> ImageDescriptionScoreResponse:
        """Create intelligent fallback response when JSON parsing fails"""
        response_lower = ai_response.lower()
        
        # More sophisticated keyword analysis
        positive_keywords = ["correct", "good", "accurate", "right", "excellent", "well", "properly"]
        partial_keywords = ["partially", "some", "partial", "medium", "somewhat", "fairly"]
        negative_keywords = ["incorrect", "wrong", "poor", "missing", "inaccurate", "failed"]
        
        positive_score = sum(1 for word in positive_keywords if word in response_lower)
        partial_score = sum(1 for word in partial_keywords if word in response_lower)
        negative_score = sum(1 for word in negative_keywords if word in response_lower)
        
        # Determine score based on keyword analysis (more lenient)
        if positive_score > negative_score:
            is_correct = True
            score_percentage = 85.0
            similarity_level = "high"
            feedback = "Good job! The description captures the main elements well."
        elif partial_score > 0 or positive_score >= negative_score:
            is_correct = True
            score_percentage = 75.0
            similarity_level = "medium"
            feedback = "Nice effort! The description shows good understanding."
        else:
            is_correct = False
            score_percentage = 50.0
            similarity_level = "low"
            feedback = "The description needs improvement to better match the expected content."
        
        return ImageDescriptionScoreResponse(
            is_correct=is_correct,
            score_percentage=score_percentage,
            feedback=feedback,
            similarity_level=similarity_level
        )
    
    def _create_rule_based_fallback(self, user_content: str, expected_results: str, language: str) -> ImageDescriptionScoreResponse:
        """Create deterministic rule-based scoring when AI fails completely"""
        
        # Normalize text for comparison
        user_words = set(user_content.lower().split())
        expected_words = set(expected_results.lower().split())
        
        # Calculate word overlap
        common_words = user_words.intersection(expected_words)
        overlap_ratio = len(common_words) / len(expected_words) if expected_words else 0
        
        # Remove common stop words from consideration
        stop_words = {"a", "an", "the", "is", "are", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
        meaningful_common = common_words - stop_words
        meaningful_expected = expected_words - stop_words
        meaningful_overlap = len(meaningful_common) / len(meaningful_expected) if meaningful_expected else 0
        
        # Determine score based on meaningful word overlap (more lenient)
        if meaningful_overlap >= 0.4:  # Lowered from 0.7
            is_correct = True
            score_percentage = 90.0
            similarity_level = "high"
            feedback = "Excellent! Good understanding of the image." if language == "en" else "Tuyệt vời! Bạn hiểu rất tốt về hình ảnh."
        elif meaningful_overlap >= 0.2:  # Lowered from 0.4
            is_correct = True
            score_percentage = 75.0
            similarity_level = "medium"
            feedback = "Good effort! You identified some key elements." if language == "en" else "Cố gắng tốt! Bạn đã nhận diện được một số yếu tố quan trọng."
        else:
            is_correct = False
            score_percentage = 55.0  # Increased from 30.0
            similarity_level = "low"
            feedback = "Keep trying! Focus on the main objects and actions." if language == "en" else "Hãy thử lại! Tập trung vào các đối tượng và hành động chính."
        
        return ImageDescriptionScoreResponse(
            is_correct=is_correct,
            score_percentage=score_percentage,
            feedback=feedback,
            similarity_level=similarity_level
        )