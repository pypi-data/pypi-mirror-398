"""Authentication service."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.security import create_access_token, create_refresh_token, verify_password
from typing import Any, Type, Optional


class AuthService:
    """
    Authentication service for handling login, registration, and token management.

    This is a base implementation. Users should extend this to work with their
    specific User model.
    """

    def __init__(self, session: AsyncSession, user_model: Type[Any], secret_key: Optional[str] = None):
        """
        Initialize auth service.
        
        Args:
            session: Database session
            user_model: User model class (can be any SQLAlchemy model - your choice!)
            secret_key: Optional secret key for JWT (uses settings or auto-generates if not provided)
        """
        self.session = session
        self.user_model = user_model
        self.secret_key = secret_key

    async def authenticate_user(self, email: str, password: str) -> Any | None:
        """
        Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User instance if authentication succeeds, None otherwise
        """
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Check is_active if it exists (optional field)
        if hasattr(user, "is_active") and not user.is_active:
            return None

        return user

    async def create_tokens(self, user: Any) -> dict[str, Any]:
        """
        Create access and refresh tokens for a user.
        Works with any primary key type (Integer, String, UUID, etc.).

        Args:
            user: User instance

        Returns:
            Dictionary with access_token and refresh_token
        """
        from apex.core.utils import get_primary_key_column
        
        # Get primary key value (works with any type)
        pk_column_name = get_primary_key_column(type(user))
        user_id = getattr(user, pk_column_name)
        
        # Get organization_id if it exists (user may have different field name)
        org_id = None
        if hasattr(user, "organization_id"):
            org_id = getattr(user, "organization_id")
        elif hasattr(user, "org_id"):
            org_id = getattr(user, "org_id")
        elif hasattr(user, "company_id"):
            org_id = getattr(user, "company_id")
        
        token_data = {
            "sub": str(user_id),  # Convert to string (works with any type)
            "email": user.email,
            "is_active": getattr(user, "is_active", True),
            "is_superuser": getattr(user, "is_superuser", False),
            "is_org_admin": getattr(user, "is_org_admin", False),
            "organization_id": str(org_id) if org_id else None,
        }

        access_token = create_access_token(data=token_data, secret_key=self.secret_key)
        refresh_token = create_refresh_token(data=token_data, secret_key=self.secret_key)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def refresh_access_token(self, refresh_token: str) -> dict[str, Any] | None:
        """
        Create a new access token from a refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            Dictionary with new access_token or None if refresh token is invalid
        """
        from apex.core.security.jwt import decode_token

        try:
            payload = decode_token(refresh_token, secret_key=self.secret_key)
            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            if not user_id:
                return None

            # Get primary key column and type
            from apex.core.utils import get_primary_key_column, get_primary_key_type, convert_id_to_type
            
            pk_column_name = get_primary_key_column(self.user_model)
            pk_column = getattr(self.user_model, pk_column_name)
            pk_type = get_primary_key_type(self.user_model)
            converted_id = convert_id_to_type(user_id, pk_type)

            # Verify user still exists and is active
            result = await self.session.execute(
                select(self.user_model).where(pk_column == converted_id)
            )
            user = result.scalar_one_or_none()

            if not user or (hasattr(user, "is_active") and not user.is_active):
                return None

            # Get primary key value
            pk_column_name = get_primary_key_column(self.user_model)
            user_id = getattr(user, pk_column_name)
            
            # Get organization_id if it exists
            org_id = None
            if hasattr(user, "organization_id"):
                org_id = getattr(user, "organization_id")
            elif hasattr(user, "org_id"):
                org_id = getattr(user, "org_id")
            elif hasattr(user, "company_id"):
                org_id = getattr(user, "company_id")
            
            # Create new access token
            token_data = {
                "sub": str(user_id),
                "email": user.email,
                "is_active": getattr(user, "is_active", True),
                "is_superuser": getattr(user, "is_superuser", False),
                "organization_id": str(org_id) if org_id else None,
            }

            access_token = create_access_token(data=token_data, secret_key=self.secret_key)

            return {
                "access_token": access_token,
                "token_type": "bearer",
            }

        except Exception:
            return None

