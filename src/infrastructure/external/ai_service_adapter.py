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
    
    async def generate_response_with_system_prompt(
        self,
        message_history: List[Dict[str, Any]],
        system_prompt: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response with specific system prompt"""
        return await self.gemini_service.generate_response_with_system_prompt(
            message_history, system_prompt, context
        )

    async def generate_response_with_audio(
        self,
        message_history: List[Dict[str, Any]],
        system_prompt: str,
        audio_base64: str,
        audio_format: str = "audio/wav",
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response with audio input"""
        return await self.gemini_service.generate_response_with_audio(
            message_history, system_prompt, audio_base64, audio_format, context
        )
    
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for conversation based on first message"""
        # Use first few words of the message or generate using AI
        words = first_message.split()[:5]
        if len(words) < 5:
            return " ".join(words)
        return " ".join(words) + "..."
    
    async def analyze_writing_vocabulary(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze vocabulary usage in writing"""
        return await self.gemini_service.analyze_writing_vocabulary(
            writing_text, writing_prompt, language
        )
    
    async def analyze_writing_grammar(
        self,
        writing_text: str,
        language: str = "en"
    ) -> str:
        """Analyze grammar in writing"""
        return await self.gemini_service.analyze_writing_grammar(writing_text, language)
    
    async def analyze_writing_structure(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze structure and logic in writing"""
        return await self.gemini_service.analyze_writing_structure(
            writing_text, writing_prompt, language
        )
    
    async def generate_detailed_feedback(
        self,
        writing_text: str,
        writing_prompt: str,
        vocabulary_analysis: str,
        grammar_analysis: str,
        structure_analysis: str,
        language: str = "en"
    ) -> str:
        """Generate comprehensive detailed feedback"""
        return await self.gemini_service.generate_detailed_feedback(
            writing_text, writing_prompt, vocabulary_analysis, 
            grammar_analysis, structure_analysis, language
        )