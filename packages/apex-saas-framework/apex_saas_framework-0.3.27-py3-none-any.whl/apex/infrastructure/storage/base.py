"""Abstract storage adapter interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO


class StorageAdapter(ABC):
    """Abstract base class for file storage adapters."""

    @abstractmethod
    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        folder: str | None = None,
    ) -> str:
        """
        Upload a file.

        Args:
            file: File-like object to upload
            filename: Name for the file
            folder: Optional folder/path prefix

        Returns:
            URL or path to the uploaded file
        """
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.

        Args:
            file_path: Path or URL to the file

        Returns:
            True if deletion was successful
        """
        pass

    @abstractmethod
    async def get_file_url(self, file_path: str) -> str:
        """
        Get a URL for accessing a file.

        Args:
            file_path: Path to the file

        Returns:
            URL to access the file
        """
        pass

