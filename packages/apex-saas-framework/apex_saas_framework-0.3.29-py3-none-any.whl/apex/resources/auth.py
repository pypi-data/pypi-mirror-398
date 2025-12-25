"""
Auth Resource - Clerk-style authentication
"""
from typing import Optional, Type, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from apex.client import Client
from apex.domain.services.auth import AuthService


class Auth:
    """
    Authentication resource - provides authentication methods
    
    Usage:
        async with client:
            # Sign up
            user = await client.auth.signup(
                email="user@example.com",
                password="password123",
                first_name="John"
            )
            
            # Login
            tokens = await client.auth.login(
                email="user@example.com",
                password="password123"
            )
            
            # Verify token
            payload = await client.auth.verify_token(tokens["access_token"])
            
            # Refresh token
            new_tokens = await client.auth.refresh_token(tokens["refresh_token"])
    """
    
    def __init__(self, client: Client, user_model: Optional[Type[Any]] = None):
        """
        Initialize Auth resource.
        
        Args:
            client: Apex client instance
            user_model: User model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.user_model = user_model
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user and get tokens.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dictionary with access_token, refresh_token, and token_type
        
        Raises:
            ValueError: If credentials are invalid or secret_key not provided
        """
        # Secret key should always be available (auto-generated if not provided)
        if not self.client.secret_key:
            # This shouldn't happen, but just in case, generate one
            import secrets
            self.client.secret_key = secrets.token_urlsafe(32)
        
        async with self.client.get_session() as session:
            auth_service = AuthService(
                session=session,
                user_model=self.user_model,
                secret_key=self.client.secret_key
            )
            
            user = await auth_service.authenticate_user(email, password)
            if not user:
                raise ValueError("Invalid email or password")
            
            # Update last_login if field exists
            if hasattr(user, 'last_login'):
                from datetime import datetime
                user.last_login = datetime.utcnow()
                await session.flush()
            
            tokens = await auth_service.create_tokens(user)
            return tokens
    
    async def signup(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Sign up a new user.
        
        Args:
            email: User email
            password: User password
            first_name: First name
            last_name: Last name
            **kwargs: Additional user fields
        
        Returns:
            Created user instance
        
        Raises:
            ValueError: If user already exists
        """
        return await self.client.users.create(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            **kwargs
        )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT access token
        
        Returns:
            Token payload dictionary
        
        Raises:
            ValueError: If token is invalid or secret_key not provided
        """
        # Secret key should always be available (auto-generated if not provided)
        if not self.client.secret_key:
            import secrets
            self.client.secret_key = secrets.token_urlsafe(32)
        
        from apex.core.security.jwt import decode_token
        
        try:
            payload = decode_token(token, secret_key=self.client.secret_key)
            return payload
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token string
        
        Returns:
            Dictionary with new access_token and token_type
        
        Raises:
            ValueError: If refresh token is invalid or secret_key not provided
        """
        # Secret key should always be available (auto-generated if not provided)
        if not self.client.secret_key:
            import secrets
            self.client.secret_key = secrets.token_urlsafe(32)
        
        async with self.client.get_session() as session:
            auth_service = AuthService(
                session=session,
                user_model=self.user_model,
                secret_key=self.client.secret_key
            )
            
            tokens = await auth_service.refresh_access_token(refresh_token)
            if not tokens:
                raise ValueError("Invalid or expired refresh token")
            
            return tokens


