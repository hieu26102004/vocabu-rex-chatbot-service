from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Body, Header
from fastapi.responses import JSONResponse
import logging

from ...application.dtos.chat_dtos import (
    ChatMessageRequest,
    ChatMessageResponse,
    StartConversationRequest,
    ConversationResponse,
    ConversationHistoryResponse,
    HealthResponse,
    ErrorResponse
)
from ...application.use_cases.chat_use_case import ChatUseCase
from ...infrastructure.repositories.user_repository import UserRepository
from ...infrastructure.repositories.conversation_repository import ConversationRepository
from ...infrastructure.external.ai_service_adapter import GeminiAIServiceAdapter
from ...shared.config import settings
from ...core.exceptions import (
    ConversationNotFoundException,
    InvalidMessageException,
    GeminiAPIException
)

logger = logging.getLogger(__name__)

# Router for chat endpoints
chat_router = APIRouter(prefix="/chat", tags=["Chat"])

# Dependency provider for ChatUseCase
def get_chat_use_case():
    user_repo = UserRepository()
    conversation_repo = ConversationRepository()
    ai_service = GeminiAIServiceAdapter()
    return ChatUseCase(user_repo, conversation_repo, ai_service)

# Dependency provider for ai_service (for health_check)
def get_ai_service():
    return GeminiAIServiceAdapter()
# Endpoint: Lấy danh sách conversation của user
@chat_router.get("/user/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    user_id: str = Header(..., alias="x-user-id"),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    try:
        conversations = await chat_use_case.conversation_repository.get_user_conversations(user_id)
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                user_id=conv.user_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=len(conv.messages) if hasattr(conv, "messages") else 0,
                is_active=conv.is_active
            ) for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user conversations: {str(e)}"
        )

# Endpoint: Lấy chi tiết một conversation
@chat_router.get("/conversation/{conversation_id}", response_model=ConversationResponse)
async def get_conversation_detail(
    conversation_id: str,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    try:
        conv = await chat_use_case.conversation_repository.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return ConversationResponse(
            id=conv.id,
            title=conv.title,
            user_id=conv.user_id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if hasattr(conv, "messages") else 0,
            is_active=conv.is_active
        )
    except Exception as e:
        logger.error(f"Error getting conversation detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation detail: {str(e)}"
        )

# Endpoint: Xóa conversation
@chat_router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    try:
        result = await chat_use_case.conversation_repository.delete_conversation(conversation_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or already deleted")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )

# Endpoint: Cập nhật conversation (chỉ cập nhật title/context/is_active)
@chat_router.put("/conversation/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: dict = Body(...),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    try:
        conv = await chat_use_case.conversation_repository.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        # Chỉ cập nhật các trường cho phép
        if "title" in update_data:
            conv.title = update_data["title"]
        if "context" in update_data:
            conv.context = update_data["context"]
        if "is_active" in update_data:
            conv.is_active = update_data["is_active"]
        updated_conv = await chat_use_case.conversation_repository.update_conversation(conv)
        return ConversationResponse(
            id=updated_conv.id,
            title=updated_conv.title,
            user_id=updated_conv.user_id,
            created_at=updated_conv.created_at,
            updated_at=updated_conv.updated_at,
            message_count=len(updated_conv.messages) if hasattr(updated_conv, "messages") else 0,
            is_active=updated_conv.is_active
        )
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )

@chat_router.post("/start", response_model=ConversationResponse)
async def start_conversation(
    request: StartConversationRequest,
    user_id: str = Header(..., alias="x-user-id"),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    request.user_id = user_id
    """Start a new conversation"""
    try:
        logger.info(f"Starting new conversation for user: {request.user_id}")
        response = await chat_use_case.start_conversation(request)
        return response
    except Exception as e:
        logger.error(f"Error starting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start conversation: {str(e)}"
        )


@chat_router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user_id: str = Header(..., alias="x-user-id"),
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    request.user_id = user_id
    """Send a message and get AI response"""
    try:
        logger.info(f"Processing message for conversation: {request.conversation_id}")
        response = await chat_use_case.send_message(request)
        return response
    except ConversationNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except InvalidMessageException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except GeminiAPIException as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@chat_router.get("/conversation/{conversation_id}/history", response_model=ConversationHistoryResponse)
async def get_conversation_history(
    conversation_id: str,
    chat_use_case: ChatUseCase = Depends(get_chat_use_case)
):
    """Get conversation history"""
    try:
        logger.info(f"Getting history for conversation: {conversation_id}")
        response = await chat_use_case.get_conversation_history(conversation_id)
        return response
    except ConversationNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting conversation history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation history: {str(e)}"
        )


@chat_router.get("/health", response_model=HealthResponse)
async def health_check(ai_service: GeminiAIServiceAdapter = Depends(get_ai_service)):
    """Health check endpoint"""
    try:
        # Check Gemini API status
        gemini_status = "healthy" if await ai_service.check_api_health() else "unhealthy"
            
        return HealthResponse(
            status="healthy",
            service=settings.service_name,
            version=settings.service_version,
            timestamp=datetime.utcnow(),
            gemini_api_status=gemini_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "service": settings.service_name,
                "version": settings.service_version,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )