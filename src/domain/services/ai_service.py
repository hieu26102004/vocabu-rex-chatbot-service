"""AI Service interface for chat domain"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator


class AIService(ABC):
    """Abstract interface for AI service operations"""
    
    @abstractmethod
    async def generate_response(
        self, 
        message_history: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response based on message history and context"""
        pass
    
    @abstractmethod
    async def generate_response_with_system_prompt(
        self,
        message_history: List[Dict[str, Any]],
        system_prompt: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response with specific system prompt"""
        pass
    
    @abstractmethod
    async def generate_response_with_system_prompt_stream(
        self,
        message_history: List[Dict[str, Any]],
        system_prompt: str,
        context: Dict[str, Any] = None
    ) -> AsyncGenerator[str, None]:
        """Stream AI response chunks with specific system prompt"""
        pass
        # Need yield to make it a proper async generator
        yield  # pragma: no cover
    
    @abstractmethod
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for conversation based on first message"""
        pass
    
    @abstractmethod
    async def analyze_writing_vocabulary(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze vocabulary usage in writing"""
        pass
    
    @abstractmethod
    async def analyze_writing_grammar(
        self,
        writing_text: str,
        language: str = "en"
    ) -> str:
        """Analyze grammar in writing"""
        pass
    
    @abstractmethod
    async def analyze_writing_structure(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze structure and logic in writing"""
        pass
    
    @abstractmethod
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
        pass