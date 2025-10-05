"""Chat controllers for handling API endpoints"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
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
from ...infrastructure.external.gemini_service import GeminiAIService
from ...infrastructure.repositories.memory_conversation_repository import InMemoryConversationRepository
from ...shared.config import settings
from ...core.exceptions import (
    ConversationNotFoundException,
    InvalidMessageException,
    GeminiAPIException
)

logger = logging.getLogger(__name__)

# Router for chat endpoints
chat_router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

# Dependencies - In production, use proper dependency injection
conversation_repo = InMemoryConversationRepository()
ai_service = GeminiAIService()
chat_use_case = ChatUseCase(conversation_repo, ai_service)


@chat_router.post("/start", response_model=ConversationResponse)
async def start_conversation(request: StartConversationRequest):
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
async def send_message(request: ChatMessageRequest):
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
async def get_conversation_history(conversation_id: str):
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
async def health_check():
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