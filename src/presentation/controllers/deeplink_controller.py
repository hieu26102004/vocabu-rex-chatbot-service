"""Deep link controller for Flutter app integration"""
from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import logging

from ...application.dtos.chat_dtos import (
    DeepLinkRequest,
    VocabularyContextRequest,
    ChatMessageRequest,
    ChatMessageResponse
)
from ...application.use_cases.chat_use_case import ChatUseCase
from ...infrastructure.database.repositories import MongoUserRepository, MongoConversationRepository
from ...infrastructure.external.ai_service_adapter import GeminiAIServiceAdapter

logger = logging.getLogger(__name__)

# Router for deep link endpoints
deeplink_router = APIRouter(prefix="/deeplink", tags=["Deep Links"])

# Dependencies - In production, use proper dependency injection
user_repo = MongoUserRepository()
conversation_repo = MongoConversationRepository()
ai_service = GeminiAIServiceAdapter()
chat_use_case = ChatUseCase(user_repo, conversation_repo, ai_service)


@deeplink_router.post("/vocabulary", response_model=ChatMessageResponse)
async def handle_vocabulary_deeplink(request: VocabularyContextRequest):
    """Handle deep link for vocabulary word assistance"""
    try:
        logger.info(f"Processing vocabulary deep link for word: {request.word}")
        
        # Build context-aware message
        vocabulary_message = f"I need help with the word '{request.word}'"
        
        # Add definition and example if provided
        if request.definition:
            vocabulary_message += f". The definition I found is: {request.definition}"
        if request.example_sentence:
            vocabulary_message += f". Here's an example: {request.example_sentence}"
        
        # Add user's specific question
        vocabulary_message += f". {request.user_question}"
        
        # Create chat request with vocabulary context
        chat_request = ChatMessageRequest(
            message=vocabulary_message,
            context={
                "current_word": request.word,
                "definition": request.definition,
                "example_sentence": request.example_sentence,
                "learning_level": request.difficulty_level or "intermediate",
                "topic": "vocabulary_assistance",
                "source": "deep_link"
            }
        )
        
        # Process through chat use case
        response = await chat_use_case.send_message(chat_request)
        return response
        
    except Exception as e:
        logger.error(f"Error processing vocabulary deep link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process vocabulary request: {str(e)}"
        )


@deeplink_router.post("/process", response_model=Dict[str, Any])
async def process_deeplink(request: DeepLinkRequest):
    """Process general deep link from Flutter app"""
    try:
        logger.info(f"Processing deep link: {request.scheme}://{request.host}{request.path or ''}")
        
        # Parse deep link and determine action
        action = _parse_deeplink_action(request)
        
        if action["type"] == "vocabulary":
            # Redirect to vocabulary handler
            vocab_request = VocabularyContextRequest(
                word=action["word"],
                definition=action.get("definition"),
                example_sentence=action.get("example"),
                difficulty_level=action.get("level"),
                user_question=action.get("question", f"Can you help me understand the word '{action['word']}'?")
            )
            
            response = await handle_vocabulary_deeplink(vocab_request)
            return {
                "type": "vocabulary_response",
                "conversation_id": response.conversation_id,
                "response": response
            }
        
        elif action["type"] == "chat":
            # Start general chat
            chat_request = ChatMessageRequest(
                message=action.get("message", "Hello! I need help with vocabulary learning."),
                user_id=request.user_id,
                context={
                    "source": "deep_link",
                    "learning_level": action.get("level", "intermediate")
                }
            )
            
            response = await chat_use_case.send_message(chat_request)
            return {
                "type": "chat_response",
                "conversation_id": response.conversation_id,
                "response": response
            }
        
        else:
            return {
                "type": "welcome",
                "message": "Welcome to VocabuRex! How can I help you learn vocabulary today?",
                "suggestions": [
                    "Ask about a specific word",
                    "Practice pronunciation",
                    "Learn word meanings",
                    "Get example sentences"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error processing deep link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process deep link: {str(e)}"
        )


def _parse_deeplink_action(request: DeepLinkRequest) -> Dict[str, Any]:
    """Parse deep link to determine action"""
    
    # Example deep link patterns:
    # vocaburex://chatbot/vocabulary?word=hello&question=pronunciation
    # vocaburex://chatbot/chat?message=help&level=beginner
    # vocaburex://chatbot/word?name=beautiful&def=attractive
    
    action = {"type": "welcome"}
    
    if request.host == "chatbot":
        if request.path == "/vocabulary" or request.path == "/word":
            action["type"] = "vocabulary"
            action["word"] = request.query_params.get("word") or request.query_params.get("name", "")
            action["definition"] = request.query_params.get("definition") or request.query_params.get("def")
            action["example"] = request.query_params.get("example")
            action["level"] = request.query_params.get("level")
            action["question"] = request.query_params.get("question")
            
        elif request.path == "/chat":
            action["type"] = "chat"
            action["message"] = request.query_params.get("message")
            action["level"] = request.query_params.get("level")
    
    return action