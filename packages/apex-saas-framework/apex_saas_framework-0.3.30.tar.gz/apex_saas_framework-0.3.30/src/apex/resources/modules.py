"""
Modules Resource - Clerk-style feature flags/modules management
"""
from typing import Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from apex.client import Client


class Modules:
    """
    Modules resource - provides feature flags/modules management
    
    Usage:
        async with client:
            # Enable a module
            modules = await client.modules.set(
                org_id=str(org.id),
                module="customer_management",
                enabled=True
            )
            
            # Get modules
            modules = await client.modules.get(org_id=str(org.id))
    """
    
    def __init__(self, client: Client, organization_model: Optional[Type[Any]] = None):
        """
        Initialize Modules resource.
        
        Args:
            client: Apex client instance
            organization_model: Organization model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.organization_model = organization_model or client.organization_model
    
    async def set(self, org_id: Any, module: str, enabled: bool) -> dict:
        """
        Set a module (feature flag) for an organization.
        
        Args:
            org_id: Organization UUID
            module: Module name (e.g., "customer_management", "invoice_system")
            enabled: Whether to enable or disable the module
        
        Returns:
            Updated modules dictionary
        
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
            
            modules = org.modules or {}
            modules[module] = enabled
            org.modules = modules
            
            await session.flush()
            await session.refresh(org)
            await session.commit()
            
            return modules
    
    async def get(self, org_id: Any) -> dict:
        """
        Get all modules (feature flags) for an organization.
        
        Args:
            org_id: Organization UUID
        
        Returns:
            Modules dictionary
        
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
            
            return org.modules or {}
    
    async def is_enabled(self, org_id: Any, module: str) -> bool:
        """
        Check if a module is enabled for an organization.
        
        Args:
            org_id: Organization UUID
            module: Module name
        
        Returns:
            True if enabled, False otherwise
        """
        modules = await self.get(org_id)
        return modules.get(module, False)

