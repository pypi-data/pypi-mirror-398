"""Password reset service with SendGrid email integration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apex.core.config import get_settings
from apex.core.security import get_password_hash
from apex.core.utils.tokens import generate_reset_token, verify_reset_token
from apex.domain.models.user import BaseUser
from apex.infrastructure.email.sendgrid import SendGridEmailAdapter
from apex.infrastructure.email.templates import password_reset_email_template

settings = get_settings()


class PasswordResetWithEmailService:
    """
    Password reset service with email sending.

    Integrates SendGrid for sending password reset emails.
    """

    def __init__(
        self,
        session: AsyncSession,
        user_model: type[BaseUser],
        email_adapter: SendGridEmailAdapter | None = None,
    ):
        """
        Initialize password reset service.

        Args:
            session: Database session
            user_model: User model class
            email_adapter: Email adapter (creates SendGrid if not provided)
        """
        self.session = session
        self.user_model = user_model
        self.email_adapter = email_adapter or SendGridEmailAdapter()

    async def request_password_reset(self, email: str) -> bool:
        """
        Request a password reset and send email.

        Args:
            email: User email address

        Returns:
            Always returns True to prevent email enumeration attacks
        """
        # Find user by email
        result = await self.session.execute(
            select(self.user_model).where(self.user_model.email == email)
        )
        user = result.scalar_one_or_none()

        # Always return True (security: prevent email enumeration)
        if not user:
            return True

        # Generate reset token
        token, expiry = generate_reset_token()

        # Store token in database
        user.reset_token = token
        user.reset_token_expires = expiry
        await self.session.commit()

        # Build reset link using FRONTEND_RESET_URL
        reset_link = f"{settings.FRONTEND_RESET_URL}?token={token}"

        # Get user name (use first_name or extract from email)
        user_name = user.first_name or user.email.split("@")[0]

        # Generate email content from template
        subject, html_body = password_reset_email_template(user_name, reset_link)

        # Send email via SendGrid
        try:
            await self.email_adapter.send_email(
                to=user.email,
                subject=subject,
                body=f"Reset your password: {reset_link}",
                html=html_body,
            )
        except Exception as e:
            # Log error but don't expose it to user
            print(f"Failed to send reset email: {str(e)}")
            # Continue anyway - don't reveal error to prevent enumeration

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.

        Args:
            token: Reset token from email
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
        user.hashed_password = get_password_hash(new_password)

        # Clear reset token
        user.reset_token = None
        user.reset_token_expires = None

        await self.session.commit()

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

