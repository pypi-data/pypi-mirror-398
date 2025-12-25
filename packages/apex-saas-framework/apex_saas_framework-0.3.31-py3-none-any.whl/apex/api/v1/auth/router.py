"""
Authentication router.

This is a base implementation that provides the structure for auth endpoints.
Users should extend this to work with their specific User model.
"""

from typing import Annotated
from uuid import UUID as UUIDType
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from apex.app.core.dependencies import get_organization_model, get_user_model
from apex.app.models import BaseOrganization
from apex.core.authentication.dependencies import get_current_active_user
from apex.api.v1.schemas.auth import (
    AdminSignupRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    OrganizationAdminSignupRequest,
    OrganizationAdminSignupResponse,
    OrganizationSignupRequest,
    OrganizationSignupResponse,
    RefreshTokenRequest,
    SignupResponse,
    UserLogin,
    UserRegister,
)
from apex.api.v1.schemas.user import UserResponse
from apex.api.v1.schemas.password_reset import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
)
from apex.domain.models.user import BaseUser
from apex.domain.services.auth import AuthService
from apex.domain.services.password_reset import PasswordResetService
from apex.domain.services.password_reset_sendgrid import PasswordResetWithEmailService
from apex.domain.services.user import UserService
from apex.infrastructure.database.session import get_db

router = APIRouter(tags=["Authentication"])


# Note: Users should override this dependency in their application
# Example:
# def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
#     from app.models import User
#     return AuthService(session=db, user_model=User)
#
# app.dependency_overrides[get_auth_service] = get_auth_service

