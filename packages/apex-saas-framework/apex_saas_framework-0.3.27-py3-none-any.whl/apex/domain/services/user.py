"""User service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.security import get_password_hash
from typing import Any, Type


class UserService:
    """
    User service for managing user operations.

    This is a base implementation. Users should extend this to work with their
    specific User model.
    """

    def __init__(self, session: AsyncSession, user_model: Type[Any]):
        """
        Initialize user service.

        Args:
            session: Database session
            user_model: User model class (can be any SQLAlchemy model - your choice!)
        """
        self.session = session
        self.user_model = user_model

    async def get_user_by_email(self, email: str) -> Any | None:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: Any) -> Any | None:
        """
        Get user by ID - works with any primary key type (Integer, String, UUID, etc.).

        Args:
            user_id: User ID (can be int, str, UUID, etc. - depends on your model's primary key)

        Returns:
            User instance or None if not found
        """
        from apex.core.utils import get_primary_key_column, get_primary_key_type, convert_id_to_type
        
        # Get primary key column name (could be 'id', 'user_id', etc.)
        pk_column_name = get_primary_key_column(self.user_model)
        pk_column = getattr(self.user_model, pk_column_name)
        
        # Get primary key type and convert ID
        pk_type = get_primary_key_type(self.user_model)
        converted_id = convert_id_to_type(user_id, pk_type)
        
        # Query using the primary key
        result = await self.session.execute(
            select(self.user_model).where(pk_column == converted_id)
        )
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Any | None:
        """
        Get user by username.

        Args:
            username: User username

        Returns:
            User instance or None if not found
        """
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.username == username)
        )
        return result.scalar_one_or_none()

    async def generate_unique_username(self, base_username: str) -> str:
        """
        Generate a unique username by appending a number if needed.

        Args:
            base_username: Base username to make unique

        Returns:
            Unique username
        """
        username = base_username.lower().strip().replace(" ", "_")
        # Remove special characters except underscore and hyphen
        import re
        username = re.sub(r'[^a-z0-9_-]', '', username)
        
        # Check if base username is available
        existing = await self.get_user_by_username(username)
        if not existing:
            return username
        
        # Try appending numbers
        counter = 1
        while True:
            candidate = f"{username}{counter}"
            existing = await self.get_user_by_username(candidate)
            if not existing:
                return candidate
            counter += 1
            # Safety limit
            if counter > 10000:
                # Fallback: use timestamp
                import time
                return f"{username}_{int(time.time())}"

    async def create_user(self, **kwargs) -> Any:
        """
        Create a new user.

        Args:
            **kwargs: User field values (password will be hashed automatically)

        Returns:
            Created user instance
        """
        # Hash password if provided
        if "password" in kwargs:
            kwargs["password_hash"] = get_password_hash(kwargs.pop("password"))

        # Ensure hashed_password is set
        if "password_hash" not in kwargs:
            raise ValueError("Password is required")

        # Filter out fields that don't exist in the model
        # This allows users to define their own models with only the fields they need
        model_columns = {col.key for col in self.user_model.__table__.columns}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in model_columns}
        
        # Warn about ignored fields (optional - for debugging)
        ignored_fields = set(kwargs.keys()) - set(filtered_kwargs.keys())
        if ignored_fields:
            import warnings
            warnings.warn(
                f"Fields {ignored_fields} were ignored because they don't exist in the User model. "
                f"Available fields: {model_columns}",
                UserWarning
            )

        user = self.user_model(**filtered_kwargs)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def update_user(self, user: Any, **kwargs) -> Any:
        """
        Update user fields.

        Args:
            user: User instance to update
            **kwargs: Fields to update (password will be hashed automatically)

        Returns:
            Updated user instance
        """
        # Hash password if provided
        if "password" in kwargs:
            kwargs["password_hash"] = get_password_hash(kwargs.pop("password"))

        # Filter out fields that don't exist in the model
        model_columns = {col.key for col in self.user_model.__table__.columns}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in model_columns}
        
        # Warn about ignored fields (optional - for debugging)
        ignored_fields = set(kwargs.keys()) - set(filtered_kwargs.keys())
        if ignored_fields:
            import warnings
            warnings.warn(
                f"Fields {ignored_fields} were ignored because they don't exist in the User model. "
                f"Available fields: {model_columns}",
                UserWarning
            )

        for key, value in filtered_kwargs.items():
            setattr(user, key, value)

        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def change_password(self, user: Any, old_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user: User instance
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully, False if old password is incorrect
        """
        from apex.core.security import verify_password

        if not verify_password(old_password, user.password_hash):
            return False

        user.password_hash = get_password_hash(new_password)
        await self.session.flush()
        return True

