"""Voice Chat Controller - WebSocket endpoint for realtime voice conversation with AI"""
import base64
import json
import uuid
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Header

from ...application.dtos.chat_dtos import ChatMessageRequest
from ...application.use_cases.chat_use_case import ChatUseCase
from ...infrastructure.external.voice_service_client import VoiceServiceClient, VoiceServiceException
from ...infrastructure.repositories.user_repository import UserRepository
from ...infrastructure.repositories.conversation_repository import ConversationRepository
from ...infrastructure.external.ai_service_adapter import GeminiAIServiceAdapter
from ...shared.config import settings

logger = logging.getLogger(__name__)

voice_router = APIRouter(prefix="/voice", tags=["Voice Chat"])


def get_chat_use_case():
    user_repo = UserRepository()
    conversation_repo = ConversationRepository()
    ai_service = GeminiAIServiceAdapter()
    return ChatUseCase(user_repo, conversation_repo, ai_service)


@voice_router.get("/health")
async def voice_health():
    """Check voice service health (TTS + STT via ngrok)"""
    if not settings.voice_enabled:
        return {"status": "disabled", "message": "Voice features are disabled"}
    
    client = VoiceServiceClient()
    try:
        health = await client.check_health()
        return {
            "status": "healthy" if all(v == "healthy" for v in health.values()) else "degraded",
            "services": health,
            "tts_url": settings.voice_tts_url,
            "stt_url": settings.voice_stt_url,
        }
    finally:
        await client.close()


@voice_router.websocket("/ws/{conversation_id}")
async def voice_chat_websocket(websocket: WebSocket, conversation_id: str):
    """
    WebSocket endpoint for realtime voice chat with AI.
    
    Flow:
    1. Client sends audio chunks (base64 encoded PCM/WAV)
    2. Server accumulates audio, then sends to STT service (Laptop 2 via ngrok)
    3. STT returns transcript → sent back to client
    4. Transcript → Gemini AI (streaming) → text chunks sent to client
    5. Full AI response → TTS service (Laptop 1 via ngrok) → audio sent back to client
    
    Client → Server messages:
        {"type": "audio", "data": "<base64_pcm_16khz>"}
        {"type": "end_speech"}
        {"type": "config", "language": "en", "role": "speaking_partner"}
    
    Server → Client messages:
        {"type": "status", "status": "listening"}
        {"type": "status", "status": "processing"}
        {"type": "transcript", "text": "what user said"}
        {"type": "ai_text", "text": "AI response chunk"}
        {"type": "ai_audio", "data": "<base64_wav_audio>"}
        {"type": "done"}
        {"type": "error", "message": "error description"}
    """
    await websocket.accept()
    
    if not settings.voice_enabled:
        await websocket.send_json({"type": "error", "message": "Voice features are disabled"})
        await websocket.close()
        return
    
    voice_client = VoiceServiceClient()
    chat_use_case = get_chat_use_case()
    audio_buffer = bytearray()
    language = "en"
    role = "speaking_partner"
    
    logger.info(f"Voice chat WebSocket connected for conversation: {conversation_id}")
    
    try:
        # Send initial status
        await websocket.send_json({"type": "status", "status": "connected"})
        
        while True:
            try:
                raw_data = await websocket.receive_text()
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue
            
            msg_type = data.get("type", "")
            
            if msg_type == "config":
                # Update session config
                language = data.get("language", language)
                role = data.get("role", role)
                await websocket.send_json({
                    "type": "status", 
                    "status": "configured",
                    "language": language,
                    "role": role
                })
            
            elif msg_type == "audio":
                # Accumulate audio chunks
                audio_data = data.get("data", "")
                if audio_data:
                    try:
                        decoded = base64.b64decode(audio_data)
                        audio_buffer.extend(decoded)
                    except Exception as e:
                        await websocket.send_json({"type": "error", "message": f"Invalid audio data: {str(e)}"})
                
            elif msg_type == "end_speech":
                if not audio_buffer:
                    await websocket.send_json({"type": "error", "message": "No audio data received"})
                    continue
                
                await websocket.send_json({"type": "status", "status": "processing"})
                
                try:
                    # Step 1: STT - Convert audio to text (via ngrok Laptop 2)
                    transcript = await voice_client.speech_to_text(
                        bytes(audio_buffer), 
                        language=language
                    )
                    audio_buffer.clear()
                    
                    if not transcript.strip():
                        await websocket.send_json({
                            "type": "error", 
                            "message": "Could not understand audio. Please try again."
                        })
                        await websocket.send_json({"type": "status", "status": "listening"})
                        continue
                    
                    # Send transcript to client
                    await websocket.send_json({
                        "type": "transcript", 
                        "text": transcript
                    })
                    
                    # Step 2: AI Response - Stream from Gemini
                    await websocket.send_json({"type": "status", "status": "thinking"})
                    
                    request = ChatMessageRequest(
                        message=transcript,
                        conversation_id=conversation_id,
                        user_id=data.get("user_id"),
                        role=role,
                        context={"voice_chat": True, "language": language}
                    )
                    
                    full_ai_response = ""
                    async for chunk in chat_use_case.send_message_stream(request):
                        full_ai_response += chunk
                        await websocket.send_json({
                            "type": "ai_text", 
                            "text": chunk
                        })
                    
                    # Step 3: TTS - Convert AI response to audio (via ngrok Laptop 1)
                    await websocket.send_json({"type": "status", "status": "speaking"})
                    
                    try:
                        audio_bytes = await voice_client.text_to_speech(
                            full_ai_response, 
                            language=language
                        )
                        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                        await websocket.send_json({
                            "type": "ai_audio",
                            "data": audio_b64
                        })
                    except VoiceServiceException as e:
                        logger.warning(f"TTS failed, sending text only: {str(e)}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "TTS unavailable, showing text only"
                        })
                    
                    # Signal completion
                    await websocket.send_json({"type": "done"})
                    await websocket.send_json({"type": "status", "status": "listening"})
                    
                except VoiceServiceException as e:
                    logger.error(f"Voice service error: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Voice service error: {str(e)}"
                    })
                    await websocket.send_json({"type": "status", "status": "listening"})
                    audio_buffer.clear()
                    
                except Exception as e:
                    logger.error(f"Voice chat processing error: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "An error occurred during processing"
                    })
                    await websocket.send_json({"type": "status", "status": "listening"})
                    audio_buffer.clear()
            
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"Voice chat WebSocket disconnected for conversation: {conversation_id}")
    except Exception as e:
        logger.error(f"Voice chat WebSocket error: {str(e)}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        await voice_client.close()