def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    """
    Dependency to get auth service.

    This is a placeholder. Users MUST override this to provide their User model.
    See module docstring for example.
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Auth service not configured. Please override get_auth_service dependency with your User model.",
    )


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    """
    Dependency to get user service.

    Users MUST override this dependency to provide their concrete User model.
    """
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="User service not configured. Please override get_user_service dependency with your User model.",
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: UserRegister,
    user_service: UserService = Depends(get_user_service),
):
    """
    User signup endpoint.

    Creates a new user record WITHOUT creating organizations.
    Users can join existing organizations later or remain without an organization.
    """
    existing_user = await user_service.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    # Check if username already exists
    existing_username = await user_service.get_user_by_username(payload.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    # User signup does NOT create organizations
    # Users can join existing organizations later via a different endpoint
    organization_id: UUIDType | None = None

    # Security: Never auto-create superuser via signup
    # Use CLI command: apexfastapi create-superuser
    try:
        # Store consent in dedicated columns (GDPR compliance)
        accept_terms_date = datetime.utcnow().isoformat() if payload.accept_terms else None
        newsletter_consent_date = datetime.utcnow().isoformat() if payload.newsletter_consent else None
        
        user = await user_service.create_user(
            email=payload.email,
            password=payload.password,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            country=payload.country,
            country_code=payload.country_code,
            organization_id=organization_id,  # Always None for regular signup
            is_superuser=False,  # Security: Never auto-create superuser
            is_verified=False,   # Users verify via email or admin approval
            accept_terms=payload.accept_terms,
            accept_terms_date=accept_terms_date,
            newsletter_consent=payload.newsletter_consent,
            newsletter_consent_date=newsletter_consent_date,
        )

        await user_service.session.commit()
        await user_service.session.refresh(user)
        return SignupResponse(
            success=True,
            message="Signup successful",
            user_id=user.id,
            email=user.email,
            username=user.username,
        )
    except IntegrityError as e:
        await user_service.session.rollback()
        # Check for specific database integrity errors
        error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "email" in error_str or "ix_users_email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
        elif "username" in error_str or "ix_users_username" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this information already exists.",
            )
    except Exception as e:
        await user_service.session.rollback()
        # Re-raise other exceptions as 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during signup: {str(e)}",
        ) from e


@router.post("/organization-signup", response_model=OrganizationSignupResponse, status_code=status.HTTP_201_CREATED)
async def organization_signup(
    payload: OrganizationSignupRequest,
    user_service: UserService = Depends(get_user_service),
    organization_model: type[BaseOrganization] = Depends(get_organization_model),
):
    """
    Organization signup endpoint.
    
    Creates an organization and the first user (organization owner).
    This is the organization-first signup flow.
    
    Flow:
    1. Create organization
    2. Create user and link to organization
    3. Return organization and user details
    """
    from sqlalchemy import inspect as sa_inspect
    
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    # Check if username already exists
    existing_username = await user_service.get_user_by_username(payload.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    # Check if organization name already exists
    stmt = select(organization_model).where(organization_model.name == payload.organization_name)
    result = await user_service.session.execute(stmt)
    existing_org = result.scalar_one_or_none()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists.",
        )

    # Check if organization slug already exists (if provided and model supports it)
    if payload.organization_slug:
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        if "slug" in available_columns:
            stmt = select(organization_model).where(organization_model.slug == payload.organization_slug)
            result = await user_service.session.execute(stmt)
            existing_slug = result.scalar_one_or_none()
            if existing_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this slug already exists.",
                )

    try:
        # Step 1: Create organization
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        org_kwargs = {"name": payload.organization_name}
        
        # Add optional organization attributes if they exist as columns
        if "slug" in available_columns and payload.organization_slug:
            org_kwargs["slug"] = payload.organization_slug
        if "description" in available_columns and payload.organization_description:
            org_kwargs["description"] = payload.organization_description
        if "modules" in available_columns:
            org_kwargs["modules"] = payload.organization_modules or {}
        
        organization = organization_model(**org_kwargs)
        user_service.session.add(organization)
        await user_service.session.flush()
        await user_service.session.refresh(organization)
        
        # Step 2: Store consent in dedicated columns (GDPR compliance)
        accept_terms_date = datetime.utcnow().isoformat() if payload.accept_terms else None
        newsletter_consent_date = datetime.utcnow().isoformat() if payload.newsletter_consent else None
        
        # Step 3: Create user and link to organization
        user = await user_service.create_user(
            email=payload.email,
            password=payload.password,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            country=payload.country,
            country_code=payload.country_code,
            organization_id=organization.id,  # Link user to organization
            is_superuser=False,  # Regular user, not admin
            is_verified=False,   # Users verify via email or admin approval
            accept_terms=payload.accept_terms,
            accept_terms_date=accept_terms_date,
            newsletter_consent=payload.newsletter_consent,
            newsletter_consent_date=newsletter_consent_date,
        )

        await user_service.session.commit()
        await user_service.session.refresh(user)
        await user_service.session.refresh(organization)
        
        return OrganizationSignupResponse(
            success=True,
            message="Organization and user created successfully",
            organization_id=organization.id,
            organization_name=organization.name,
            user_id=user.id,
            email=user.email,
            username=user.username,
        )
    except IntegrityError as e:
        await user_service.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "email" in error_str or "ix_users_email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
        elif "username" in error_str or "ix_users_username" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )
        elif "organization" in error_str or "name" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during organization signup: {str(e)}",
        ) from e
    except Exception as e:
        await user_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during organization signup: {str(e)}",
        ) from e


@router.post("/organization-admin-signup", response_model=OrganizationAdminSignupResponse, status_code=status.HTTP_201_CREATED)
async def organization_admin_signup(
    payload: OrganizationAdminSignupRequest,
    user_service: UserService = Depends(get_user_service),
    organization_model: type[BaseOrganization] = Depends(get_organization_model),
):
    """
    Organization admin signup endpoint.
    
    Creates an organization and the first user (organization admin).
    Organization admin has full CRUD access, permission management, and can see
    all data/users within their organization.
    
    Flow:
    1. Create organization
    2. Create user with is_org_admin=True and link to organization
    3. Return organization and user details
    
    Organization Admin Privileges:
    - Full CRUD access to all resources in their organization
    - Manage permissions and roles for users in their organization
    - See all users and data within their organization
    - Cannot access other organizations' data
    """
    from sqlalchemy import inspect as sa_inspect
    
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    # Check if username already exists
    existing_username = await user_service.get_user_by_username(payload.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    # Check if organization name already exists
    stmt = select(organization_model).where(organization_model.name == payload.organization_name)
    result = await user_service.session.execute(stmt)
    existing_org = result.scalar_one_or_none()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this name already exists.",
        )

    # Check if organization slug already exists (if provided and model supports it)
    if payload.organization_slug:
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        if "slug" in available_columns:
            stmt = select(organization_model).where(organization_model.slug == payload.organization_slug)
            result = await user_service.session.execute(stmt)
            existing_slug = result.scalar_one_or_none()
            if existing_slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization with this slug already exists.",
                )

    try:
        # Step 1: Create organization
        mapper = sa_inspect(organization_model)
        available_columns = {col.name for col in mapper.columns} if mapper else set()
        
        org_kwargs = {"name": payload.organization_name}
        
        # Add optional organization attributes if they exist as columns
        if "slug" in available_columns and payload.organization_slug:
            org_kwargs["slug"] = payload.organization_slug
        if "description" in available_columns and payload.organization_description:
            org_kwargs["description"] = payload.organization_description
        if "modules" in available_columns:
            org_kwargs["modules"] = payload.organization_modules or {}
        
        organization = organization_model(**org_kwargs)
        user_service.session.add(organization)
        await user_service.session.flush()
        await user_service.session.refresh(organization)
        
        # Step 2: Create user with is_org_admin=True and link to organization
        user = await user_service.create_user(
            email=payload.email,
            password=payload.password,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            country=payload.country,
            country_code=payload.country_code,
            organization_id=organization.id,  # Link user to organization
            is_org_admin=True,  # Organization admin has full access within org
            is_superuser=False,  # Not a global superuser
            is_verified=True,   # Org admin is auto-verified
            is_active=True,      # Org admin is active
        )

        await user_service.session.commit()
        await user_service.session.refresh(user)
        await user_service.session.refresh(organization)
        
        return OrganizationAdminSignupResponse(
            success=True,
            message="Organization and admin user created successfully. Admin has full access within the organization.",
            organization_id=organization.id,
            organization_name=organization.name,
            user_id=user.id,
            email=user.email,
            username=user.username,
            is_org_admin=True,
        )
    except IntegrityError as e:
        await user_service.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "email" in error_str or "ix_users_email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
        elif "username" in error_str or "ix_users_username" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )
        elif "organization" in error_str or "name" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization with this name already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during organization admin signup: {str(e)}",
        ) from e
    except Exception as e:
        await user_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during organization admin signup: {str(e)}",
        ) from e


@router.post("/admin-signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def admin_signup(
    payload: AdminSignupRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Admin signup endpoint.
    
    Creates a superuser account with all permissions.
    Admin users bypass all permission checks automatically.
    
    Note: Admin users do NOT belong to any organization (organization_id = NULL).
    This allows them to see and manage ALL organizations.
    """
    # Check if user already exists
    existing_user = await user_service.get_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists.",
        )

    # Check if username already exists
    existing_username = await user_service.get_user_by_username(payload.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists.",
        )

    # Admin users should NOT have organization_id
    # They need to see ALL organizations, not be limited to one
    organization_id: UUIDType | None = None
    
    try:
        # Create admin user with superuser privileges
        # organization_id is explicitly set to None
        user = await user_service.create_user(
            email=payload.email,
            password=payload.password,
            username=payload.username,
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            country=payload.country,
            country_code=payload.country_code,
            organization_id=None,  # Admin has no organization
            is_superuser=True,      # Admin has all permissions
            is_verified=True,       # Admin is auto-verified
            is_active=True,         # Admin is active
        )

        await user_service.session.commit()
        await user_service.session.refresh(user)
        
        return SignupResponse(
            success=True,
            message="Admin account created successfully with all permissions",
            user_id=user.id,
            email=user.email,
            username=user.username,
        )
    except IntegrityError as e:
        await user_service.session.rollback()
        error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
        if "email" in error_str or "ix_users_email" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
        elif "username" in error_str or "ix_users_username" in error_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during admin signup: {str(e)}",
        ) from e
    except Exception as e:
        await user_service.session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during admin signup: {str(e)}",
        ) from e


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Login endpoint using JSON payload.
    Returns JWT access and refresh tokens for authenticated requests.
    """
    user = await auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create JWT tokens
    tokens = await auth_service.create_tokens(user)
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user_id=user.id,
    )


@router.post("/refresh", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access token using refresh token.
    Returns new access token and optionally a new refresh token.
    """
    new_tokens = await auth_service.refresh_access_token(request.refresh_token)
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    return LoginResponse(
        access_token=new_tokens["access_token"],
        refresh_token=new_tokens.get("refresh_token", request.refresh_token),
        token_type=new_tokens["token_type"],
        user_id=None,
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout(
    request: LogoutRequest,
    user_service: UserService = Depends(get_user_service),
):
    """
    Logout endpoint.

    Returns a simple success message after verifying the user exists.
    """
    user = await user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return LogoutResponse(success=True, message="User logged out successfully.")


@router.get("/me", response_model=dict, status_code=status.HTTP_200_OK)
async def get_current_user_info(
    current_user: dict = Depends(get_current_active_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Get current user information using JWT token.
    Simple - any authenticated user can access their own data.
    """
    from apex.app.core.dependencies import get_user_model
    from apex.domain.services.user import UserService
    from apex.infrastructure.database.session import get_db as get_db_session
    from uuid import UUID
    
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user in token",
        )
    
    # Get database session if not provided
    if db is None:
        async for session in get_db_session():
            db = session
            break
    
    # Load user from database
    user_model = get_user_model()
    user_service = UserService(db, user_model)
    
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = await user_service.get_user_by_id(str(user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    
    # Return user data - simple format
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or None,
        "phone": user.phone,
        "country": user.country,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "is_superuser": getattr(user, "is_superuser", False),
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "settings": user.settings if hasattr(user, "settings") else {},
        "created_at": user.created_at.isoformat() if hasattr(user, "created_at") else None,
        "updated_at": user.updated_at.isoformat() if hasattr(user, "updated_at") else None,
    }


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user_model: type[BaseUser] = Depends(get_user_model),
):
    """
    Request password reset via email.

    Sends a password reset link to the user's email using SendGrid.
    Always returns success to prevent email enumeration attacks.

    Args:
        request: Forgot password request with email
        db: Database session

    Returns:
        Success message (always returns success for security)
    """
    # Create password reset service with SendGrid integration
    # Note: Users should override get_user_model() to provide their User model
    try:
        service = PasswordResetWithEmailService(
            session=db,
            user_model=user_model,
        )
        
        # Request password reset (sends email via SendGrid)
        await service.request_password_reset(request.email)
    except Exception as e:
        # Log error but don't expose it (security: prevent enumeration)
        print(f"Password reset error: {str(e)}")
    
    # Always return success to prevent email enumeration
    return PasswordResetResponse(
        message="If the email exists, a password reset link has been sent",
        success=True,
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    user_model: type[BaseUser] = Depends(get_user_model),
):
    """
    Reset password using token from email.

    Validates the reset token and updates the user's password.

    Args:
        request: Reset password request with token and new password
        db: Database session

    Returns:
        Success or error message

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Create password reset service
    service = PasswordResetWithEmailService(
        session=db,
        user_model=user_model,
    )
    
    # Attempt to reset password
    success = await service.reset_password(request.token, request.new_password)
    
    if success:
        return PasswordResetResponse(
            message="Password has been reset successfully. You can now login with your new password.",
            success=True,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new password reset.",
        )


@router.post("/change-password", response_model=PasswordResetResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_active_user),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """
    Change current user's password using JWT token.
    Simple - any authenticated user can change their own password.
    """
    from apex.app.core.dependencies import get_user_model
    from apex.domain.services.user import UserService
    from apex.infrastructure.database.session import get_db as get_db_session
    from uuid import UUID
    
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user in token",
        )
    
    # Get database session if not provided
    if db is None:
        async for session in get_db_session():
            db = session
            break
    
    # Load user from database
    user_model = get_user_model()
    user_service = UserService(db, user_model)
    
    try:
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format",
        )
    
    user = await user_service.get_user_by_id(str(user_uuid))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    # Change password
    changed = await user_service.change_password(user, request.old_password, request.new_password)
    if not changed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )

    await db.commit()

    return PasswordResetResponse(
        message="Password changed successfully.",
        success=True,
    )

