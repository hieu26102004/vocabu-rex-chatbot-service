import httpx
import logging
from typing import Optional
from ...shared.config import settings

logger = logging.getLogger(__name__)

class GoogleTTSService:
    """Service to synthesize speech using Google Cloud TTS API"""
    
    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        
    async def synthesize(self, text: str, language_code: str = "en-US", voice_name: str = "en-US-Journey-F") -> Optional[str]:
        """
        Synthesize text to speech using Google Cloud TTS.
        Returns base64 encoded MP3 audio or None if failed.
        """
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": language_code,
                "name": voice_name
            },
            "audioConfig": {
                "audioEncoding": "MP3"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.url, json=payload, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("audioContent")  # This is already base64 encoded
                else:
                    logger.error(f"Google TTS API Error: {response.status_code} - {response.text}")
                    return None
        except Exception as e:
            logger.error(f"Google TTS request failed: {str(e)}")
            return None
