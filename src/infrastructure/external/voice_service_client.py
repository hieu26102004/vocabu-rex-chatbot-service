"""Voice Service Client - Calls TTS/STT services running on local laptops via ngrok"""
import httpx
import logging
import base64
from typing import AsyncGenerator, Optional

from ...shared.config import settings

logger = logging.getLogger(__name__)


class VoiceServiceClient:
    """HTTP client for Voice Services (TTS on Laptop 1, STT on Laptop 2) exposed via ngrok"""
    
    def __init__(self):
        self.tts_url = settings.voice_tts_url
        self.stt_url = settings.voice_stt_url
        self.client = httpx.AsyncClient(
            timeout=60.0,
            headers={"ngrok-skip-browser-warning": "true"}  # Skip ngrok warning page
        )
    
    @property
    def is_enabled(self) -> bool:
        """Check if voice services are configured"""
        return bool(settings.voice_enabled and self.tts_url and self.stt_url)
    
    async def text_to_speech(self, text: str, language: str = "en") -> bytes:
        """Convert text to speech audio bytes via TTS service (ngrok Laptop 1)"""
        try:
            response = await self.client.post(
                f"{self.tts_url}/tts",
                json={"text": text, "language": language}
            )
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.error(f"TTS service error: {str(e)}")
            raise VoiceServiceException(f"TTS service unavailable: {str(e)}")
    
    async def text_to_speech_stream(self, text: str, language: str = "en") -> AsyncGenerator[bytes, None]:
        """Stream text to speech audio chunks via TTS service"""
        try:
            async with self.client.stream(
                "POST",
                f"{self.tts_url}/tts/stream",
                json={"text": text, "language": language}
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    yield chunk
        except httpx.HTTPError as e:
            logger.error(f"TTS stream error: {str(e)}")
            raise VoiceServiceException(f"TTS stream unavailable: {str(e)}")
    
    async def speech_to_text(self, audio_bytes: bytes, language: str = "en") -> str:
        """Convert speech audio to text via STT service (ngrok Laptop 2)"""
        try:
            response = await self.client.post(
                f"{self.stt_url}/stt",
                files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
                data={"language": language}
            )
            response.raise_for_status()
            result = response.json()
            return result.get("text", "")
        except httpx.HTTPError as e:
            logger.error(f"STT service error: {str(e)}")
            raise VoiceServiceException(f"STT service unavailable: {str(e)}")
    
    async def assess_pronunciation(
        self, audio_bytes: bytes, reference_text: str, 
        language: str = "en", native_language: str = None
    ) -> dict:
        """
        Assess pronunciation via Voice Service (migrated from speech-service).
        Calls /pronunciation/assess on STT laptop.
        """
        try:
            data = {
                "reference_text": reference_text,
                "language": language,
            }
            if native_language:
                data["native_language"] = native_language
            
            response = await self.client.post(
                f"{self.stt_url}/pronunciation/assess",
                files={"audio": ("audio.wav", audio_bytes, "audio/wav")},
                data=data,
                timeout=120.0,  # Pronunciation assessment can take longer
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Pronunciation assessment error: {str(e)}")
            raise VoiceServiceException(f"Pronunciation service unavailable: {str(e)}")
    
    async def speech_transcribe(
        self, audio_bytes: bytes, reference_text: str = None,
        language: str = "english", model_size: str = "small"
    ) -> dict:
        """
        Full transcription with optional pronunciation analysis.
        Calls /speech/transcribe (speech-service compatible endpoint).
        """
        try:
            data = {
                "language": language,
                "model_size": model_size,
            }
            if reference_text:
                data["reference_text"] = reference_text
            
            response = await self.client.post(
                f"{self.stt_url}/speech/transcribe",
                files={"audio_file": ("audio.wav", audio_bytes, "audio/wav")},
                data=data,
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Speech transcribe error: {str(e)}")
            raise VoiceServiceException(f"Speech transcribe unavailable: {str(e)}")
    
    async def check_health(self) -> dict:
        """Check health of both TTS and STT services"""
        health = {"tts": "unavailable", "stt": "unavailable"}
        
        try:
            tts_resp = await self.client.get(f"{self.tts_url}/health", timeout=5.0)
            if tts_resp.status_code == 200:
                health["tts"] = "healthy"
        except Exception:
            pass
        
        try:
            stt_resp = await self.client.get(f"{self.stt_url}/health", timeout=5.0)
            if stt_resp.status_code == 200:
                health["stt"] = "healthy"
        except Exception:
            pass
        
        return health
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


class VoiceServiceException(Exception):
    """Exception for voice service errors"""
    pass
