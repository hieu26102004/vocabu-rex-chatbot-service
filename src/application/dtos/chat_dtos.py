"""Data Transfer Objects for API requests and responses"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    """Request model for sending a chat message"""
    message: str = Field(..., min_length=1, max_length=1000, description="Chat message content")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    user_id: Optional[str] = Field(None, description="User ID for conversation tracking")
    role: Optional[str] = Field("vocabulary_expert", description="AI role: grammar_tutor, speaking_partner, corrector_assistant, vocabulary_expert, app_navigator")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class ChatMessageResponse(BaseModel):
    """Response model for chat message"""
    message_id: str
    conversation_id: str
    role: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    quick_replies: Optional[List[str]] = Field(None, description="AI-generated quick reply options for the user")
    progress: Optional[int] = Field(None, description="Roadmap creation progress percentage 0-100")
    step: Optional[str] = Field(None, description="Current step in roadmap creation flow")


class StartConversationRequest(BaseModel):
    """Request model for starting a new conversation"""
    user_id: Optional[str] = Field(None, description="User ID")
    initial_message: Optional[str] = Field(None, description="Optional initial message")
    role: Optional[str] = Field("vocabulary_expert", description="AI role: grammar_tutor, speaking_partner, corrector_assistant, vocabulary_expert, app_navigator")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Initial context")


class ConversationResponse(BaseModel):
    """Response model for conversation details"""
    id: str
    title: str
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history"""
    conversation: ConversationResponse
    messages: List[ChatMessageResponse]


class DeepLinkRequest(BaseModel):
    """Request model for deep link processing"""
    scheme: str = Field(..., description="App scheme (e.g., vocaburex)")
    host: str = Field(..., description="Deep link host")
    path: Optional[str] = Field(None, description="Deep link path")
    query_params: Optional[Dict[str, str]] = Field(default_factory=dict, description="Query parameters")
    user_id: Optional[str] = Field(None, description="User ID")


class VocabularyContextRequest(BaseModel):
    """Request model for vocabulary-specific chat context"""
    word: str = Field(..., description="Vocabulary word")
    definition: Optional[str] = Field(None, description="Word definition")
    example_sentence: Optional[str] = Field(None, description="Example sentence")
    difficulty_level: Optional[str] = Field(None, description="Difficulty level")
    user_question: str = Field(..., description="User's question about the word")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    gemini_api_status: str


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    message: str
    timestamp: datetime
    request_id: Optional[str] = None