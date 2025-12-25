"""
Authentication decorators and middleware for Flask and FastAPI
"""

from typing import Optional, List, Callable
from functools import wraps
from .user_verifier import UserVerifier
from .schemas import User


# Flask Support
try:
    from flask import request, jsonify, g, Response
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False


# FastAPI Support
try:
    from fastapi import HTTPException, Header, Depends, status
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


def require_auth(
    verifier: UserVerifier,
    required_roles: Optional[List[str]] = None,
    header_name: str = "x-user-email",
    auto_create: bool = False
) -> Callable:
    """
    Flask decorator for authentication
    
    Args:
        verifier: UserVerifier instance
        required_roles: Optional list of required roles
        header_name: Header name to check (default: 'x-user-email')
        auto_create: Auto-create user if doesn't exist (default: False)
    
    Usage:
        @app.route('/protected')
        @require_auth(verifier, required_roles=['admin'])
        def protected_route():
            user = g.current_user
            return jsonify({"message": "Access granted"})
    """
    if not FLASK_AVAILABLE:
        raise ImportError("Flask is required for Flask decorators")
    
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_identifier = request.headers.get(header_name)
            
            if not user_identifier:
                # Try alternative headers
                user_identifier = request.headers.get("x-user-id") or request.headers.get("Authorization")
                if user_identifier and user_identifier.startswith("Bearer "):
                    # Extract from token if needed (basic support)
                    user_identifier = user_identifier[7:]
            
            if not user_identifier:
                return jsonify({"error": "Unauthorized - Missing user identifier"}), 401
            
            # Get user from Cosmos DB
            user = verifier.get_user(user_identifier)
            
            if not user:
                if auto_create:
                    user = verifier.create_user(
                        email=user_identifier,
                        display_name=user_identifier
                    )
                else:
                    return jsonify({"error": "Unauthorized - User not found"}), 401
            
            # Check role if required
            if required_roles:
                if user.role not in required_roles:
                    return jsonify({"error": "Forbidden - Insufficient permissions"}), 403
            
            # Attach user to request context
            g.current_user = user
            g.user_id = user.user_id
            g.user_email = user.email
            g.user_role = user.role
            
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_current_user_fastapi(
    verifier: UserVerifier,
    header_name: str = "x-user-email",
    auto_create: bool = False
):
    """
    FastAPI dependency for getting current authenticated user
    
    Args:
        verifier: UserVerifier instance
        header_name: Header name to check (default: 'x-user-email')
        auto_create: Auto-create user if doesn't exist (default: False)
    
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user_fastapi(verifier))):
            return {"message": f"Hello {current_user.email}"}
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required for FastAPI dependencies")
    
    async def _get_current_user(
        user_header: Optional[str] = Header(None, alias=header_name),
        user_id_header: Optional[str] = Header(None, alias="x-user-id"),
    ) -> User:
        user_identifier = user_header or user_id_header
        
        if not user_identifier:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized - Missing user identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from Cosmos DB
        user = verifier.get_user(user_identifier)
        
        if not user:
            if auto_create:
                user = verifier.create_user(
                    email=user_identifier,
                    display_name=user_identifier
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unauthorized - User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        return user
    
    return _get_current_user


def require_role_fastapi(
    verifier: UserVerifier,
    required_roles: List[str],
    header_name: str = "x-user-email",
    auto_create: bool = False
):
    """
    FastAPI dependency with role checking
    
    Args:
        verifier: UserVerifier instance
        required_roles: List of required roles
        header_name: Header name to check
        auto_create: Auto-create user if doesn't exist
    
    Usage:
        @app.get("/admin")
        async def admin_route(
            current_user: User = Depends(require_role_fastapi(verifier, ['admin']))
        ):
            return {"message": "Admin access"}
    """
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required for FastAPI dependencies")
    
    async def _require_role(
        current_user: User = Depends(get_current_user_fastapi(verifier, header_name, auto_create))
    ) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden - Insufficient permissions",
            )
        return current_user
    
    return _require_role


# Alias for convenience
get_current_user = get_current_user_fastapi

