"""
Easy model definition and management - No conflicts, simple setup.

Usage:
    # Option 1: Use decorator (Recommended - Simple!)
    from apex.models import Model, ID, Timestamps, register_model
    
    @register_model
    class User(Model, ID, Timestamps):
        __tablename__ = "users"
        email = Column(String(255))
    
    # Option 2: Use helper function
    from apex.models import define_model, create_tables
    
    User = define_model("User", "users", {"email": Column(String(255))})
    create_tables()
    
    # Option 3: Traditional (still works, but register for conflict checking)
    from apex.models import Model, ID, Timestamps, register_model
    
    @register_model
    class Product(Model, ID, Timestamps):
        __tablename__ = "products"
        name = Column(String(255))
"""

# Base class - Simple name
from apex.core.base import Base as _Base

# User-friendly base class
class Model(_Base):
    """
    Simple base class for all models.
    
    Usage:
        from apex.models import Model
        
        class User(Model):
            __tablename__ = "users"
            id = Column(UUID, primary_key=True)
    """
    __abstract__ = True

# Primary Key Mixins - Simple names
from apex.core.base import (
    UUIDPKMixin,
    IntegerPKMixin,
    StringPKMixin,
    MySQLUUIDMixin,
)

# User-friendly aliases
ID = UUIDPKMixin  # Simple: "ID" instead of "UUIDPKMixin"
IntID = IntegerPKMixin  # Integer ID
StrID = StringPKMixin  # String ID

# Timestamp Mixins - Simple names
from apex.core.base import TimestampMixin

# User-friendly aliases
Timestamps = TimestampMixin  # Simple: "Timestamps" instead of "TimestampMixin"
CreatedUpdated = TimestampMixin  # Alternative name
AutoTimestamps = TimestampMixin  # Another alternative

# Other mixins
from apex.core.base import (
    FlexibleBaseModel,
    JSONType,
)

# Model aliases (pre-defined models)
from apex.domain.models.user import BaseUser
from apex.domain.models.organization import BaseOrganization, BaseOrganizationLocation
from apex.domain.models.role import BaseRole
from apex.domain.models.permission import BasePermission

User = BaseUser
Organization = BaseOrganization
OrganizationLocation = BaseOrganizationLocation
Role = BaseRole
Permission = BasePermission

# Registry and helpers
from apex.models.registry import (
    register_model,
    get_registry,
    validate_models,
    get_all_models,
)

from apex.models.helpers import (
    define_model,
    create_tables,
    auto_table_name,
)

# Export both simple and technical names
__all__ = [
    # Simple base class
    "Model",
    "Base",  # Also export Base for advanced users
    
    # Simple ID mixins
    "ID",  # UUID primary key (most common)
    "IntID",  # Integer primary key
    "StrID",  # String primary key
    
    # Technical names (for advanced users)
    "UUIDPKMixin",
    "IntegerPKMixin",
    "StringPKMixin",
    "MySQLUUIDMixin",
    
    # Simple timestamp mixins
    "Timestamps",  # Most common
    "CreatedUpdated",  # Alternative
    "AutoTimestamps",  # Alternative
    
    # Technical name
    "TimestampMixin",
    
    # Other utilities
    "FlexibleBaseModel",
    "JSONType",
    
    # Pre-defined models
    "User",
    "Organization",
    "OrganizationLocation",
    "Role",
    "Permission",
    "BaseUser",
    "BaseOrganization",
    "BaseOrganizationLocation",
    "BaseRole",
    "BasePermission",
    
    # Registry
    "register_model",
    "get_registry",
    "validate_models",
    "get_all_models",
    
    # Helpers
    "define_model",
    "create_tables",
    "auto_table_name",
]

# Re-export Base for backward compatibility
Base = _Base







