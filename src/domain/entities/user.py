"""User domain entity"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User domain entity - simplified for chat microservice"""
    user_id: str
    learning_level: str = "intermediate"
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_learning_level(self, level: str):
        """Update user's learning level"""
        self.learning_level = level
        self.updated_at = datetime.utcnow()