"""MongoDB implementation of UserRepository"""
from typing import Optional
from datetime import datetime
from ...domain.entities.user import User as UserEntity
from ...domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from ..database.models import User as UserModel

class UserRepository(UserRepositoryInterface):
    async def get_user_by_id(self, user_id: str) -> Optional[UserEntity]:
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
        user_doc = UserModel(
            user_id=user.user_id,
            learning_level=user.learning_level
        )
        await user_doc.insert()
        return UserEntity(
            user_id=user_doc.user_id,
            learning_level=user_doc.learning_level,
            created_at=user_doc.created_at,
            updated_at=user_doc.updated_at
        )

    async def update_user(self, user: UserEntity) -> UserEntity:
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
