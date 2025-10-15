"""MongoDB implementation of ConversationRepository"""
from typing import Optional, List
from datetime import datetime
from ...domain.entities.conversation import Conversation as ConversationEntity
from ...domain.entities.message import Message
from ...domain.repositories.conversation_repository import ConversationRepository as ConversationRepositoryInterface
from ..database.models import ChatConversation, ChatMessage

class ConversationRepository(ConversationRepositoryInterface):
    async def create_conversation(self, conversation: ConversationEntity) -> ConversationEntity:
        conv_doc = ChatConversation(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context=conversation.context
        )
        await conv_doc.insert()
        for message in conversation.messages:
            msg_doc = ChatMessage(
                message_id=message.id,
                conversation_id=message.conversation_id,
                user_id=conversation.user_id,
                role=message.role.value.lower(),
                content=message.content,
                metadata=message.metadata,
                timestamp=message.timestamp
            )
            await msg_doc.insert()
        conversation.created_at = conv_doc.created_at
        conversation.updated_at = conv_doc.updated_at
        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationEntity]:
        conv_doc = await ChatConversation.find_one(ChatConversation.conversation_id == conversation_id)
        if not conv_doc:
            return None
        message_docs = await ChatMessage.find(
            ChatMessage.conversation_id == conversation_id
        ).sort(ChatMessage.timestamp).to_list()
        conversation = ConversationEntity(
            id=conv_doc.conversation_id,
            user_id=conv_doc.user_id,
            title=conv_doc.title,
            context=conv_doc.context,
            created_at=conv_doc.created_at,
            updated_at=conv_doc.updated_at,
            is_active=conv_doc.is_active
        )
        for msg_doc in message_docs:
            from ...domain.entities.message import MessageRole, MessageType
            role = MessageRole.SYSTEM if msg_doc.role == "system" else (
                MessageRole.USER if msg_doc.role == "user" else MessageRole.ASSISTANT
            )
            message = Message(
                id=msg_doc.message_id,
                conversation_id=msg_doc.conversation_id,
                role=role,
                content=msg_doc.content,
                message_type=MessageType.TEXT,
                timestamp=msg_doc.timestamp,
                metadata=msg_doc.metadata
            )
            conversation.add_message(message)
        return conversation

    async def update_conversation(self, conversation: ConversationEntity) -> ConversationEntity:
        conv_doc = await ChatConversation.find_one(ChatConversation.conversation_id == conversation.id)
        if not conv_doc:
            raise ValueError(f"Conversation {conversation.id} not found")
        conv_doc.title = conversation.title
        conv_doc.context = conversation.context
        conv_doc.updated_at = datetime.utcnow()
        conv_doc.is_active = conversation.is_active
        await conv_doc.save()
        existing_messages = await ChatMessage.find(
            ChatMessage.conversation_id == conversation.id
        ).to_list()
        existing_ids = {msg.message_id for msg in existing_messages}
        for message in conversation.messages:
            if message.id not in existing_ids:
                msg_doc = ChatMessage(
                    message_id=message.id,
                    conversation_id=message.conversation_id,
                    user_id=conversation.user_id,
                    role=message.role.value.lower(),
                    content=message.content,
                    metadata=message.metadata,
                    timestamp=message.timestamp
                )
                await msg_doc.insert()
        conversation.updated_at = conv_doc.updated_at
        return conversation

    async def delete_conversation(self, conversation_id: str) -> bool:
        try:
            await ChatMessage.find(ChatMessage.conversation_id == conversation_id).delete()
            result = await ChatConversation.find_one(
                ChatConversation.conversation_id == conversation_id
            ).delete()
            return result is not None
        except Exception:
            return False

    async def get_user_conversations(self, user_id: str, limit: int = 10) -> List[ConversationEntity]:
        conv_docs = await ChatConversation.find(
            ChatConversation.user_id == user_id
        ).sort([("updated_at", -1)]).limit(limit).to_list()
        conversations = []
        for conv_doc in conv_docs:
            conversation = ConversationEntity(
                id=conv_doc.conversation_id,
                user_id=conv_doc.user_id,
                title=conv_doc.title,
                context=conv_doc.context,
                created_at=conv_doc.created_at,
                updated_at=conv_doc.updated_at,
                is_active=conv_doc.is_active
            )
            conversations.append(conversation)
        return conversations

    async def add_message_to_conversation(self, conversation_id: str, message: Message) -> bool:
        conv_doc = await ChatConversation.find_one(ChatConversation.conversation_id == conversation_id)
        if not conv_doc:
            return False
        msg_doc = ChatMessage(
            message_id=message.id,
            conversation_id=message.conversation_id,
            user_id=conv_doc.user_id,
            role=message.role.value.lower(),
            content=message.content,
            metadata=message.metadata,
            timestamp=message.timestamp
        )
        await msg_doc.insert()
        return True
