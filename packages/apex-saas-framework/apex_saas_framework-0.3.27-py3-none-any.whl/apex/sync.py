"""
Synchronous convenience wrappers for the async Client API.

These helpers run coroutines via asyncio.run(), so they are intended for
scripts/CLIs or non-async frameworks. In an already-async app (e.g., FastAPI
endpoints), you should keep using `await` to avoid blocking the event loop.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from apex.core.exceptions import (
    ApexError,
    AuthenticationError,
    ClientError,
    ConflictError,
    DatabaseError,
    ValidationError,
)
from apex.core.validation import validate_email, validate_password
from apex.core.db_errors import handle_database_error

# Lazy import to avoid circular dependency
def _get_client_type():
    from apex.client import Client
    return Client

_default_client: Optional[Any] = None


def set_default_client(client: Any) -> None:
    """Set a default client so wrappers can be used without passing a client each time."""
    global _default_client
    _default_client = client


def _client(client: Optional[Any]) -> Any:
    if client is not None:
        return client
    if _default_client is None:
        raise ClientError(
            "No client provided and no default client set. "
            "Call set_default_client(client) or pass client parameter.",
            details={"hint": "client = Client(database_url='...', user_model=User)"},
        )
    return _default_client


def _run(coro):
    """Run a coroutine in a single persistent event loop."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # No event loop in current thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        return asyncio.run(coro)
    try:
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except Exception as e:
        logging.error(f"Error running coroutine: {e}", exc_info=True)
        raise


# Lifecycle / setup
def bootstrap(client: Optional[Any] = None, models: Optional[list[type]] = None) -> None:
    """Create tables for the provided models (or the client's registered models)."""
    c = _client(client)
    return _run(c.init_database(models=models))


# Auth
def signup(client: Optional[Any] = None, **kwargs) -> Any:
    """
    Signup a user.
    Validates only email/password; all other required fields are controlled by the user's model.
    """
    try:
        if "email" in kwargs:
            kwargs["email"] = validate_email(kwargs["email"])
        if "password" in kwargs:
            kwargs["password"] = validate_password(kwargs["password"])

        c = _client(client)
        return _run(c.auth.signup(**kwargs))

    except ValidationError:
        raise
    except IntegrityError as e:
        # handle known duplicates; otherwise bubble meaningful database error
        err = handle_database_error(e, context="signup")
        raise err
    except SQLAlchemyError as e:
        raise DatabaseError(f"Database error: {str(e)}", details={"original_error": str(e)})
    except Exception as e:
        logging.error(f"Unexpected error in signup: {e}", exc_info=True)
        raise ApexError(f"Signup failed: {str(e)}", details={"original_error": str(e)})


def login(client: Optional[Any] = None, **kwargs) -> dict[str, Any]:
    """
    Login user.
    Validates only email; user's model controls other requirements.
    """
    try:
        if "email" in kwargs:
            kwargs["email"] = validate_email(kwargs["email"])
        if "password" not in kwargs or not kwargs["password"]:
            raise ValidationError("Password is required")

        c = _client(client)
        result = _run(c.auth.login(**kwargs))

        if not result:
            raise AuthenticationError("Invalid email or password")

        return result

    except (ValidationError, AuthenticationError):
        raise
    except Exception as e:
        logging.error(f"Error in login: {e}", exc_info=True)
        raise AuthenticationError(f"Login failed: {str(e)}")


def verify_token(token: str, client: Optional[Any] = None) -> dict[str, Any]:
    c = _client(client)
    return _run(c.auth.verify_token(token))


def refresh_token(refresh_token: str, client: Optional[Any] = None) -> dict[str, Any]:
    c = _client(client)
    return _run(c.auth.refresh_token(refresh_token))


# Users
def create_user(client: Optional[Any] = None, **kwargs) -> Any:
    c = _client(client)
    return _run(c.users.create(**kwargs))


def get_user(client: Optional[Any] = None, user_id: Any = None, email: Optional[str] = None) -> Any:
    c = _client(client)
    return _run(c.users.get(user_id=user_id, email=email))


def update_user(client: Optional[Any] = None, user_id: Any = None, **kwargs) -> Any:
    c = _client(client)
    return _run(c.users.update(user_id=user_id, **kwargs))


def delete_user(client: Optional[Any] = None, user_id: Any = None) -> bool:
    c = _client(client)
    return _run(c.users.delete(user_id=user_id))


# Organizations (optional)
def create_organization(client: Optional[Any] = None, **kwargs) -> Any:
    c = _client(client)
    if c.organization_model is None:
        raise RuntimeError("organization_model not set on client. Initialize Client with organization_model parameter.")
    if c.organizations is None:
        raise RuntimeError("Organizations resource not available. Initialize Client with organization_model parameter.")
    return _run(c.organizations.create(**kwargs))


def get_organization(client: Optional[Any] = None, org_id: Any = None) -> Any:
    c = _client(client)
    if c.organization_model is None:
        raise RuntimeError("organization_model not set on client. Initialize Client with organization_model parameter.")
    if c.organizations is None:
        raise RuntimeError("Organizations resource not available. Initialize Client with organization_model parameter.")
    return _run(c.organizations.get(org_id))


