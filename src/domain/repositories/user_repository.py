"""Repository interface for user domain"""
from abc import ABC, abstractmethod
from typing import Optional
from ...domain.entities.user import User

class UserRepository(ABC):
    """Abstract repository for user operations"""
    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass

    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create new user"""
        pass

    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update existing user"""
        pass
