"""Application settings and configuration management."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Apex"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database - Accept any SQLAlchemy-compatible database URL
    # Examples:
    # - PostgreSQL: postgresql+asyncpg://user:pass@localhost/db
    # - SQLite: sqlite+aiosqlite:///./mydb.db
    # - MySQL: mysql+aiomysql://user:pass@localhost/db
    # - Any SQLAlchemy-supported database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./apex.db"
    )
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Security
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        min_length=32,
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    )
    CORS_ALLOW_HEADERS: list[str] = Field(default_factory=lambda: ["*"])

    # Email Configuration
    EMAIL_PROVIDER: str = "sendgrid"  # 'smtp' or 'sendgrid'
    
    # SMTP (optional - if not using SendGrid)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # SendGrid Configuration
    SEND_GRID_API: Optional[str] = None
    # Alias for backward compatibility (SENDGRID_API_KEY)
    SENDGRID_API_KEY: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    FROM_NAME: Optional[str] = None
    
    @property
    def sendgrid_api_key(self) -> Optional[str]:
        """Get SendGrid API key from either variable name."""
        return self.SEND_GRID_API or self.SENDGRID_API_KEY
    
    # Frontend URLs
    FRONTEND_RESET_URL: str = "https://dbaas.apexneural.cloud/reset-password"
    FRONTEND_BASE_URL: str = "https://dbaas.apexneural.cloud"

    # PayPal Redirect URLs
    PAYPAL_RETURN_URL: Optional[str] = None
    PAYPAL_CANCEL_URL: Optional[str] = None

    # File Storage
    STORAGE_TYPE: str = "local"  # 'local' or 's3'
    STORAGE_LOCAL_PATH: str = "./uploads"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_S3_BUCKET: Optional[str] = None

    # Payments (PayPal ONLY)
    PAYPAL_CLIENT_ID: Optional[str] = None
    PAYPAL_CLIENT_SECRET: Optional[str] = None
    PAYPAL_MODE: str = "sandbox"  # 'sandbox' or 'live'
    PAYPAL_WEBHOOK_ID: Optional[str] = None

    # Multi-tenancy
    MULTI_TENANT_MODE: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # No validation - accept any SQLAlchemy-compatible database URL
    # Users can use PostgreSQL, SQLite, MySQL, or any supported database


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

