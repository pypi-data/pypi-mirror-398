"""Authentication schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserRegister(BaseModel):
    """Schema for user registration.
    
    Regular user signup - does NOT create organizations.
    Users can join existing organizations later.
    """

    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, description="Username is required and must be at least 3 characters")
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    country_code: str | None = Field(None, max_length=10, description="ISO country code (e.g., US, IN, GB)")
    # Removed organization_name - users don't create orgs during signup
    
    # Consent checkboxes
    accept_terms: bool = Field(..., description="Must accept Terms and Conditions and Privacy Policy")
    newsletter_consent: bool = Field(False, description="Consent to receive newsletters and updates")

    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self
    
    @model_validator(mode='after')
    def validate_terms_acceptance(self):
        """Validate that terms are accepted."""
        if not self.accept_terms:
            raise ValueError('You must accept the Terms and Conditions and Privacy Policy')
        return self

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        """Validate phone number format (basic E.164 check)."""
        if v is None:
            return v
        
        # Remove common formatting characters
        cleaned = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Basic E.164 validation: should start with + and contain only digits after
        if cleaned.startswith("+"):
            digits = cleaned[1:]
            if not digits.isdigit():
                raise ValueError("Phone number must contain only digits after the + prefix")
            if len(digits) < 7 or len(digits) > 15:
                raise ValueError("Phone number must be between 7 and 15 digits (E.164 format)")
        else:
            # If no +, just check it's digits and reasonable length
            if not cleaned.isdigit():
                raise ValueError("Phone number must contain only digits or start with +")
            if len(cleaned) < 7 or len(cleaned) > 15:
                raise ValueError("Phone number must be between 7 and 15 digits")
        
        return v
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Validate username format."""
        if v is None:
            return v
        
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters long")
        
        # Allow alphanumeric, underscore, and hyphen
        if not all(c.isalnum() or c in "_-" for c in v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        
        return v


class SignupResponse(BaseModel):
    """Schema for signup response."""

    success: bool
    message: str
    user_id: UUID
    email: EmailStr
    username: str | None = None


class LoginResponse(BaseModel):
    """Schema for login response with JWT tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID | None = None


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema for logout requests."""

    email: EmailStr


class LogoutResponse(BaseModel):
    """Schema for logout responses."""

    success: bool
    message: str


class AdminSignupRequest(BaseModel):
    """Schema for admin signup request.
    
    Admin users do NOT belong to any organization (organization_id = NULL).
    This allows them to see and manage ALL organizations.
    """
    
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3)
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    country_code: str | None = Field(None, max_length=10)
    # Removed organization_name - admins don't belong to organizations
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self


class OrganizationSignupRequest(BaseModel):
    """Schema for organization signup request.
    
    Creates an organization and the first user (organization owner).
    This is the organization-first signup flow.
    """
    
    # Organization details
    organization_name: str = Field(..., min_length=1, description="Organization name is required")
    organization_slug: str | None = None
    organization_description: str | None = None
    organization_settings: dict | None = None
    organization_modules: dict | None = None
    
    # User details (organization owner/admin)
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3)
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    country_code: str | None = Field(None, max_length=10)
    
    # Consent checkboxes
    accept_terms: bool = Field(..., description="Must accept Terms and Conditions and Privacy Policy")
    newsletter_consent: bool = Field(False, description="Consent to receive newsletters and updates")
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self
    
    @model_validator(mode='after')
    def validate_terms_acceptance(self):
        """Validate that terms are accepted."""
        if not self.accept_terms:
            raise ValueError('You must accept the Terms and Conditions and Privacy Policy')
        return self


class OrganizationSignupResponse(BaseModel):
    """Schema for organization signup response."""
    
    success: bool
    message: str
    organization_id: UUID
    organization_name: str
    user_id: UUID
    email: EmailStr
    username: str | None = None


class OrganizationAdminSignupRequest(BaseModel):
    """Schema for organization admin signup request.
    
    Creates an organization and the first user (organization admin).
    Organization admin has full CRUD access and permission management within their organization.
    """
    
    # Organization details
    organization_name: str = Field(..., min_length=1, description="Organization name is required")
    organization_slug: str | None = None
    organization_description: str | None = None
    organization_settings: dict | None = None
    organization_modules: dict | None = None
    
    # User details (organization admin)
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3)
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    country: str | None = None
    country_code: str | None = Field(None, max_length=10)
    
    @model_validator(mode='after')
    def passwords_match(self):
        """Validate that password and password_confirm match."""
        if self.password != self.password_confirm:
            raise ValueError('Passwords do not match')
        return self


class OrganizationAdminSignupResponse(BaseModel):
    """Schema for organization admin signup response."""
    
    success: bool
    message: str
    organization_id: UUID
    organization_name: str
    user_id: UUID
    email: EmailStr
    username: str | None = None
    is_org_admin: bool = True

