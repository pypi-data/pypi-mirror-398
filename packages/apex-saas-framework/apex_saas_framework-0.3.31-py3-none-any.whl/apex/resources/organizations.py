"""
Organizations Resource - Clerk-style organization management
"""
from typing import Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from apex.client import Client


class Organizations:
    """
    Organizations resource - provides organization management methods
    
    Usage:
        async with client:
            # Create organization
            org = await client.organizations.create(
                name="My Company",
                description="Company description"
            )
            
            # Get organization
            org = await client.organizations.get(org_id=str(org.id))
            
            # Update organization
            org = await client.organizations.update(
                org_id=str(org.id),
                name="Updated Name"
            )
            
            # Delete organization
            await client.organizations.delete(org_id=str(org.id))
    """
    
    def __init__(self, client: Client, organization_model: Optional[Type[Any]] = None):
        """
        Initialize Organizations resource.
        
        Args:
            client: Apex client instance
            organization_model: Organization model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.organization_model = organization_model
    
    async def create(
        self,
        name: str,
        slug: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create a new organization.
        
        Args:
            name: Organization name (required)
            slug: Organization slug (optional, auto-generated if not provided)
            description: Organization description
            **kwargs: Additional organization fields
        
        Returns:
            Created organization instance
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            # Only include description if it's not None
            org_kwargs = {"name": name}
            if slug is not None:
                org_kwargs["slug"] = slug
            if description is not None:
                org_kwargs["description"] = description
            org_kwargs.update(kwargs)
            
            org = self.organization_model(**org_kwargs)
            session.add(org)
            await session.flush()
            await session.refresh(org)
            await session.commit()
            return org
    
    async def get(self, org_id: Any) -> Optional[Any]:
        """
        Get organization by ID.
        
        Args:
            org_id: Organization UUID
        
        Returns:
            Organization instance or None if not found
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            # Convert ID to correct type
            pk_type = get_primary_key_type(self.organization_model)
            converted_id = convert_id_to_type(org_id, pk_type)
            
            org = await session.get(self.organization_model, converted_id)
            return org
    
    async def update(self, org_id: Any, **kwargs) -> Any:
        """
        Update organization fields.
        
        Args:
            org_id: Organization UUID
            **kwargs: Fields to update
        
        Returns:
            Updated organization instance
        
        Raises:
            ValueError: If organization not found
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_column, get_primary_key_type, convert_id_to_type
            
            # Get primary key and convert ID to correct type
            pk_column_name = get_primary_key_column(self.organization_model)
            pk_type = get_primary_key_type(self.organization_model)
            converted_id = convert_id_to_type(org_id, pk_type)
            
            # Use get() method which works with any primary key type
            org = await session.get(self.organization_model, converted_id)
            if not org:
                raise ValueError(f"Organization with id {org_id} not found")
            
            for key, value in kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)
            
            await session.flush()
            await session.refresh(org)
            await session.commit()
            return org
    
    async def delete(self, org_id: Any) -> bool:
        """
        Delete an organization.
        
        Args:
            org_id: Organization UUID
        
        Returns:
            True if deleted, False if not found
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            from apex.core.utils import get_primary_key_type, convert_id_to_type
            
            # Convert ID to correct type
            pk_type = get_primary_key_type(self.organization_model)
            converted_id = convert_id_to_type(org_id, pk_type)
            
            org = await session.get(self.organization_model, converted_id)
            if not org:
                return False
            
            await session.delete(org)
            await session.commit()
            return True
    
    async def list(self) -> list[Any]:
        """
        List all organizations.
        
        Returns:
            List of organization instances
        """
        if not self.organization_model:
            raise ValueError("organization_model must be provided to Client")
        
        async with self.client.get_session() as session:
            result = await session.execute(select(self.organization_model))
            return list(result.scalars().all())


