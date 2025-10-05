"""In-memory conversation repository implementation"""
from typing import List, Optional, Dict
import logging

from ...domain.entities.conversation import Conversation
from ...domain.entities.message import Message
from ...domain.repositories.conversation_repository import ConversationRepository, MessageRepository

logger = logging.getLogger(__name__)


class InMemoryConversationRepository(ConversationRepository):
    """In-memory implementation of conversation repository"""
    
    def __init__(self):
        self._conversations: Dict[str, Conversation] = {}
        self._messages: Dict[str, Message] = {}
    
    async def create_conversation(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        self._conversations[conversation.id] = conversation
        logger.info(f"Created conversation {conversation.id}")
        return conversation
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        return self._conversations.get(conversation_id)
    
    async def update_conversation(self, conversation: Conversation) -> Conversation:
        """Update existing conversation"""
        if conversation.id in self._conversations:
            self._conversations[conversation.id] = conversation
            logger.info(f"Updated conversation {conversation.id}")
            return conversation
        raise ValueError(f"Conversation {conversation.id} not found")
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        if conversation_id in self._conversations:
            # Also delete associated messages
            conversation = self._conversations[conversation_id]
            for message in conversation.messages:
                self._messages.pop(message.id, None)
            
            del self._conversations[conversation_id]
            logger.info(f"Deleted conversation {conversation_id}")
            return True
        return False
    
    async def get_conversations_by_user(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        return [
            conv for conv in self._conversations.values()
            if conv.user_id == user_id
        ]
    
    async def add_message_to_conversation(self, conversation_id: str, message: Message) -> bool:
        """Add message to conversation"""
        conversation = self._conversations.get(conversation_id)
        if conversation:
            conversation.add_message(message)
            self._messages[message.id] = message
            logger.info(f"Added message {message.id} to conversation {conversation_id}")
            return True
        return False


class InMemoryMessageRepository(MessageRepository):
    """In-memory implementation of message repository"""
    
    def __init__(self):
        self._messages: Dict[str, Message] = {}
    
    async def create_message(self, message: Message) -> Message:
        """Create a new message"""
        self._messages[message.id] = message
        logger.info(f"Created message {message.id}")
        return message
    
    async def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return self._messages.get(message_id)
    
    async def get_messages_by_conversation(self, conversation_id: str, limit: int = 50) -> List[Message]:
        """Get messages for a conversation"""
        messages = [
            msg for msg in self._messages.values()
            if msg.conversation_id == conversation_id
        ]
        # Sort by timestamp and limit
        messages.sort(key=lambda x: x.timestamp)
        return messages[-limit:] if limit > 0 else messages
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete message"""
        if message_id in self._messages:
            del self._messages[message_id]
            logger.info(f"Deleted message {message_id}")
            return True
        return False