"""AI Service interface for chat domain"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


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
    async def generate_conversation_title(self, first_message: str) -> str:
        """Generate a title for conversation based on first message"""
        pass