"""
Roles Resource - Clerk-style role management
"""
from typing import Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apex.client import Client


class Roles:
    """
    Roles resource - provides role management methods
    """
    
    def __init__(self, client: Client, role_model: Optional[Type[Any]] = None):
        """
        Initialize Roles resource.
        
        Args:
            client: Apex client instance
            role_model: Role model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.role_model = role_model
    
    async def create(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Any:
        """Create a new role"""
        if not self.role_model:
            raise ValueError("role_model must be provided")
        
        async with self.client.get_session() as session:
            role = self.role_model(
                name=name,
                slug=slug,
                description=description,
                **kwargs
            )
            session.add(role)
            await session.flush()
            await session.refresh(role)
            await session.commit()
            return role
    
    async def get(self, role_id: Any) -> Optional[Any]:
        """Get role by ID"""
        if not self.role_model:
            raise ValueError("role_model must be provided")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            pk_type = get_primary_key_type(self.role_model)
            converted_id = convert_id_to_type(role_id, pk_type)
            return await session.get(self.role_model, converted_id)
    
    async def list(self) -> list[Any]:
        """List all roles"""
        if not self.role_model:
            raise ValueError("role_model must be provided")
        
        async with self.client.get_session() as session:
            result = await session.execute(select(self.role_model))
            return list(result.scalars().all())


