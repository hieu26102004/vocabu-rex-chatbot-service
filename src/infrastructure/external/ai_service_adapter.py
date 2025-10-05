"""Gemini AI Service implementation"""
from typing import List, Dict, Any
from ...domain.services.ai_service import AIService
from .gemini_service import GeminiAIService as GeminiImplementation


class GeminiAIServiceAdapter(AIService):
    """Adapter for Gemini AI service to implement domain interface"""
    
    def __init__(self):
        self.gemini_service = GeminiImplementation()
    
    async def generate_response(
        self, 
        message_history: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response based on message history and context"""
        return await self.gemini_service.generate_response(message_history, context)
    
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for conversation based on first message"""
        # Use first few words of the message or generate using AI
        words = first_message.split()[:5]
        if len(words) < 5:
            return " ".join(words)
        return " ".join(words) + "..."