def list_organizations(client: Optional[Any] = None) -> list[Any]:
    c = _client(client)
    if c.organization_model is None:
        raise RuntimeError("organization_model not set on client. Initialize Client with organization_model parameter.")
    if c.organizations is None:
        raise RuntimeError("Organizations resource not available. Initialize Client with organization_model parameter.")
    return _run(c.organizations.list())


# Password Reset
def forgot_password(client: Optional[Any] = None, email: Optional[str] = None) -> tuple[Any, str | None]:
    """
    Request password reset for a user.
    Automatically uses SendGrid if configured in .env to send email, otherwise returns token without sending email.
    
    Returns:
        Tuple of (user, reset_token) if user found, (None, None) otherwise
    """
    c = _client(client)
    async def _forgot_password():
        async with c.get_session() as session:
            # Try to use SendGrid email service if available
            try:
                from apex.domain.services.password_reset_sendgrid import PasswordResetWithEmailService
                from apex.infrastructure.email.sendgrid import SendGridEmailAdapter
                
                # Use email adapter from client if available, otherwise create new one
                email_adapter = None
                if hasattr(c, 'email') and hasattr(c.email, 'adapter') and c.email.adapter.enabled:
                    email_adapter = c.email.adapter
                else:
                    email_adapter = SendGridEmailAdapter()
                
                # Use SendGrid service if email is enabled
                if email_adapter and email_adapter.enabled:
                    reset_service = PasswordResetWithEmailService(
                        session=session,
                        user_model=c.user_model,
                        email_adapter=email_adapter
                    )
                    # This sends email and returns bool, but we need to get the token for return value
                    success = await reset_service.request_password_reset(email)
                    if success:
                        # Get the user and token from database
                        from apex.domain.services.password_reset import PasswordResetService
                        basic_service = PasswordResetService(session=session, user_model=c.user_model)
                        # Get user first to check if exists
                        from apex.domain.services.user import UserService
                        user_service = UserService(session=session, user_model=c.user_model)
                        user = await user_service.get_user_by_email(email)
                        if user and user.reset_token:
                            await session.commit()
                            return user, user.reset_token
                    return None, None
            except Exception as e:
                # Fall back to basic service if SendGrid fails
                import warnings
                warnings.warn(f"SendGrid email not available, using basic password reset: {str(e)}")
            
            # Fallback to basic password reset service (no email sent)
            from apex.domain.services.password_reset import PasswordResetService
            reset_service = PasswordResetService(session=session, user_model=c.user_model)
            user, reset_token = await reset_service.request_password_reset(email)
            await session.commit()
            return user, reset_token
    return _run(_forgot_password())


def reset_password(client: Optional[Any] = None, token: Optional[str] = None, new_password: Optional[str] = None) -> bool:
    """
    Reset user password using reset token.
    
    Returns:
        True if password was reset successfully, False otherwise
    """
    c = _client(client)
    async def _reset_password():
        async with c.get_session() as session:
            from apex.domain.services.password_reset import PasswordResetService
            reset_service = PasswordResetService(session=session, user_model=c.user_model)
            success = await reset_service.reset_password(token, new_password)
            await session.commit()
            return success
    return _run(_reset_password())


def change_password(client: Optional[Any] = None, user_id: Optional[Any] = None, old_password: Optional[str] = None, new_password: Optional[str] = None) -> bool:
    """
    Change user password (authenticated).
    
    Returns:
        True if password changed, False if old password incorrect
    """
    c = _client(client)
    return _run(c.users.change_password(user_id=user_id, old_password=old_password, new_password=new_password))


# Email
def send_email(
    client: Optional[Any] = None,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    html: Optional[str] = None,
) -> bool:
    """
    Send an email via SendGrid (if configured in .env).
    
    Args:
        client: Optional client instance (uses default if not provided)
        to: Recipient email address
        subject: Email subject
        body: Plain text body
        html: HTML body (optional)
    
    Returns:
        True if sent successfully, False otherwise
    
    Example:
        from apex import send_email
        success = send_email(to="user@example.com", subject="Hello", body="Welcome!")
    """
    c = _client(client)
    return _run(c.email.send(to=to, subject=subject, body=body, html=html))


def send_bulk_email(
    client: Optional[Any] = None,
    to: Optional[list[str]] = None,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    html: Optional[str] = None,
) -> bool:
    """
    Send email to multiple recipients via SendGrid (if configured in .env).
    
    Args:
        client: Optional client instance (uses default if not provided)
        to: List of recipient email addresses
        subject: Email subject
        body: Plain text body
        html: HTML body (optional)
    
    Returns:
        True if all emails sent successfully, False otherwise
    
    Example:
        from apex import send_bulk_email
        success = send_bulk_email(
            to=["user1@example.com", "user2@example.com"],
            subject="Newsletter",
            body="Check out our updates"
        )
    """
    c = _client(client)
    return _run(c.email.send_bulk(to=to, subject=subject, body=body, html=html))


