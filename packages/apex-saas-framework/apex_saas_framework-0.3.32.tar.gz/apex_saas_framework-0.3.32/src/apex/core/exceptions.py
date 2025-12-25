"""
Centralized Apex exception hierarchy.
"""

class ApexError(Exception):
    """Base exception for all Apex errors."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ValidationError(ApexError):
    """Input validation error."""


class AuthenticationError(ApexError):
    """Authentication failure."""


class AuthorizationError(ApexError):
    """Authorization/permission failure."""


class NotFoundError(ApexError):
    """Resource not found."""


class ConflictError(ApexError):
    """Resource conflict (e.g., duplicate)."""


class DatabaseError(ApexError):
    """Database operation error."""


class ConfigurationError(ApexError):
    """Configuration/setup error."""


class ExternalServiceError(ApexError):
    """External service error (PayPal, SendGrid, etc.)."""


class ClientError(ApexError):
    """Client initialization/usage error."""


__all__ = [
    "ApexError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "DatabaseError",
    "ConfigurationError",
    "ExternalServiceError",
    "ClientError",
]







