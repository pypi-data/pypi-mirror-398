"""
Application configuration layer for generated projects.

This module re-exports the package-level Settings helpers while providing
project-scoped aliases expected by the blueprint.
"""
from apex.core.config import Settings as PackageSettings
from apex.core.config import get_settings as get_package_settings


class AppSettings(PackageSettings):
    """Alias for backwards compatibility with the new project structure."""


def get_settings() -> AppSettings:
    """Return the cached settings instance typed for the project."""
    return AppSettings.model_validate(get_package_settings().model_dump())


__all__ = ["AppSettings", "get_settings"]

