"""
Simple decorators for easier development - LangChain-style
"""

from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, status

from apex.core.authentication import get_current_active_user


def auth_required(func: Callable) -> Callable:
    """
    Decorator to require authentication for a route.
    Automatically injects the current user as the first parameter.
    
    Example:
        >>> from apex import auth_required
        >>> from apex.models import User
        >>> 
        >>> @app.get("/protected")
        >>> @auth_required
        >>> async def protected_route(user: User):
        ...     return {"message": f"Hello {user.first_name}!"}
    """
    @wraps(func)
    async def wrapper(*args, current_user=Depends(get_current_active_user), **kwargs):
        return await func(current_user, *args, **kwargs)
    return wrapper


def permission_required(permission_code: str):
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission_code: Permission code (e.g., "users:create")
    
    Example:
        >>> from apex import permission_required
        >>> 
        >>> @app.post("/admin/action")
        >>> @permission_required("admin:action")
        >>> async def admin_action():
        ...     return {"message": "Admin action performed"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement permission checking logic
            # For now, just call the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def role_required(role_name: str):
    """
    Decorator to require a specific role for a route.
    
    Args:
        role_name: Role name (e.g., "Admin", "Manager")
    
    Example:
        >>> from apex import role_required
        >>> 
        >>> @app.get("/admin/dashboard")
        >>> @role_required("Admin")
        >>> async def admin_dashboard():
        ...     return {"message": "Admin dashboard"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement role checking logic
            # For now, just call the function
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def route(
    path: str,
    methods: Optional[List[str]] = None,
    auth: bool = True,
    **kwargs
):
    """
    Simple route decorator that combines FastAPI route with auth.
    
    Args:
        path: Route path
        methods: HTTP methods (default: ["GET"])
        auth: Require authentication (default: True)
        **kwargs: Additional FastAPI route parameters
    
    Example:
        >>> from apex import route
        >>> 
        >>> @route("/api/custom", methods=["GET", "POST"])
        >>> async def custom_endpoint():
        ...     return {"message": "Custom endpoint"}
    """
    methods = methods or ["GET"]
    
    def decorator(func: Callable) -> Callable:
        # This is a placeholder - actual implementation would need
        # access to the FastAPI app instance
        if auth:
            func = auth_required(func)
        return func
    
    return decorator


def on(event: str):
    """
    Decorator for event handlers - hooks into lifecycle events.
    
    Supported events:
        - "startup": App startup
        - "shutdown": App shutdown
        - "user:created": After user creation
        - "user:login": After user login
        - "user:logout": After user logout
        - "organization:created": After organization creation
    
    Example:
        >>> from apex import on
        >>> 
        >>> @on("user:created")
        >>> async def send_welcome_email(user):
        ...     print(f"Welcome {user.email}!")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Store event name on function for later registration
        wrapper._apex_event = event
        return wrapper
    
    return decorator


def validate(schema):
    """
    Decorator to validate request data against a Pydantic schema.
    
    Args:
        schema: Pydantic model class
    
    Example:
        >>> from apex import validate
        >>> from pydantic import BaseModel
        >>> 
        >>> class CreateItemRequest(BaseModel):
        ...     name: str
        ...     price: float
        >>> 
        >>> @app.post("/items")
        >>> @validate(CreateItemRequest)
        >>> async def create_item(data: CreateItemRequest):
        ...     return {"item": data.dict()}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Validation happens automatically in FastAPI
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def cache(ttl: int = 60):
    """
    Decorator to cache endpoint responses.
    
    Args:
        ttl: Time to live in seconds
    
    Example:
        >>> from apex import cache
        >>> 
        >>> @app.get("/expensive-operation")
        >>> @cache(ttl=300)
        >>> async def expensive_operation():
        ...     # Expensive computation here
        ...     return {"result": "cached for 5 minutes"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement caching logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window: int = 60):
    """
    Decorator to rate limit an endpoint.
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
    
    Example:
        >>> from apex import rate_limit
        >>> 
        >>> @app.post("/api/action")
        >>> @rate_limit(max_requests=10, window=60)
        >>> async def limited_action():
        ...     return {"message": "Rate limited to 10 per minute"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # TODO: Implement rate limiting logic
            return await func(*args, **kwargs)
        return wrapper
    return decorator

