"""Password reset schemas."""

from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""

    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Schema for change password request.

    Note: Email is optional - if not provided, uses authenticated user from JWT token.
    """

    email: EmailStr | None = None  # Optional - uses JWT token user if not provided
    old_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""

    message: str
    success: bool

