"""Local file storage adapter."""

import os
from pathlib import Path
from typing import BinaryIO

from apex.core.config import get_settings
from apex.infrastructure.storage.base import StorageAdapter

settings = get_settings()


class LocalStorageAdapter(StorageAdapter):
    """Local filesystem storage adapter."""

    def __init__(self, base_path: str | None = None):
        """
        Initialize local storage adapter.

        Args:
            base_path: Base path for file storage. Defaults to settings.STORAGE_LOCAL_PATH
        """
        self.base_path = Path(base_path or settings.STORAGE_LOCAL_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        folder: str | None = None,
    ) -> str:
        """
        Upload a file to local storage.

        Args:
            file: File-like object to upload
            filename: Name for the file
            folder: Optional folder/path prefix (ignored - no folder creation)

        Returns:
            Relative path to the uploaded file
        """
        # Store all files directly in base_path, no folder creation
        upload_path = self.base_path
        upload_path.mkdir(parents=True, exist_ok=True)

        file_path = upload_path / filename

        with open(file_path, "wb") as f:
            f.write(file.read())

        relative_path = file_path.relative_to(self.base_path)
        return str(relative_path)

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from local storage.

        Args:
            file_path: Relative path to the file

        Returns:
            True if deletion was successful
        """
        full_path = self.base_path / file_path
        try:
            if full_path.exists():
                os.remove(full_path)
                return True
            return False
        except Exception:
            return False

    async def get_file_url(self, file_path: str) -> str:
        """
        Get a URL for accessing a file.

        Args:
            file_path: Relative path to the file

        Returns:
            URL to access the file (local path in this case)
        """
        # Return just the filename, not folder path
        filename = file_path.split('/')[-1] if '/' in file_path else file_path
        return f"/uploads/{filename}"

