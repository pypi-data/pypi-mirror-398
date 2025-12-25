"""
Model Registry - Prevents table name conflicts and makes model definition easy.

Usage:
    from apex.models import register_model, create_table
    
    # Register your model
    @register_model
    class User(Base, UUIDPKMixin, TimestampMixin):
        __tablename__ = "users"
        email = Column(String(255))
    
    # Create all registered tables (no conflicts!)
    create_tables()
"""

from typing import Dict, List, Type, Any, Optional, Set
import warnings


class ModelRegistry:
    """Registry to track all models and prevent table name conflicts."""
    
    def __init__(self):
        self._models: Dict[str, Type[Any]] = {}
        self._table_names: Set[str] = set()
        self._schemas: Dict[str, str] = {}  # table_name -> schema
    
    def register(self, model: Type[Any], schema: Optional[str] = None) -> Type[Any]:
        """
        Register a model and check for table name conflicts.
        
        Args:
            model: SQLAlchemy model class
            schema: Optional schema name (for multi-tenant or namespacing)
        
        Returns:
            The model class (for use as decorator)
        
        Raises:
            ValueError: If table name conflicts with existing model
        """
        if not hasattr(model, "__tablename__"):
            raise ValueError(f"Model {model.__name__} must have __tablename__ attribute")
        
        table_name = model.__tablename__
        full_name = f"{schema}.{table_name}" if schema else table_name
        
        # Check for conflicts
        if full_name in self._table_names:
            existing_model = self._models.get(full_name)
            if existing_model:
                raise ValueError(
                    f"Table name conflict: '{full_name}' is already used by {existing_model.__name__}. "
                    f"Use a different __tablename__ or schema."
                )
        
        # Register
        self._models[full_name] = model
        self._table_names.add(full_name)
        if schema:
            self._schemas[table_name] = schema
        
        return model
    
    def get_all_models(self) -> List[Type[Any]]:
        """Get all registered models."""
        return list(self._models.values())
    
    def get_table_names(self) -> Set[str]:
        """Get all registered table names."""
        return self._table_names.copy()
    
    def validate_no_conflicts(self) -> bool:
        """Validate that all registered models have unique table names."""
        seen = set()
        conflicts = []
        
        for full_name, model in self._models.items():
            if full_name in seen:
                conflicts.append(full_name)
            seen.add(full_name)
        
        if conflicts:
            raise ValueError(f"Table name conflicts detected: {', '.join(conflicts)}")
        
        return True


# Global registry instance
_registry = ModelRegistry()


def register_model(model: Optional[Type[Any]] = None, schema: Optional[str] = None):
    """
    Decorator to register a model and prevent conflicts.
    
    Usage:
        @register_model
        class User(Base, UUIDPKMixin, TimestampMixin):
            __tablename__ = "users"
            email = Column(String(255))
        
        # Or with schema:
        @register_model(schema="app")
        class User(Base, UUIDPKMixin, TimestampMixin):
            __tablename__ = "users"
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        return _registry.register(cls, schema=schema)
    
    if model is None:
        return decorator
    else:
        return decorator(model)


def get_registry() -> ModelRegistry:
    """Get the global model registry."""
    return _registry


def validate_models() -> bool:
    """Validate all registered models for conflicts."""
    return _registry.validate_no_conflicts()


def get_all_models() -> List[Type[Any]]:
    """Get all registered models."""
    return _registry.get_all_models()







