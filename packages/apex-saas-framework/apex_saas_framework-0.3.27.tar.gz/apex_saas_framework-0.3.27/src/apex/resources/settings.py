"""
Settings Resource - Clerk-style settings management
"""
from typing import Optional, Dict, Any, Type
from sqlalchemy.ext.asyncio import AsyncSession
from apex.client import Client


class Settings:
    """
    Settings resource - provides user and organization settings management
    
    Usage:
        async with client:
            # Update user settings
            settings = await client.settings.update_user(
                user_id=str(user.id),
                preferences={"theme": "dark", "language": "en"}
            )
            
            # Get user settings
            settings = await client.settings.get_user(user_id=str(user.id))
            
            # Update organization settings
            settings = await client.settings.update_organization(
                org_id=str(org.id),
                preferences={"billing_email": "billing@example.com"}
            )
    """
    
    def __init__(
        self,
        client: Client,
        user_model: Optional[Type[Any]] = None,
        organization_model: Optional[Type[Any]] = None
    ):
        """
        Initialize Settings resource.
        
        Args:
            client: Apex client instance
            user_model: User model class (can be any SQLAlchemy model - your choice!)
            organization_model: Organization model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.user_model = user_model or client.user_model
        self.organization_model = organization_model or client.organization_model
    
    async def update_user(self, user_id: Any, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user settings/preferences.
        
        Args:
            user_id: User UUID
            preferences: Dictionary of preferences to update (will be merged with existing)
        
        Returns:
            Updated preferences dictionary
        
        Raises:
            ValueError: If user not found
        """
        if not self.user_model:
            raise ValueError("user_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.user_model)
            converted_id = convert_id_to_type(user_id, pk_type)
            user = await session.get(self.user_model, converted_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            # Merge with existing settings
            existing = user.settings or {}
            existing.update(preferences)
            user.settings = existing
            
            await session.flush()
            await session.refresh(user)
            await session.commit()
            
            return user.settings
    
    async def get_user(self, user_id: Any) -> Dict[str, Any]:
        """
        Get user settings/preferences.
        
        Args:
            user_id: User UUID
        
        Returns:
            Preferences dictionary
        
        Raises:
            ValueError: If user not found
        """
        if not self.user_model:
            raise ValueError("user_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.user_model)
            converted_id = convert_id_to_type(user_id, pk_type)
            user = await session.get(self.user_model, converted_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            return user.settings or {}
    
    async def update_organization(
        self,
        org_id: Any,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update organization settings/preferences.
        
        Args:
            org_id: Organization UUID
            preferences: Dictionary of preferences to update (will be merged with existing)
        
        Returns:
            Updated preferences dictionary
        
        Raises:
            ValueError: If organization not found
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.organization_model)
            converted_id = convert_id_to_type(org_id, pk_type)
            org = await session.get(self.organization_model, converted_id)
            if not org:
                raise ValueError(f"Organization with id {org_id} not found")
            
            # Merge with existing settings
            existing = org.settings or {}
            existing.update(preferences)
            org.settings = existing
            
            await session.flush()
            await session.refresh(org)
            await session.commit()
            
            return org.settings
    
    async def get_organization(self, org_id: Any) -> Dict[str, Any]:
        """
        Get organization settings/preferences.
        
        Args:
            org_id: Organization UUID
        
        Returns:
            Preferences dictionary
        
        Raises:
            ValueError: If organization not found
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.organization_model)
            converted_id = convert_id_to_type(org_id, pk_type)
            org = await session.get(self.organization_model, converted_id)
            if not org:
                raise ValueError(f"Organization with id {org_id} not found")
            
            return org.settings or {}

