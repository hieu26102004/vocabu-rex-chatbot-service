"""Repository interfaces for chat domain"""
from abc import ABC, abstractmethod
from typing import Optional, List
from ...domain.entities.conversation import Conversation
from ...domain.entities.user import User


class UserRepository(ABC):
    """Abstract repository for user operations"""
    
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create new user"""
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update existing user"""
        pass


class ConversationRepository(ABC):
    """Abstract repository for conversation operations"""
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        pass
    
    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create new conversation"""
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update existing conversation"""
        pass
    
    @abstractmethod
    async def get_user_conversations(self, user_id: str, limit: int = 10) -> List[Conversation]:
        """Get user's conversations"""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        pass