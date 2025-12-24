"""Data models for Drime S3 Gateway."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FileEntry:
    """Represents a file or folder in Drime Cloud."""
    
    id: int
    name: str
    parent_id: Optional[int] = None
    is_folder: bool = False
    file_size: int = 0
    hash: Optional[str] = None
    mime: Optional[str] = None
    updated_at: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None  # Direct download URL

    @classmethod
    def from_dict(cls, data: dict) -> "FileEntry":
        """Create FileEntry from API response dict."""
        return cls(
            id=data.get("id", 0),
            name=data.get("name", ""),
            parent_id=data.get("parent_id"),
            is_folder=data.get("type") == "folder",
            file_size=data.get("file_size", 0),
            hash=data.get("hash"),
            mime=data.get("mime"),
            updated_at=data.get("updated_at"),
            description=data.get("description"),
            url=data.get("url"),
        )
