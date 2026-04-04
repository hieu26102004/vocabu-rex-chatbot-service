"""Chat use cases for handling conversation logic"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, AsyncGenerator

from ..dtos.chat_dtos import (
    ChatMessageRequest, 
    ChatMessageResponse, 
    StartConversationRequest,
    ConversationResponse,
    ConversationHistoryResponse
)

from ...domain.entities.conversation import Conversation
from ...domain.entities.message import Message, MessageRole, MessageType
from ...domain.entities.user import User
from ...domain.services.ai_service import AIService
from ...core.exceptions import ConversationNotFoundException, InvalidMessageException
from ...domain.repositories.user_repository import UserRepository
from ...domain.repositories.conversation_repository import ConversationRepository


class ChatUseCase:
    """Use case for handling chat operations"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        ai_service: AIService
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository
        self.ai_service = ai_service
    
    async def start_conversation(self, request: StartConversationRequest) -> ConversationResponse:
        """Start a new conversation"""
        conversation_id = str(uuid.uuid4())
        
        # Ensure user exists
        user = await self.user_repository.get_user_by_id(request.user_id)
        if not user:
            user = User(
                user_id=request.user_id,
                learning_level=request.context.get('learning_level', 'intermediate') if request.context else 'intermediate'
            )
            await self.user_repository.create_user(user)
        
        # Create new conversation
        conversation = Conversation(
            id=conversation_id,
            user_id=request.user_id,
            context=request.context or {}
        )
        
        # Add initial system message for vocabulary learning context
        role = request.context.get('role', 'vocabulary_expert') if request.context else 'vocabulary_expert'
        system_message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content=self._get_system_prompt(role),
            message_type=MessageType.TEXT
        )
        conversation.add_message(system_message)
        
        
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
            # Create new conversation with role
            context_with_role = request.context.copy() if request.context else {}
            context_with_role['role'] = request.role
            start_request = StartConversationRequest(
                user_id=request.user_id,
                role=request.role,
                context=context_with_role
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
        
        # Get AI response with role-specific system prompt
        try:
            # Extract role from request or conversation context
            role = request.role if hasattr(request, 'role') and request.role else conversation.context.get('role', 'general')
            system_prompt = self._get_system_prompt(role)
            
            ai_response = await self.ai_service.generate_response_with_system_prompt(
                conversation.get_message_history_for_ai(),
                system_prompt,
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
    
    async def send_message_stream(self, request: ChatMessageRequest) -> AsyncGenerator[str, None]:
        """Send a message and stream AI response chunks"""
        
        # Get or create conversation (same logic as send_message)
        if request.conversation_id:
            conversation = await self.conversation_repository.get_conversation(request.conversation_id)
            if not conversation:
                raise ConversationNotFoundException(f"Conversation {request.conversation_id} not found")
        else:
            context_with_role = request.context.copy() if request.context else {}
            context_with_role['role'] = request.role
            start_request = StartConversationRequest(
                user_id=request.user_id,
                role=request.role,
                context=context_with_role
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
        
        # Stream AI response
        try:
            role = request.role if hasattr(request, 'role') and request.role else conversation.context.get('role', 'general')
            system_prompt = self._get_system_prompt(role)
            
            full_response = ""
            async for chunk in self.ai_service.generate_response_with_system_prompt_stream(
                conversation.get_message_history_for_ai(),
                system_prompt,
                conversation.context
            ):
                full_response += chunk
                yield chunk
            
            # After streaming complete, save the full AI message
            ai_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=full_response,
                message_type=MessageType.TEXT
            )
            conversation.add_message(ai_message)
            await self.conversation_repository.update_conversation(conversation)
            
        except Exception as e:
            raise InvalidMessageException(f"Failed to stream AI response: {str(e)}")
    
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
    
    def _get_system_prompts(self) -> Dict[str, str]:
        """Get system prompts dictionary for different AI roles"""
        return {
            "grammar_tutor": """Bạn là Gia sư Ngữ pháp của VocabuRex. Luôn trả lời bằng tiếng Việt.

🎯 CHUYÊN MÔN: Giải thích ngữ pháp tiếng Anh chi tiết, phân tích cấu trúc câu, so sánh với tiếng Việt.
📝 PHONG CÁCH: Từ cơ bản đến phức tạp, 3-4 ví dụ minh họa, tạo bài tập kiểm tra.
🚨 QUAN TRỌNG: Bạn KHÔNG được tự ý tạo Deep Link. Hãy đặt trường 'action' trong JSON là NULL trừ khi người dùng HỎI CỤ THỂ về bài học.""",

            "speaking_partner": """Bạn là Đối tác Luyện nói của VocabuRex. Luôn trả lời bằng tiếng Việt.

🗣️ VAI TRÒ: Tạo hội thoại tự nhiên, mô phỏng tình huống thực tế, khuyến khích giao tiếp.
💬 PHONG CÁCH: Thân thiện, sửa lỗi nhẹ nhàng, tạo không khí thoải mái.
🚨 QUAN TRỌNG: Bạn KHÔNG được tự ý tạo Deep Link. Hãy đặt trường 'action' trong JSON là NULL trừ khi người dùng HỎI CỤ THỂ về bài học.""",

            "corrector_assistant": """Bạn là Trợ lý Sửa lỗi của VocabuRex. Luôn trả lời bằng tiếng Việt.

✏️ NHIỆM VỤ: Phát hiện lỗi ngữ pháp/từ vựng, đưa ra phiên bản sửa, giải thích lý do.
🔍 PHƯƠNG PHÁP: Phân tích tỉ mỉ, ưu tiên lỗi nghiêm trọng, gợi ý diễn đạt hay hơn.
🚨 QUAN TRỌNG: Bạn KHÔNG được tự ý tạo Deep Link. Hãy đặt trường 'action' trong JSON là NULL trừ khi người dùng HỎI CỤ THỂ về bài học.""",

            "vocabulary_expert": """Bạn là Chuyên gia Từ vựng của VocabuRex. Luôn trả lời bằng tiếng Việt.

📚 CHUYÊN MÔN: Giải thích từ vựng toàn diện, phân loại từ loại, hướng dẫn phát âm, từ đồng/trái nghĩa.
🎨 PHƯƠNG PHÁP: Tạo câu chuyện nhớ từ, 3-4 ví dụ thực tế, giải thích từ gốc.
🚨 QUAN TRỌNG: Bạn KHÔNG được tự ý tạo Deep Link. Hãy đặt trường 'action' trong JSON là NULL trừ khi người dùng HỎI CỤ THỂ về bài học.""",

            "app_navigator": """Bạn là Hướng dẫn Ứng dụng của VocabuRex. Luôn trả lời bằng tiếng Việt.

🧭 VAI TRÒ: Tư vấn học tập, gợi ý bài học phù hợp, tạo lộ trình cá nhân.
📱 CHUYÊN MÔN: BẠN PHẢI luôn trả lời bằng cấu trúc JSON đã được định nghĩa.
Nếu người dùng yêu cầu học 'từ vựng về động vật', hãy tạo một đối tượng ACTION: {"type": "NAVIGATE_TO_LESSON", "data": {"screen_name": "VocabularyList", "topic_id": "animals"}}"""
        }

    def _get_system_prompt(self, role: str = "vocabulary_expert") -> str:
        """Get system prompt for specific AI role"""
        prompts = self._get_system_prompts()
        base_instruction = """

🌟 NGUYÊN TẮC CHUNG:
- Luôn trả lời bằng tiếng Việt
- Thân thiện, kiên nhẫn như thầy giáo
- Thích ứng trình độ học viên
- Đặt câu hỏi ngược kiểm tra hiểu biết
- Khen ngợi tiến bộ, động viên khó khăn

Hãy bắt đầu hỗ trợ học viên!"""
        
        return prompts.get(role, prompts["vocabulary_expert"]) + base_instruction