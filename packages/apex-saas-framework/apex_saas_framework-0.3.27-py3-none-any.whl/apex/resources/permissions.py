"""
Permissions Resource - Clerk-style permission management
"""
from typing import Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apex.client import Client


class Permissions:
    """
    Permissions resource - provides permission management methods
    """
    
    def __init__(self, client: Client, permission_model: Optional[Type[Any]] = None):
        """
        Initialize Permissions resource.
        
        Args:
            client: Apex client instance
            permission_model: Permission model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.permission_model = permission_model
    
    async def create(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a new permission"""
        if not self.permission_model:
            raise ValueError("permission_model must be provided")
        
        async with self.client.get_session() as session:
            permission = self.permission_model(
                name=name,
                slug=slug,
                description=description,
                **kwargs
            )
            session.add(permission)
            await session.flush()
            await session.refresh(permission)
            await session.commit()
            return permission
    
    async def get(self, permission_id: Any) -> Optional[Any]:
        """Get permission by ID"""
        if not self.permission_model:
            raise ValueError("permission_model must be provided")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.permission_model)
            converted_id = convert_id_to_type(permission_id, pk_type)
            return await session.get(self.permission_model, converted_id)
    
    async def list(self) -> list[Any]:
        """List all permissions"""
        if not self.permission_model:
            raise ValueError("permission_model must be provided")
        
        async with self.client.get_session() as session:
            result = await session.execute(select(self.permission_model))
            return list(result.scalars().all())


