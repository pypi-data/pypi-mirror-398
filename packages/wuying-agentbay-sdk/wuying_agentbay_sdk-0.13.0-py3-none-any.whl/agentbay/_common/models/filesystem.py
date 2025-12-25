"""
Filesystem module data models.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from .response import ApiResponse


@dataclass
class UploadResult:
    """Result structure for file upload operations."""

    success: bool
    request_id_upload_url: Optional[str]
    request_id_sync: Optional[str]
    http_status: Optional[int]
    etag: Optional[str]
    bytes_sent: int
    path: str
    error: Optional[str] = None


@dataclass
class DownloadResult:
    """Result structure for file download operations."""

    success: bool
    request_id_download_url: Optional[str]
    request_id_sync: Optional[str]
    http_status: Optional[int]
    bytes_received: int
    path: str
    local_path: str
    error: Optional[str] = None


class FileChangeEvent:
    """Represents a single file change event."""

    def __init__(
        self,
        event_type: str = "",
        path: str = "",
        path_type: str = "",
    ):
        """
        Initialize a FileChangeEvent.

        Args:
            event_type (str): Type of the file change event (e.g., "modify", "create", "delete").
            path (str): Path of the file or directory that changed.
            path_type (str): Type of the path ("file" or "directory").
        """
        self.event_type = event_type
        self.path = path
        self.path_type = path_type

    def __repr__(self):
        return f"FileChangeEvent(event_type='{self.event_type}', path='{self.path}', path_type='{self.path_type}')"

    def _to_dict(self) -> Dict[str, str]:
        """Convert to dictionary representation."""
        return {
            "eventType": self.event_type,
            "path": self.path,
            "pathType": self.path_type,
        }

    @classmethod
    def _from_dict(cls, data: Dict[str, str]) -> "FileChangeEvent":
        """Create FileChangeEvent from dictionary."""
        return cls(
            event_type=data.get("eventType", ""),
            path=data.get("path", ""),
            path_type=data.get("pathType", ""),
        )


class FileChangeResult(ApiResponse):
    """
    Result of file change detection operations.
    """

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        events: Optional[List[FileChangeEvent]] = None,
        raw_data: str = "",
        error_message: str = "",
    ):
        """
        Initialize a FileChangeResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            events (List[FileChangeEvent], optional): List of file change events.
                Defaults to None.
            raw_data (str, optional): Raw response data for debugging. Defaults to "".
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.events = events or []
        self.raw_data = raw_data
        self.error_message = error_message

    def has_changes(self) -> bool:
        """
        Check if there are any file changes.

        Returns:
            bool: True if there are any file change events, False otherwise.
        """
        return len(self.events) > 0

    def get_modified_files(self) -> List[str]:
        """
        Get list of modified file paths.

        Returns:
            List[str]: List of file paths that were modified.
        """
        return [
            event.path
            for event in self.events
            if event.event_type == "modify" and event.path_type == "file"
        ]

    def get_created_files(self) -> List[str]:
        """
        Get list of created file paths.

        Returns:
            List[str]: List of file paths that were created.
        """
        return [
            event.path
            for event in self.events
            if event.event_type == "create" and event.path_type == "file"
        ]

    def get_deleted_files(self) -> List[str]:
        """
        Get list of deleted file paths.

        Returns:
            List[str]: List of file paths that were deleted.
        """
        return [
            event.path
            for event in self.events
            if event.event_type == "delete" and event.path_type == "file"
        ]


class FileInfoResult(ApiResponse):
    """Result of file info operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        file_info: Optional[Dict[str, Any]] = None,
        error_message: str = "",
    ):
        """
        Initialize a FileInfoResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            file_info (Dict[str, Any], optional): File information. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.file_info = file_info or {}
        self.error_message = error_message
    
    @property
    def is_file(self) -> bool:
        """Check if the path is a file."""
        return self.file_info.get("isFile", False)
    
    @property
    def is_directory(self) -> bool:
        """Check if the path is a directory."""
        return self.file_info.get("isDirectory", False)
    
    @property
    def size(self) -> int:
        """Get file size in bytes."""
        return self.file_info.get("size", 0)
    
    @property
    def permissions(self) -> str:
        """Get file permissions."""
        return self.file_info.get("permissions", "")


class DirectoryEntry:
    """Wrapper for directory entry with attribute access."""
    
    def __init__(self, entry_dict: Dict[str, Any]):
        self._data = entry_dict
    
    @property
    def name(self) -> str:
        """Get entry name."""
        return self._data.get("name", "")
    
    @property
    def is_file(self) -> bool:
        """Check if entry is a file."""
        # Support both key formats for compatibility
        return self._data.get("isFile", self._data.get("is_file", False))
    
    @property
    def is_directory(self) -> bool:
        """Check if entry is a directory."""
        # Support both key formats for compatibility
        return self._data.get("is_directory", self._data.get("isDirectory", False))
    
    @property
    def size(self) -> int:
        """Get entry size."""
        return self._data.get("size", 0)


class DirectoryListResult(ApiResponse):
    """Result of directory listing operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        entries: Optional[List[Dict[str, Any]]] = None,
        error_message: str = "",
    ):
        """
        Initialize a DirectoryListResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            entries (List[Dict[str, Any]], optional): Directory entries. Defaults to
                None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self._entries = entries or []
        self.error_message = error_message
    
    @property
    def entries(self) -> List[DirectoryEntry]:
        """Get directory entries with attribute access."""
        return [DirectoryEntry(entry) for entry in self._entries]


class FileContentResult(ApiResponse):
    """Result of file read operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        content: str = "",
        error_message: str = "",
    ):
        """
        Initialize a FileContentResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            content (str, optional): File content. Defaults to "".
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.content = content
        self.error_message = error_message


class MultipleFileContentResult(ApiResponse):
    """Result of multiple file read operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        contents: Optional[Dict[str, str]] = None,
        error_message: str = "",
    ):
        """
        Initialize a MultipleFileContentResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            contents (Dict[str, str], optional): Dictionary of file paths to file
                contents. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.contents = contents or {}
        self.error_message = error_message


class FileSearchResult(ApiResponse):
    """Result of file search operations."""

    def __init__(
        self,
        request_id: str = "",
        success: bool = False,
        matches: Optional[List[str]] = None,
        error_message: str = "",
    ):
        """
        Initialize a FileSearchResult.

        Args:
            request_id (str, optional): Unique identifier for the API request.
                Defaults to "".
            success (bool, optional): Whether the operation was successful.
                Defaults to False.
            matches (List[str], optional): Matching file paths. Defaults to None.
            error_message (str, optional): Error message if the operation failed.
                Defaults to "".
        """
        super().__init__(request_id)
        self.success = success
        self.matches = matches or []
        self.error_message = error_message

