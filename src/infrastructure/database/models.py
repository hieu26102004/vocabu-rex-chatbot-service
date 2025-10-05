"""MongoDB models using Beanie ODM"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from beanie import Document, Indexed
from pydantic import Field
from pymongo import IndexModel


class User(Document):
    """User model for storing user information"""
    user_id: str = Field(..., description="Unique user identifier")
    email: Optional[str] = Field(None, description="User email")
    username: Optional[str] = Field(None, description="Username")
    learning_level: str = Field("intermediate", description="User's learning level")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        indexes = [
            IndexModel([("user_id", 1)], unique=True),
            IndexModel([("email", 1)], unique=True, sparse=True),
        ]


class ChatConversation(Document):
    """Chat conversation model"""
    conversation_id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User who owns this conversation")
    title: Optional[str] = Field(None, description="Conversation title")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Whether conversation is active")
    
    class Settings:
        name = "chat_conversations"
        indexes = [
            IndexModel([("conversation_id", 1)], unique=True),
            IndexModel([("user_id", 1)]),
            IndexModel([("created_at", -1)]),
        ]


class ChatMessage(Document):
    """Chat message model"""
    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation this message belongs to")
    user_id: str = Field(..., description="User who sent/received this message")
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "chat_messages"
        indexes = [
            IndexModel([("conversation_id", 1)]),
            IndexModel([("user_id", 1)]),
            IndexModel([("timestamp", -1)]),
            IndexModel([("conversation_id", 1), ("timestamp", 1)]),
        ]