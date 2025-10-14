"""Conversation entity for managing chat sessions"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .message import Message


@dataclass
class Conversation:
    """Conversation entity representing a chat session"""
    
    id: str
    user_id: Optional[str] = None
    title: str = "New Conversation"
    messages: List[Message] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = None
    updated_at: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        # Update title based on first user message (regardless of position)
        if message.role.value == "user" and self.title == "New Conversation":
            self.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages limited by count"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def get_message_history_for_ai(self, limit: int = 20) -> List[Dict[str, str]]:
        """Get message history formatted for AI model"""
        recent_messages = self.get_recent_messages(limit)
        return [
            {
                "role": msg.role.value,
                "parts": [msg.content]
            }
            for msg in recent_messages
            if msg.role.value in ["user", "model"]  # Gemini uses "model" instead of "assistant"
        ]
    
    def update_context(self, key: str, value: Any) -> None:
        """Update conversation context"""
        self.context[key] = value
        self.updated_at = datetime.utcnow()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get value from conversation context"""
        return self.context.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """Create conversation from dictionary"""
        messages = [Message.from_dict(msg_data) for msg_data in data.get("messages", [])]
        
        return cls(
            id=data["id"],
            user_id=data.get("user_id"),
            title=data.get("title", "New Conversation"),
            messages=messages,
            context=data.get("context", {}),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            is_active=data.get("is_active", True)
        )