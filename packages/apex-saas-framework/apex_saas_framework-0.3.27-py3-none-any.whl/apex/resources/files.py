"""
Files Resource - Clerk-style file/storage management
"""
from typing import Optional, BinaryIO
from apex.client import Client
from apex.infrastructure.storage.local import LocalStorageAdapter
from apex.infrastructure.storage.base import StorageAdapter


class Files:
    """
    Files resource - provides file upload and storage management
    
    Usage:
        # Upload file
        file_path = await client.files.upload(
            file=file_object,
            filename="document.pdf"
        )
        
        # Get file URL
        url = await client.files.get_url(file_path)
        
        # Delete file
        await client.files.delete(file_path)
    """
    
    def __init__(self, client: Client, adapter: Optional[StorageAdapter] = None):
        self.client = client
        self.adapter = adapter or LocalStorageAdapter()
    
    async def upload(
        self,
        file: BinaryIO,
        filename: str,
        folder: Optional[str] = None
    ) -> str:
        """
        Upload a file.
        
        Args:
            file: File object (BinaryIO)
            filename: File name
            folder: Ignored (no folder creation) - kept for backward compatibility
        
        Returns:
            File path/identifier (filename only)
        """
        return await self.adapter.upload_file(
            file=file,
            filename=filename,
            folder=None  # No folder creation
        )
    
    async def get_url(self, file_path: str) -> str:
        """
        Get file URL.
        
        Args:
            file_path: File path/identifier
        
        Returns:
            File URL
        """
        return await self.adapter.get_file_url(file_path)
    
    async def delete(self, file_path: str) -> bool:
        """
        Delete a file.
        
        Args:
            file_path: File path/identifier
        
        Returns:
            True if deleted successfully
        """
        return await self.adapter.delete_file(file_path)
    
    async def exists(self, file_path: str) -> bool:
        """
        Check if file exists.
        
        Args:
            file_path: File path/identifier
        
        Returns:
            True if file exists
        """
        # Check if file exists by trying to get URL
        try:
            url = await self.adapter.get_file_url(file_path)
            return bool(url)
        except Exception:
            return False

