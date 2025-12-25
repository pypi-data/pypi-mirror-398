"""Password reset service."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.security import get_password_hash
from apex.core.utils.tokens import generate_reset_token, verify_reset_token
from apex.domain.models.user import BaseUser


class PasswordResetService:
    """
    Service for handling password reset flows.

    This is a base implementation. Users should extend this to work with their
    specific User model and email service.
    """

    def __init__(self, session: AsyncSession, user_model: type[BaseUser]):
        """
        Initialize password reset service.

        Args:
            session: Database session
            user_model: User model class
        """
        self.session = session
        self.user_model = user_model

    async def request_password_reset(self, email: str) -> tuple[BaseUser | None, str | None]:
        """
        Request a password reset for a user.

        Args:
            email: User email address

        Returns:
            Tuple of (user, reset_token) if user found, (None, None) otherwise
        """
        # Find user by email
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None, None

        # Generate reset token
        token, expiry = generate_reset_token()

        # Store token in database
        user.reset_token = token
        user.reset_token_expires = expiry

        await self.session.flush()

        return user, token

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.

        Args:
            token: Reset token
            new_password: New password

        Returns:
            True if password was reset successfully, False otherwise
        """
        # Find user by reset token
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.reset_token == token)
        )
        user = result.scalar_one_or_none()

        if not user or not user.reset_token_expires:
            return False

        # Verify token is valid and not expired
        if not verify_reset_token(token, user.reset_token, user.reset_token_expires):
            return False

        # Update password
        user.password_hash = get_password_hash(new_password)

        # Clear reset token
        user.reset_token = None
        user.reset_token_expires = None

        await self.session.flush()

        return True

    async def verify_reset_token_valid(self, token: str) -> bool:
        """
        Verify if a reset token is valid.

        Args:
            token: Reset token

        Returns:
            True if token is valid and not expired
        """
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.reset_token == token)
        )
        user = result.scalar_one_or_none()

        if not user or not user.reset_token_expires:
            return False

        return verify_reset_token(token, user.reset_token, user.reset_token_expires)

