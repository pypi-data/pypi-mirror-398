"""
Organization management functions - LangChain-style direct imports.

Usage:
    from apex.organizations import create_organization, get_organization
    
    # Set client once
    from apex import Client, set_default_client
    client = Client(database_url="...", organization_model=Organization)
    set_default_client(client)
    
    # Use functions directly (no await, no client parameter)
    org = create_organization(name="My Org")
    org = get_organization(org_id=org.id)
"""

from typing import Any, List, Optional

from apex.client import Client
from apex.sync import (
    create_organization as _create_organization,
    get_organization as _get_organization,
    list_organizations as _list_organizations,
    set_default_client as _set_default_client,
)


def set_client(client: Client) -> None:
    """Set the default client for organization operations."""
    _set_default_client(client)


def create_organization(
    name: str,
    client: Optional[Client] = None,
    **kwargs
) -> Any:
    """
    Create a new organization.
    
    Args:
        name: Organization name
        client: Optional client instance (uses default if not provided)
        **kwargs: Additional organization fields
    
    Returns:
        Created organization instance
    
    Example:
        from apex.organizations import create_organization, set_client
        from apex import Client
        
        client = Client(database_url="...", organization_model=Organization)
        set_client(client)
        org = create_organization(name="My Org")
    """
    return _create_organization(client=client, name=name, **kwargs)


def get_organization(
    org_id: Any,
    client: Optional[Client] = None,
) -> Optional[Any]:
    """
    Get an organization by ID.
    
    Args:
        org_id: Organization ID
        client: Optional client instance (uses default if not provided)
    
    Returns:
        Organization instance or None
    
    Example:
        from apex.organizations import get_organization
        org = get_organization(org_id=1)
    """
    return _get_organization(client=client, org_id=org_id)


def list_organizations(
    client: Optional[Client] = None,
) -> List[Any]:
    """
    List all organizations.
    
    Args:
        client: Optional client instance (uses default if not provided)
    
    Returns:
        List of organization instances
    
    Example:
        from apex.organizations import list_organizations
        orgs = list_organizations()
    """
    return _list_organizations(client=client)


__all__ = ["create_organization", "get_organization", "list_organizations", "set_client"]

