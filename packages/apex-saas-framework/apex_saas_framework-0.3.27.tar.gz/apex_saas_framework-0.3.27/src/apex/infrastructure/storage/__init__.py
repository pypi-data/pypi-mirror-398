"""File storage infrastructure."""

from apex.infrastructure.storage.base import StorageAdapter
from apex.infrastructure.storage.local import LocalStorageAdapter

__all__ = [
    "StorageAdapter",
    "LocalStorageAdapter",
]

