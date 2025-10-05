"""Chat use cases for handling conversation logic"""
import uuid
from datetime import datetime
from typing import Optional

from ..dtos.chat_dtos import (
    ChatMessageRequest, 
    ChatMessageResponse, 
    StartConversationRequest,
    ConversationResponse,
    ConversationHistoryResponse
)
from ...domain.entities.conversation import Conversation
from ...domain.entities.message import Message, MessageRole, MessageType
from ...domain.repositories.conversation_repository import ConversationRepository
from ...core.exceptions import ConversationNotFoundException, InvalidMessageException


class ChatUseCase:
    """Use case for handling chat operations"""
    
    def __init__(
        self, 
        conversation_repository: ConversationRepository,
        ai_service,  # Will be injected from infrastructure layer
    ):
        self.conversation_repository = conversation_repository
        self.ai_service = ai_service
    
    async def start_conversation(self, request: StartConversationRequest) -> ConversationResponse:
        """Start a new conversation"""
        conversation_id = str(uuid.uuid4())
        
        conversation = Conversation(
            id=conversation_id,
            user_id=request.user_id,
            context=request.context or {}
        )
        
        # Add initial system message for vocabulary learning context
        system_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=self._get_system_prompt(),
            message_type=MessageType.TEXT
        )
        conversation.add_message(system_message)
        
        # Add initial user message if provided
        if request.initial_message:
            user_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=request.initial_message,
                message_type=MessageType.TEXT
            )
            conversation.add_message(user_message)
        
        # Save conversation
        saved_conversation = await self.conversation_repository.create_conversation(conversation)
        
        return ConversationResponse(
            id=saved_conversation.id,
            title=saved_conversation.title,
            user_id=saved_conversation.user_id,
            created_at=saved_conversation.created_at,
            updated_at=saved_conversation.updated_at,
            message_count=len(saved_conversation.messages),
            is_active=saved_conversation.is_active
        )
    
    async def send_message(self, request: ChatMessageRequest) -> ChatMessageResponse:
        """Send a message and get AI response"""
        
        # Get or create conversation
        if request.conversation_id:
            conversation = await self.conversation_repository.get_conversation(request.conversation_id)
            if not conversation:
                raise ConversationNotFoundException(f"Conversation {request.conversation_id} not found")
        else:
            # Create new conversation
            start_request = StartConversationRequest(
                user_id=request.user_id,
                context=request.context
            )
            conv_response = await self.start_conversation(start_request)
            conversation = await self.conversation_repository.get_conversation(conv_response.id)
        
        # Add user message
        user_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=request.message,
            message_type=MessageType.TEXT
        )
        conversation.add_message(user_message)
        
        # Get AI response
        try:
            ai_response = await self.ai_service.generate_response(
                conversation.get_message_history_for_ai(),
                conversation.context
            )
            
            # Add AI message
            ai_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=ai_response,
                message_type=MessageType.TEXT
            )
            conversation.add_message(ai_message)
            
            # Update conversation
            await self.conversation_repository.update_conversation(conversation)
            
            return ChatMessageResponse(
                message_id=ai_message.id,
                conversation_id=conversation.id,
                role=ai_message.role.value,
                content=ai_message.content,
                timestamp=ai_message.timestamp,
                metadata=ai_message.metadata
            )
            
        except Exception as e:
            raise InvalidMessageException(f"Failed to generate AI response: {str(e)}")
    
    async def get_conversation_history(self, conversation_id: str) -> ConversationHistoryResponse:
        """Get conversation history"""
        conversation = await self.conversation_repository.get_conversation(conversation_id)
        if not conversation:
            raise ConversationNotFoundException(f"Conversation {conversation_id} not found")
        
        messages = [
            ChatMessageResponse(
                message_id=msg.id,
                conversation_id=msg.conversation_id,
                role=msg.role.value,
                content=msg.content,
                timestamp=msg.timestamp,
                metadata=msg.metadata
            )
            for msg in conversation.messages
            if msg.role != MessageRole.SYSTEM  # Don't expose system messages
        ]
        
        conv_response = ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            user_id=conversation.user_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(messages),
            is_active=conversation.is_active
        )
        
        return ConversationHistoryResponse(
            conversation=conv_response,
            messages=messages
        )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for vocabulary learning assistant"""
        return """You are VocabuRex AI Assistant, a friendly and knowledgeable vocabulary learning tutor. Your mission is to help users improve their English vocabulary in an engaging and educational way.

Core Responsibilities:
1. Help users understand new vocabulary words with clear definitions and examples
2. Provide pronunciation guidance when requested
3. Create memorable contexts and associations for better word retention
4. Adapt explanations to the user's learning level
5. Encourage active usage through exercises and questions

Communication Style:
- Be encouraging and supportive
- Use simple language for explanations
- Provide practical examples from daily life
- Ask follow-up questions to reinforce learning
- Celebrate user progress and efforts

When users ask about vocabulary:
- Give clear, concise definitions
- Provide 2-3 example sentences
- Suggest related words or synonyms
- Share memory techniques or word origins when helpful
- Encourage the user to create their own example sentence

Always maintain a positive, educational tone and focus on making vocabulary learning enjoyable and effective."""