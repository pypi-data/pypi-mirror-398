"""
User verification functions for Cosmos DB
"""

from typing import Optional, Dict, List
from azure.cosmos import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError
from azure.cosmos import CosmosDict
from .schemas import User, UserRole


class UserVerifier:
    """User verification and management for Cosmos DB"""
    
    def __init__(self, user_container: ContainerProxy):
        """
        Initialize UserVerifier with Cosmos DB container
        
        Args:
            user_container: Azure Cosmos DB ContainerProxy for users
        """
        if not user_container:
            raise ValueError("user_container is required")
        self.container = user_container
    
    def verify_user_exists(self, user_id: str) -> bool:
        """
        Verify if user exists in Cosmos DB
        
        Args:
            user_id: User ID (email or username)
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            user = self.get_user(user_id)
            return user is not None
        except Exception:
            return False
    
    def get_user(self, user_id: str) -> Optional[User]:
        """
        Get user from Cosmos DB by user_id (email or username)
        
        Args:
            user_id: User ID (email or username)
            
        Returns:
            User object if found, None otherwise
        """
        try:
            item_id = f"user_{user_id}"
            item = self.container.read_item(
                item=item_id,
                partition_key=user_id
            )
            
            if isinstance(item, CosmosDict):
                return User.from_dict(dict(item))
            return User.from_dict(item)
        except CosmosResourceNotFoundError:
            return None
        except Exception as e:
            raise Exception(f"Error getting user: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address
        
        Args:
            email: User email address
            
        Returns:
            User object if found, None otherwise
        """
        return self.get_user(email)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username
            
        Returns:
            User object if found, None otherwise
        """
        # Query by username
        query = "SELECT * FROM c WHERE c.username = @username AND c.type = 'user'"
        parameters = [{"name": "@username", "value": username}]
        
        items = self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        )
        
        for item in items:
            return User.from_dict(dict(item))
        
        return None
    
    def create_user(
        self,
        email: str,
        username: Optional[str] = None,
        role: Optional[str] = None,
        display_name: Optional[str] = None,
        **kwargs
    ) -> User:
        """
        Create a new user in Cosmos DB
        
        Args:
            email: User email (used as user_id)
            username: Username (defaults to email prefix)
            role: User role (defaults to 'user')
            display_name: Display name (defaults to username)
            **kwargs: Additional user fields
            
        Returns:
            Created User object
        """
        user = User(
            user_id=email,
            email=email,
            username=username,
            role=role,
            display_name=display_name,
            **kwargs
        )
        
        user_dict = user.to_dict()
        self.container.upsert_item(user_dict)
        
        return user
    
    def get_or_create_user(
        self,
        email: str,
        username: Optional[str] = None,
        role: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> User:
        """
        Get user if exists, otherwise create new user
        
        Args:
            email: User email
            username: Username
            role: User role
            display_name: Display name
            
        Returns:
            User object (existing or newly created)
        """
        user = self.get_user_by_email(email)
        if user:
            return user
        
        return self.create_user(
            email=email,
            username=username,
            role=role,
            display_name=display_name
        )
    
    def verify_user_role(self, user_id: str, required_roles: List[str]) -> bool:
        """
        Verify if user has one of the required roles
        
        Args:
            user_id: User ID
            required_roles: List of required roles
            
        Returns:
            True if user has required role, False otherwise
        """
        user = self.get_user(user_id)
        if not user:
            return False
        
        return user.role in required_roles
    
    def update_user_role(self, user_id: str, new_role: str) -> bool:
        """
        Update user role
        
        Args:
            user_id: User ID
            new_role: New role
            
        Returns:
            True if updated successfully
        """
        try:
            item_id = f"user_{user_id}"
            patch_operations = [{'op': 'set', 'path': '/role', 'value': new_role}]
            
            self.container.patch_item(
                item=item_id,
                partition_key=user_id,
                patch_operations=patch_operations
            )
            return True
        except Exception:
            return False

