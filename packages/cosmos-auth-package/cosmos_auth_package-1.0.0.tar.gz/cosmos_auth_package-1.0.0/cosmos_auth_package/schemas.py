"""
User schemas and models for Cosmos Auth Package
"""

from typing import Optional, List
from enum import Enum


class UserRole(str, Enum):
    """User role enumeration"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class User:
    """User model for Cosmos DB"""
    
    def __init__(
        self,
        user_id: str,
        email: str,
        username: Optional[str] = None,
        role: Optional[str] = None,
        display_name: Optional[str] = None,
        is_active: bool = True,
        **kwargs
    ):
        self.id = f"user_{user_id}"
        self.type = "user"
        self.user_id = user_id
        self.email = email
        self.username = username or email.split("@")[0]
        self.role = role or UserRole.USER.value
        self.display_name = display_name or username or email
        self.is_active = is_active
        self.agents = kwargs.get("agents", [])
        self.created_at = kwargs.get("created_at")
        self.updated_at = kwargs.get("updated_at")
    
    def to_dict(self) -> dict:
        """Convert user to dictionary for Cosmos DB"""
        return {
            "id": self.id,
            "type": self.type,
            "user_id": self.user_id,
            "email": self.email,
            "username": self.username,
            "role": self.role,
            "display_name": self.display_name,
            "is_active": self.is_active,
            "agents": self.agents,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create user from Cosmos DB dictionary"""
        return cls(
            user_id=data.get("user_id", ""),
            email=data.get("email", ""),
            username=data.get("username"),
            role=data.get("role"),
            display_name=data.get("display_name"),
            is_active=data.get("is_active", True),
            agents=data.get("agents", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

