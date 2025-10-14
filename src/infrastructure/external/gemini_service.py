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
            # Prefer response.parts if available
            if not response or not hasattr(response, "parts") or not response.parts:
                raise GeminiAPIException("Empty response from Gemini API")
            # Join all text parts
            text = "\n".join([part.text for part in response.parts if hasattr(part, "text")])
            if not text.strip():
                raise GeminiAPIException("Empty response text from Gemini API")
            return text.strip()
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
    
    async def analyze_writing_vocabulary(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze vocabulary usage in writing"""
        
        prompt = f"""
        Analyze the vocabulary usage in this writing assignment:
        
        WRITING PROMPT: {writing_prompt}
        
        STUDENT WRITING: {writing_text}
        
        Evaluate the vocabulary based on:
        1. Vocabulary richness and variety (0-3 points)
        2. Advanced vocabulary usage (0-3 points) 
        3. Contextual appropriateness (0-2 points)
        4. Word choice accuracy (0-2 points)
        
        Provide your analysis in JSON format:
        {{
            "score": 8.5,
            "feedback": "Overall vocabulary usage analysis...",
            "strengths": ["Strength 1", "Strength 2", "Strength 3"],
            "weaknesses": ["Weakness 1", "Weakness 2", "Weakness 3"],
            "advanced_words_used": ["word1", "word2", "word3"],
            "vocabulary_level": "intermediate"
        }}
        
        Be specific and constructive in your feedback.
        """
        
        return await self.generate_response([{"role": "user", "parts": [prompt]}])
    
    async def analyze_writing_grammar(
        self,
        writing_text: str,
        language: str = "en"
    ) -> str:
        """Analyze grammar in writing"""
        
        prompt = f"""
        Check and analyze grammar in this writing:
        
        TEXT: {writing_text}
        
        Identify and evaluate:
        1. Sentence structure accuracy (0-3 points)
        2. Verb tense consistency (0-2 points)  
        3. Subject-verb agreement (0-2 points)
        4. Preposition and article usage (0-2 points)
        5. Punctuation accuracy (0-1 points)
        
        Provide detailed analysis in JSON format:
        {{
            "score": 7.5,
            "feedback": "Grammar analysis overview...",
            "strengths": ["Grammar strength 1", "Grammar strength 2"],
            "weaknesses": ["Grammar issue 1", "Grammar issue 2"],
            "error_count": {{
                "tense_errors": 2,
                "agreement_errors": 1,
                "preposition_errors": 3,
                "punctuation_errors": 2
            }},
            "major_errors": [
                {{
                    "error_text": "I have went",
                    "corrected_text": "I have gone",
                    "explanation": "Past participle of 'go' is 'gone'",
                    "error_type": "verb_form"
                }}
            ]
        }}
        
        Focus on the most important grammar issues.
        """
        
        return await self.generate_response([{"role": "user", "parts": [prompt]}])
    
    async def analyze_writing_structure(
        self,
        writing_text: str,
        writing_prompt: str,
        language: str = "en"
    ) -> str:
        """Analyze structure and logic in writing"""
        
        prompt = f"""
        Evaluate the structure and logic of this writing:
        
        WRITING PROMPT: {writing_prompt}
        
        STUDENT WRITING: {writing_text}
        
        Assess:
        1. Overall coherence and flow (0-3 points)
        2. Paragraph organization (0-2 points)
        3. Logical progression of ideas (0-2 points)
        4. Relevance to prompt requirements (0-2 points)
        5. Introduction and conclusion effectiveness (0-1 points)
        
        Provide analysis in JSON format:
        {{
            "score": 8.0,
            "feedback": "Structure analysis overview...",
            "strengths": ["Structure strength 1", "Structure strength 2"],
            "weaknesses": ["Structure issue 1", "Structure issue 2"],
            "organization_score": 7.5,
            "coherence_score": 8.0,
            "prompt_adherence_score": 8.5,
            "missing_elements": ["conclusion", "topic sentences"],
            "suggestions": {{
                "introduction": "Suggestion for intro improvement",
                "body_paragraphs": "Suggestion for body improvement", 
                "conclusion": "Suggestion for conclusion improvement",
                "transitions": "Suggestion for better transitions"
            }}
        }}
        
        Be specific about structural improvements needed.
        """
        
        return await self.generate_response([{"role": "user", "parts": [prompt]}])
    
    async def generate_detailed_feedback(
        self,
        writing_text: str,
        writing_prompt: str,
        vocabulary_analysis: str,
        grammar_analysis: str,
        structure_analysis: str,
        language: str = "en"
    ) -> str:
        """Generate comprehensive detailed feedback"""
        
        prompt = f"""
        Generate comprehensive feedback for this writing based on the analysis:
        
        WRITING PROMPT: {writing_prompt}
        STUDENT WRITING: {writing_text}
        
        ANALYSIS RESULTS:
        Vocabulary Analysis: {vocabulary_analysis}
        Grammar Analysis: {grammar_analysis}
        Structure Analysis: {structure_analysis}
        
        Generate detailed feedback in JSON format:
        {{
            "prompt_adherence": {{
                "score": 8.5,
                "feedback": "How well the writing addresses the prompt...",
                "missed_requirements": ["requirement 1", "requirement 2"]
            }},
            "grammar_corrections": [
                {{
                    "error_text": "I have went to school",
                    "corrected_text": "I have gone to school",
                    "explanation": "Past participle of 'go' is 'gone', not 'went'",
                    "error_type": "verb_form",
                    "rule_reference": "Present perfect tense formation"
                }}
            ],
            "vocabulary_enhancements": [
                {{
                    "original": "very good",
                    "suggestion": "exceptional",
                    "context_explanation": "More precise and academic",
                    "example_sentence": "The research showed exceptional results.",
                    "formality_level": "academic"
                }}
            ],
            "structure_suggestions": {{
                "introduction": "Consider adding a stronger thesis statement",
                "body_paragraphs": "Use clearer topic sentences",
                "conclusion": "Restate main points more effectively",
                "transitions": "Add linking words between paragraphs"
            }},
            "overall_strengths": ["strength 1", "strength 2", "strength 3"],
            "areas_for_improvement": ["area 1", "area 2", "area 3"],
            "next_steps": ["step 1", "step 2", "step 3"],
            "recommended_topics": ["grammar topic 1", "vocabulary topic 2"],
            "difficulty_level": "intermediate"
        }}
        
        Provide actionable, specific feedback that helps the student improve.
        """
        
        return await self.generate_response([{"role": "user", "parts": [prompt]}])