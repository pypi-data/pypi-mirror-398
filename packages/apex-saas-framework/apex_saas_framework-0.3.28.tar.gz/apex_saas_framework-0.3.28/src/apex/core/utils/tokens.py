"""Token generation and verification utilities."""

import secrets
from datetime import datetime, timedelta


def generate_reset_token() -> tuple[str, str]:
    """
    Generate a password reset token.

    Returns:
        Tuple of (token, expiry_timestamp)
    """
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    return token, expiry.isoformat()


def verify_reset_token(token: str, stored_token: str, expiry: str) -> bool:
    """
    Verify a password reset token.

    Args:
        token: Token from request
        stored_token: Token stored in database
        expiry: Expiry timestamp (ISO format)

    Returns:
        True if token is valid and not expired
    """
    if not token or not stored_token or token != stored_token:
        return False

    try:
        expiry_dt = datetime.fromisoformat(expiry)
        if datetime.utcnow() > expiry_dt:
            return False
        return True
    except (ValueError, TypeError):
        return False

