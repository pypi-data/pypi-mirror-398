"""JWT token creation and verification utilities."""

from datetime import datetime, timedelta
from typing import Any, Optional

from jose import JWTError, jwt

from apex.core.config import get_settings

settings = get_settings()


def _get_secret_key(secret_key: Optional[str] = None) -> str:
    """Get secret key from parameter, settings, or auto-generate."""
    if secret_key:
        return secret_key
    
    # Check settings
    if hasattr(settings, 'SECRET_KEY') and settings.SECRET_KEY and settings.SECRET_KEY != "change-this-secret-key-in-production":
        return settings.SECRET_KEY
    
    # Auto-generate (this should rarely happen as Client generates it)
    import secrets
    return secrets.token_urlsafe(32)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None, secret_key: Optional[str] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: The data to encode in the token (typically user_id, email, etc.)
        expires_delta: Optional custom expiration time. Defaults to settings.ACCESS_TOKEN_EXPIRE_MINUTES
        secret_key: Optional secret key (uses settings or auto-generates if not provided)

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "type": "access"})
    key = _get_secret_key(secret_key)
    encoded_jwt = jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], secret_key: Optional[str] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: The data to encode in the token
        secret_key: Optional secret key (uses settings or auto-generates if not provided)

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    key = _get_secret_key(secret_key)
    encoded_jwt = jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str, secret_key: Optional[str] = None) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: The JWT token string to decode
        secret_key: Optional secret key (uses settings or auto-generates if not provided)

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        key = _get_secret_key(secret_key)
        payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}") from e

