"""Real Gemini AI service implementation - NO MOCK DATA"""
import google.generativeai as genai
from typing import List, Dict, Any, Optional
import asyncio
import logging

from ...shared.config import settings
from ...core.exceptions import GeminiAPIException

logger = logging.getLogger(__name__)


class GeminiAIService:
    """Real Gemini AI service using Google's API"""
    
    def __init__(self):
        """Initialize Gemini AI service with real API"""
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            raise GeminiAPIException("Gemini API key not configured. Please set GEMINI_API_KEY in .env file")
        
        # Configure Gemini API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )
        
        logger.info(f"Initialized Gemini AI service with model: {settings.gemini_model}")
    
    async def generate_response(
        self, 
        message_history: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response using real Gemini API"""
        try:
            # Prepare context-aware prompt
            enhanced_prompt = self._build_context_aware_prompt(message_history, context)
            
            # Call Gemini API in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._generate_sync_response, 
                enhanced_prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise GeminiAPIException(f"Failed to generate response: {str(e)}")
    
    async def generate_response_with_system_prompt(
        self,
        message_history: List[Dict[str, Any]],
        system_prompt: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate AI response using specific system prompt"""
        try:
            # Build prompt with custom system instruction
            enhanced_prompt = self._build_prompt_with_system_instruction(
                message_history, system_prompt, context
            )
            
            # Call Gemini API in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self._generate_sync_response, 
                enhanced_prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            raise GeminiAPIException(f"Failed to generate response: {str(e)}")

    def _generate_sync_response(self, prompt: str) -> str:
        """Synchronous call to Gemini API"""
        try:
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise GeminiAPIException("Empty response from Gemini API")
            
            return response.text.strip()
            
        except Exception as e:
            raise GeminiAPIException(f"Gemini API call failed: {str(e)}")
    
    def _build_context_aware_prompt(
        self, 
        message_history: List[Dict[str, Any]], 
        context: Dict[str, Any] = None
    ) -> str:
        """Build context-aware prompt for vocabulary learning"""
        
        # Base system instruction for vocabulary learning
        system_instruction = """You are VocabuRex AI Assistant, a vocabulary learning tutor. Help users learn English vocabulary effectively.

Key Guidelines:
1. Provide clear, simple definitions
2. Give practical examples
3. Suggest memory techniques
4. Encourage active practice
5. Adapt to user's learning level
6. Be encouraging and supportive

Focus on making vocabulary learning engaging and memorable."""
        
        # Add vocabulary-specific context if available
        vocab_context = ""
        if context:
            if "current_word" in context:
                vocab_context += f"\nCurrent word being discussed: {context['current_word']}"
            if "learning_level" in context:
                vocab_context += f"\nUser's learning level: {context['learning_level']}"
            if "topic" in context:
                vocab_context += f"\nCurrent topic: {context['topic']}"
        
        # Build conversation history
        conversation = ""
        for msg in message_history[-10:]:  # Last 10 messages for context
            role = msg.get('role', '')
            content = msg.get('parts', [''])[0] if msg.get('parts') else msg.get('content', '')
            
            if role == 'user':
                conversation += f"\nUser: {content}"
            elif role in ['model', 'assistant']:
                conversation += f"\nAssistant: {content}"
        
        # Combine all parts
        full_prompt = f"""{system_instruction}
        
{vocab_context}

Conversation History:{conversation}

Please provide a helpful, educational response that supports vocabulary learning. Be concise but thorough."""
        
        return full_prompt
    
    def _build_prompt_with_system_instruction(
        self,
        message_history: List[Dict[str, Any]],
        system_instruction: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Build prompt with custom system instruction"""
        
        # Add context if available
        context_info = ""
        if context:
            if "current_word" in context:
                context_info += f"\nCurrent word being discussed: {context['current_word']}"
            if "learning_level" in context:
                context_info += f"\nUser's learning level: {context['learning_level']}"
            if "topic" in context:
                context_info += f"\nCurrent topic: {context['topic']}"
        
        # Build conversation history
        conversation = ""
        for msg in message_history[-10:]:  # Last 10 messages for context
            role = msg.get('role', '')
            content = msg.get('parts', [''])[0] if msg.get('parts') else msg.get('content', '')
            
            if role == 'user':
                conversation += f"\nUser: {content}"
            elif role in ['model', 'assistant']:
                conversation += f"\nAssistant: {content}"
        
        # Combine all parts with custom system instruction
        full_prompt = f"""{system_instruction}
        
{context_info}

Conversation History:{conversation}

Please provide a helpful response based on your role and the conversation context."""
        
        return full_prompt
    
    async def check_api_health(self) -> bool:
        """Check if Gemini API is accessible"""
        try:
            # Simple test call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._test_api_connection
            )
            return response
        except Exception as e:
            logger.error(f"Gemini API health check failed: {str(e)}")
            return False
    
    def _test_api_connection(self) -> bool:
        """Test API connection with simple call"""
        try:
            response = self.model.generate_content("Hello")
            return bool(response and response.text)
        except Exception:
            return False