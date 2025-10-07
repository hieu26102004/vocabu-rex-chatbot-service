"""MongoDB repository implementations"""
from typing import Optional, List
from datetime import datetime

from ...domain.entities.user import User as UserEntity
from ...domain.entities.conversation import Conversation as ConversationEntity
from ...domain.repositories.chat_repositories import UserRepository, ConversationRepository
from .models import User as UserModel, ChatConversation, ChatMessage


class MongoUserRepository(UserRepository):
    """MongoDB implementation of UserRepository"""
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserEntity]:
        """Get user by ID"""
        user_doc = await UserModel.find_one(UserModel.user_id == user_id)
        if not user_doc:
            return None
        
        return UserEntity(
            user_id=user_doc.user_id,
            learning_level=user_doc.learning_level,
            created_at=user_doc.created_at,
            updated_at=user_doc.updated_at
        )
    
    async def create_user(self, user: UserEntity) -> UserEntity:
        """Create new user"""
        user_doc = UserModel(
            user_id=user.user_id,
            learning_level=user.learning_level
        )
        await user_doc.insert()
        
        # Return updated entity with timestamps
        return UserEntity(
            user_id=user_doc.user_id,
            learning_level=user_doc.learning_level,
            created_at=user_doc.created_at,
            updated_at=user_doc.updated_at
        )
    
    async def update_user(self, user: UserEntity) -> UserEntity:
        """Update existing user"""
        user_doc = await UserModel.find_one(UserModel.user_id == user.user_id)
        if not user_doc:
            raise ValueError(f"User {user.user_id} not found")
        
        user_doc.learning_level = user.learning_level
        user_doc.updated_at = datetime.utcnow()
        
        await user_doc.save()
        
        return UserEntity(
            user_id=user_doc.user_id,
            learning_level=user_doc.learning_level,
            created_at=user_doc.created_at,
            updated_at=user_doc.updated_at
        )


class MongoConversationRepository(ConversationRepository):
    """MongoDB implementation of ConversationRepository"""
    
    async def get_conversation(self, conversation_id: str) -> Optional[ConversationEntity]:
        """Get conversation by ID with messages"""
        conv_doc = await ChatConversation.find_one(ChatConversation.conversation_id == conversation_id)
        if not conv_doc:
            return None
        
        # Get messages for this conversation
        message_docs = await ChatMessage.find(
            ChatMessage.conversation_id == conversation_id
        ).sort(ChatMessage.timestamp).to_list()
        
        # Convert to domain entity
        conversation = ConversationEntity(
            id=conv_doc.conversation_id,
            user_id=conv_doc.user_id,
            title=conv_doc.title,
            context=conv_doc.context,
            created_at=conv_doc.created_at,
            updated_at=conv_doc.updated_at,
            is_active=conv_doc.is_active
        )
        
        # Add messages
        for msg_doc in message_docs:
            from ...domain.entities.message import Message, MessageRole, MessageType
            
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
    
    async def create_conversation(self, conversation: ConversationEntity) -> ConversationEntity:
        """Create new conversation with messages"""
        # Create conversation document
        conv_doc = ChatConversation(
            conversation_id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title or f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            context=conversation.context
        )
        await conv_doc.insert()
        
        # Create message documents
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
        
        # Return updated entity
        conversation.created_at = conv_doc.created_at
        conversation.updated_at = conv_doc.updated_at
        return conversation
    
    async def update_conversation(self, conversation: ConversationEntity) -> ConversationEntity:
        """Update existing conversation and add new messages"""
        conv_doc = await ChatConversation.find_one(ChatConversation.conversation_id == conversation.id)
        if not conv_doc:
            raise ValueError(f"Conversation {conversation.id} not found")
        
        # Update conversation metadata
        conv_doc.title = conversation.title
        conv_doc.context = conversation.context
        conv_doc.updated_at = datetime.utcnow()
        conv_doc.is_active = conversation.is_active
        await conv_doc.save()
        
        # Get existing message IDs to avoid duplicates
        existing_messages = await ChatMessage.find(
            ChatMessage.conversation_id == conversation.id
        ).to_list()
        existing_ids = {msg.message_id for msg in existing_messages}
        
        # Add new messages only
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
        
        # Return updated entity
        conversation.updated_at = conv_doc.updated_at
        return conversation
    
    async def get_user_conversations(self, user_id: str, limit: int = 10) -> List[ConversationEntity]:
        """Get user's conversations"""
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
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and its messages"""
        try:
            # Delete messages first
            await ChatMessage.find(ChatMessage.conversation_id == conversation_id).delete()
            
            # Delete conversation
            result = await ChatConversation.find_one(
                ChatConversation.conversation_id == conversation_id
            ).delete()
            
            return result is not None
        except Exception:
            return False