"""
Cosmos Auth Package - Azure Cosmos DB Authentication and User Verification
"""

from .user_verifier import UserVerifier
from .auth_decorators import (
    require_auth,
    get_current_user_fastapi,
    require_role_fastapi,
    get_current_user,
)
from .schemas import User, UserRole

__version__ = "1.0.0"
__all__ = [
    "UserVerifier",
    "require_auth",
    "get_current_user_fastapi",
    "require_role_fastapi",
    "get_current_user",
    "User",
    "UserRole",
]

