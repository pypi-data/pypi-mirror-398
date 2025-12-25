"""
Security utilities for database migrations - Input validation and sanitization.
"""

import re
from typing import Optional
from urllib.parse import urlparse, quote, unquote


def validate_database_url(url: str) -> bool:
    """
    Validate database URL format and security.
    
    Supports localhost, 127.0.0.1, and remote hosts.
    
    Args:
        url: Database URL string
    
    Returns:
        True if valid, raises ValueError if invalid
    
    Raises:
        ValueError: If URL is invalid or contains suspicious patterns
    """
    if not url or not isinstance(url, str):
        raise ValueError("Database URL must be a non-empty string")
    
    # Check for suspicious patterns (basic SQL injection attempts)
    suspicious_patterns = [
        r';\s*(drop|delete|truncate|alter|create|insert|update)',
        r'union\s+select',
        r'exec\s*\(',
        r'xp_\w+',
        r'--',
        r'/\*',
    ]
    
    url_lower = url.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, url_lower, re.IGNORECASE):
            raise ValueError(f"Database URL contains suspicious pattern: {pattern}")
    
    # Validate URL structure
    try:
        parsed = urlparse(url)
        if not parsed.scheme:
            raise ValueError("Database URL must have a scheme (e.g., postgresql://, mysql://, sqlite://)")
        
        # Accept localhost, 127.0.0.1, and any valid hostname/IP
        # For SQLite, hostname might be empty (file path)
        if parsed.scheme not in ['sqlite', 'sqlite+aiosqlite']:
            if not parsed.hostname and not parsed.path:
                raise ValueError("Database URL must have a hostname (e.g., localhost, 127.0.0.1) or file path")
        
        # Validate common localhost formats
        if parsed.hostname:
            valid_hosts = ['localhost', '127.0.0.1', '::1', '0.0.0.0']
            if parsed.hostname.lower() not in valid_hosts:
                # Allow any other hostname (remote connections)
                # Basic validation: should not contain spaces or special SQL chars
                if ' ' in parsed.hostname or ';' in parsed.hostname:
                    raise ValueError("Hostname contains invalid characters")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Invalid database URL format: {str(e)}")
    
    return True


def sanitize_database_url(url: str) -> str:
    """
    Sanitize database URL by encoding special characters properly.
    
    Supports localhost, 127.0.0.1, and remote hosts.
    
    Args:
        url: Database URL string
    
    Returns:
        Sanitized URL string
    """
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        
        # For SQLite, return as-is (file path, no hostname)
        if parsed.scheme in ['sqlite', 'sqlite+aiosqlite']:
            return url
        
        # Encode username and password if present
        if parsed.username:
            username = quote(unquote(parsed.username), safe='')
        else:
            username = None
        
        if parsed.password:
            password = quote(unquote(parsed.password), safe='')
        else:
            password = None
        
        # Preserve hostname (localhost, 127.0.0.1, or remote)
        hostname = parsed.hostname or "localhost"
        
        # Reconstruct URL with encoded credentials
        if username and password:
            netloc = f"{username}:{password}@{hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
        elif username:
            netloc = f"{username}@{hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
        else:
            netloc = hostname
            if parsed.port:
                netloc += f":{parsed.port}"
        
        # Reconstruct URL
        sanitized = f"{parsed.scheme}://{netloc}{parsed.path}"
        if parsed.query:
            sanitized += f"?{parsed.query}"
        if parsed.fragment:
            sanitized += f"#{parsed.fragment}"
        
        return sanitized
    except Exception:
        # If parsing fails, return original (will be caught by validation)
        return url


def mask_sensitive_url(url: str) -> str:
    """
    Mask sensitive information in database URL for logging.
    
    Args:
        url: Database URL string
    
    Returns:
        URL with password masked
    """
    if not url:
        return url
    
    try:
        parsed = urlparse(url)
        if parsed.password:
            # Replace password with asterisks
            netloc = parsed.netloc.replace(f":{parsed.password}", ":****")
            masked = url.replace(parsed.netloc, netloc)
            return masked
    except Exception:
        pass
    
    return url


__all__ = ["validate_database_url", "sanitize_database_url", "mask_sensitive_url"]

