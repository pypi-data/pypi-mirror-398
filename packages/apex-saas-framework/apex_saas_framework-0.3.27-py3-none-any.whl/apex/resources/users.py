"""
Users Resource - Clerk-style user management
"""
from typing import Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from apex.client import Client
from apex.domain.services.user import UserService


class Users:
    """
    Users resource - provides user management methods
    
    Usage:
        async with client:
            # Create user
            user = await client.users.create(
                email="user@example.com",
                password="password123",
                first_name="John",
                last_name="Doe"
            )
            
            # Get user
            user = await client.users.get(email="user@example.com")
            
            # Update user
            user = await client.users.update(
                user_id=str(user.id),
                first_name="Jane"
            )
            
            # Delete user
            await client.users.delete(user_id=str(user.id))
    """
    
    def __init__(self, client: Client, user_model: Optional[Type[Any]] = None):
        """
        Initialize Users resource.
        
        Args:
            client: Apex client instance
            user_model: User model class (can be any SQLAlchemy model - your choice!)
        """
        self.client = client
        self.user_model = user_model
    
    async def create(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        country: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Create a new user.
        
        Args:
            email: User email (required)
            password: User password (will be hashed)
            first_name: First name
            last_name: Last name
            phone: Phone number
            country: Country
            **kwargs: Additional user fields (based on your model)
        
        Returns:
            Created user instance
        
        Raises:
            ValueError: If user already exists
        """
        from sqlalchemy.exc import IntegrityError
        
        async with self.client.get_session() as session:
            user_service = UserService(session=session, user_model=self.user_model)
            
            # Check if user exists by email
            existing = await user_service.get_user_by_email(email)
            if existing:
                raise ValueError(f"User with email {email} already exists")
            
            # Check if username exists (if username is provided)
            if 'username' in kwargs and kwargs['username']:
                existing_username = await user_service.get_user_by_username(kwargs['username'])
                if existing_username:
                    raise ValueError(f"Username '{kwargs['username']}' already exists. Please choose another username.")
            
            try:
                # Create user
                user = await user_service.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    country=country,
                    **kwargs
                )
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError as e:
                await session.rollback()
                error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
                
                # Check for specific constraint violations
                if "username" in error_str and ("unique" in error_str or "duplicate" in error_str):
                    username = kwargs.get('username', 'provided')
                    raise ValueError(f"Username '{username}' already exists. Please choose another username.")
                elif "email" in error_str and ("unique" in error_str or "duplicate" in error_str):
                    raise ValueError(f"User with email {email} already exists.")
                else:
                    raise ValueError(f"Failed to create user: {str(e)}")
    
    async def get(
        self,
        user_id: Optional[Any] = None,
        email: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get user by ID or email.
        
        Args:
            user_id: User ID (can be int, str, UUID, etc. - depends on your model's primary key)
            email: User email
        
        Returns:
            User instance or None if not found
        
        Raises:
            ValueError: If neither user_id nor email is provided
        """
        if not user_id and not email:
            raise ValueError("Must provide either user_id or email")
        
        async with self.client.get_session() as session:
            user_service = UserService(session=session, user_model=self.user_model)
            
            if user_id:
                return await user_service.get_user_by_id(user_id)
            if email:
                return await user_service.get_user_by_email(email)
            
            return None
    
    async def update(self, user_id: Any, **kwargs) -> Any:
        """
        Update user fields.
        
        Args:
            user_id: User UUID
            **kwargs: Fields to update (password will be hashed automatically)
        
        Returns:
            Updated user instance
        
        Raises:
            ValueError: If user not found
        """
        async with self.client.get_session() as session:
            user_service = UserService(session=session, user_model=self.user_model)
            
            user = await user_service.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            updated_user = await user_service.update_user(user, **kwargs)
            await session.commit()
            await session.refresh(updated_user)
            return updated_user
    
    async def delete(self, user_id: Any) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User UUID
        
        Returns:
            True if deleted, False if not found
        """
        async with self.client.get_session() as session:
            user_service = UserService(session=session, user_model=self.user_model)
            
            user = await user_service.get_user_by_id(user_id)
            if not user:
                return False
            
            await session.delete(user)
            await session.commit()
            return True
    
    async def change_password(
        self,
        user_id: Any,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User UUID
            old_password: Current password
            new_password: New password
        
        Returns:
            True if password changed, False if old password incorrect
        """
        async with self.client.get_session() as session:
            user_service = UserService(session=session, user_model=self.user_model)
            
            user = await user_service.get_user_by_id(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")
            
            success = await user_service.change_password(user, old_password, new_password)
            if success:
                await session.commit()
            return success


