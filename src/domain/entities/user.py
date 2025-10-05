"""User domain entity"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class User:
    """User domain entity"""
    user_id: str
    email: Optional[str] = None
    username: Optional[str] = None
    learning_level: str = "intermediate"
    preferences: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_learning_level(self, level: str):
        """Update user's learning level"""
        self.learning_level = level
        self.updated_at = datetime.utcnow()
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        self.preferences.update(preferences)
        self.updated_at = datetime.utcnow()