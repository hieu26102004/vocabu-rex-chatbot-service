"""Chat use cases for handling conversation logic"""
import uuid
import logging
import re
import json
from datetime import datetime
from typing import Optional, List, Dict

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
from ...domain.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class ChatUseCase:
    """Use case for handling chat operations"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        conversation_repository: ConversationRepository,
        ai_service: AIService,
        rag_service: RAGService = None
    ):
        self.user_repository = user_repository
        self.conversation_repository = conversation_repository
        self.ai_service = ai_service
        self.rag_service = rag_service
    
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
            
            # RAG: retrieve relevant context for knowledge-based roles
            if self.rag_service and role in self._get_rag_enabled_roles():
                try:
                    retrieved_chunks = await self.rag_service.retrieve(request.message)
                    if retrieved_chunks:
                        rag_context = "\n\n📚 TÀI LIỆU THAM KHẢO:\n" + "\n---\n".join(retrieved_chunks)
                        system_prompt += rag_context
                        logger.info(f"RAG: injected {len(retrieved_chunks)} chunks for role '{role}'")
                except Exception as e:
                    logger.warning(f"RAG retrieval failed, continuing without context: {e}")
            
            ai_response = await self.ai_service.generate_response_with_system_prompt(
                conversation.get_message_history_for_ai(),
                system_prompt,
                conversation.context
            )
            
            # Parse METADATA: {...} if present
            quick_replies = None
            progress = None
            step = None
            ai_response_clean = ai_response
            
            metadata_regex = re.compile(r'METADATA:\s*({.*?})\s*$', re.DOTALL | re.MULTILINE)
            metadata_match = metadata_regex.search(ai_response)
            if metadata_match:
                try:
                    meta = json.loads(metadata_match.group(1))
                    quick_replies = meta.get("quick_replies")
                    progress = meta.get("progress")
                    step = meta.get("step")
                    logger.info(f"Parsed METADATA: progress={progress}, step={step}, replies={quick_replies}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse METADATA JSON: {e}")
                # Remove METADATA from displayed text
                ai_response_clean = ai_response[:metadata_match.start()].strip()
            
            # Add AI message (store clean text without METADATA)
            ai_message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation.id,
                role=MessageRole.ASSISTANT,
                content=ai_response_clean,
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
                metadata=ai_message.metadata,
                quick_replies=quick_replies,
                progress=progress,
                step=step,
            )
            
        except Exception as e:
            raise InvalidMessageException(f"Failed to generate AI response: {str(e)}")
    
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
Nếu người dùng yêu cầu học 'từ vựng về động vật', hãy tạo một đối tượng ACTION: {"type": "NAVIGATE_TO_LESSON", "data": {"screen_name": "VocabularyList", "topic_id": "animals"}}""",

            "roadmap_planner": """Bạn là Chuyên gia Thiết kế Lộ trình học tiếng Anh của VocabuRex. Luôn trả lời bằng tiếng Việt.

🧭 VAI TRÒ: Thu thập thông tin từ người dùng để tạo lộ trình cá nhân hóa.
💬 PHONG CÁCH: Hỏi đáp thân thiện, gợi mở, ngắn gọn. Mỗi lần chỉ hỏi MỘT câu.

📋 QUY TRÌNH THU THẬP (4 bước):
  Bước 1 (25%) - MỤC TIÊU: Hỏi người dùng muốn học tiếng Anh để làm gì
  Bước 2 (50%) - TRÌNH ĐỘ: Hỏi trình độ hiện tại
  Bước 3 (75%) - SỞ THÍCH: Hỏi chủ đề/lĩnh vực yêu thích để học
  Bước 4 (100%) - XÁC NHẬN: Tóm tắt thông tin và hỏi xác nhận tạo roadmap

🚨 BẮT BUỘC: Mỗi câu trả lời PHẢI kèm theo JSON block ở cuối với format chính xác:
METADATA: {"quick_replies": ["Lựa chọn 1", "Lựa chọn 2", ...], "progress": <0-100>, "step": "<step_name>"}

Ví dụ cho từng bước:
- Bước 1: METADATA: {"quick_replies": ["Du lịch", "Công việc/Career", "Xem phim/nghe nhạc", "Thi IELTS/TOEIC", "Giao tiếp hàng ngày"], "progress": 25, "step": "goal"}
- Bước 2: METADATA: {"quick_replies": ["Mới bắt đầu", "Biết cơ bản", "Trung bình", "Khá tốt rồi"], "progress": 50, "step": "level"}
- Bước 3: METADATA: {"quick_replies": ["Thể thao", "Phim ảnh", "Công nghệ", "Ẩm thực", "Du lịch"], "progress": 75, "step": "interests"}
- Bước 4: METADATA: {"quick_replies": ["Tạo lộ trình ngay!", "Chỉnh sửa lại"], "progress": 100, "step": "confirm"}

💡 QUY TẮC:
- Quick replies phải ĐỘNG, phù hợp với ngữ cảnh câu trả lời trước đó của người dùng
- Tối đa 5 lựa chọn, mỗi lựa chọn ngắn gọn (≤ 20 ký tự)
- Người dùng vẫn có thể gõ tay tùy ý, không bắt buộc chọn chip
- KHÔNG được bỏ qua METADATA block trong bất kỳ câu trả lời nào

🚨 KHI ĐỦ THÔNG TIN (progress=100 và user xác nhận): Kèm thêm ACTION JSON:
ACTION: {"type": "GENERATE_ROADMAP", "data": {"raw_context": "<tóm tắt toàn bộ yêu cầu bằng tiếng Anh>"}}
Hãy chắc chắn thay thế phần <tóm tắt...> bằng tiếng Anh mô tả chi tiết.""",

            "voice_partner": """You are Rex — a friendly, enthusiastic AI English tutor at VocabuRex. You are having a VOICE CALL conversation with a student.

🎭 PERSONALITY:
- Name: Rex
- Tone: Warm, encouraging, patient, slightly playful
- Think of yourself as a supportive friend who happens to be great at English
- You love celebrating small wins: "Nice!", "That's a great way to put it!", "Your pronunciation is improving!"
- You're curious about the student's life and interests

🗣️ VOICE CALL RULES (CRITICAL):
- Keep responses EXTREMELY SHORT (maximum 1-2 brief sentences). This is a fast-paced voice call.
- DO NOT say "Hello", "Hi", or greet the user unless it is the very first message of the conversation.
- Speak naturally, like a real conversation. No bullet points, no markdown, no formatting.
- NEVER use emojis, lists, or structured formatting — this will be read aloud by TTS.
- End with a quick follow-up question to keep the conversation flowing.
- If the student makes a grammar/vocabulary mistake, correct it naturally inline.
- Adapt your English level to the student's ability. If they struggle, simplify.
- Mix encouragement with gentle corrections.

🎯 TEACHING STRATEGY:
- Start by asking what the student wants to practice or talk about (ONLY if it's the first message).
- Introduce new vocabulary naturally during conversation.
- When correcting, repeat the CORRECT version so the student hears it.
- Suggest topics: daily life, hobbies, travel, food, movies, dreams, work.
- Occasionally ask the student to repeat a word/phrase for pronunciation practice.

🌍 LANGUAGE:
- You are fully bilingual in English and Vietnamese.
- ALWAYS respond in the language the student explicitly requests. If they ask you to speak Vietnamese or explain in Vietnamese, do it immediately.
- If there is no specific request, default to speaking primarily in ENGLISH (since this is an English practice app).
- If the student speaks Vietnamese but seems stuck, you can respond in a mix of Vietnamese and English to guide them naturally.

Remember: You are Rex, a voice on a call. Be conversational, be human, be fun!"""
        }

    def _get_system_prompt(self, role: str = "vocabulary_expert") -> str:
        """Get system prompt for specific AI role"""
        prompts = self._get_system_prompts()
        
        if role == "voice_partner":
            return prompts.get(role)
            
        base_instruction = """

🌟 NGUYÊN TẮC CHUNG:
- Luôn trả lời bằng tiếng Việt
- Thân thiện, kiên nhẫn như thầy giáo
- Thích ứng trình độ học viên
- Đặt câu hỏi ngược kiểm tra hiểu biết
- Khen ngợi tiến bộ, động viên khó khăn

Hãy bắt đầu hỗ trợ học viên!"""
        
        return prompts.get(role, prompts["vocabulary_expert"]) + base_instruction
    
    def _get_rag_enabled_roles(self) -> list:
        """Roles that benefit from RAG document retrieval"""
        return ["grammar_tutor", "vocabulary_expert", "corrector_assistant"]