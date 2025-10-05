"""Repository interfaces for conversation management"""
from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.conversation import Conversation
from ..entities.message import Message


class ConversationRepository(ABC):
    """Abstract repository for conversation management"""
    
    @abstractmethod
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        pass
    
    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        pass
    
    @abstractmethod
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update existing conversation"""
        pass
    
    @abstractmethod
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        pass
    
    @abstractmethod
    async def get_conversations_by_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        pass
    
    @abstractmethod
    async def add_message_to_conversation(self, conversation_id: str, message: Message) -> bool:
        """Add message to conversation"""
        pass


class MessageRepository(ABC):
    """Abstract repository for message management"""
    
    @abstractmethod
    async def create_message(self, message: Message) -> Message:
        """Create a new message"""
        pass
    
    @abstractmethod
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        pass
    
    @abstractmethod
    async def get_messages_by_conversation(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a conversation"""
        pass
    
    @abstractmethod
    async def delete_message(self, message_id: str) -> bool:
        """Delete message"""
        pass