"""Configuration settings for VocabuRex Chatbot Service"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Gemini AI Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    
    # Service Configuration  
    service_name: str = "vocabu-rex-chatbot-service"
    service_version: str = "1.0.0"
    service_host: str = "0.0.0.0"
    service_port: int = 3006
    
    # CORS Configuration
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"
    allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
    allowed_headers: str = "*"
    
    # Deep Link Configuration
    flutter_app_scheme: str = "vocaburex"
    flutter_app_host: str = "chatbot"
    
    # Educational Context
    max_conversation_history: int = 50
    default_learning_level: str = "intermediate"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # External Services
    user_service_url: str = "http://localhost:3002"
    learning_service_url: str = "http://localhost:3003"
    speech_service_url: str = "http://localhost:3005"
    
    # MongoDB Configuration
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "vocabu_rex_chatbot"
    
    # Voice Service Configuration (ngrok URLs for local GPU laptops)
    voice_tts_url: str = ""  # ngrok URL for Laptop 1 (TTS)
    voice_stt_url: str = ""  # ngrok URL for Laptop 2 (STT)
    voice_enabled: bool = False  # Toggle voice features
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()