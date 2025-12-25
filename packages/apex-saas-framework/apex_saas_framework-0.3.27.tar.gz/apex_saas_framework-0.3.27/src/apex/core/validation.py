"""
Input validation helpers.

Only validate fields the package itself depends on (e.g., auth).
User-defined models control their own required fields.
"""

from apex.core.exceptions import ValidationError


def validate_email(email: str) -> str:
    """Validate email format (minimal checks)."""
    if not isinstance(email, str):
        raise ValidationError("Email must be a string")

    email = email.strip().lower()

    if not email:
        raise ValidationError("Email is required")

    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError(f"Invalid email format: {email}")

    if len(email) > 255:
        raise ValidationError("Email must be 255 characters or less")

    return email


def validate_password(password: str, min_length: int = 8) -> str:
    """Validate password length (strength checks are user-controlled)."""
    if not isinstance(password, str):
        raise ValidationError("Password must be a string")

    if len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters")

    return password


def validate_positive_number(value, field_name: str):
    """Validate positive numeric values (for payments, etc.)."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{field_name} must be a number")
    if value <= 0:
        raise ValidationError(f"{field_name} must be positive (got {value})")
    return value


def validate_string(value: str, field_name: str, min_length: int = 0, max_length: int | None = None) -> str:
    """Validate string length bounds."""
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string")
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    if max_length is not None and len(value) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters")
    return value.strip()


__all__ = [
    "validate_email",
    "validate_password",
    "validate_positive_number",
    "validate_string",
]







