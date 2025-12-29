"""Base file operation abstract class

Defines the abstract interface for file system operations that all file operators must implement.
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

PathLike = Union[str, Path, os.PathLike]


class BaseFileOperator(ABC):
    """Abstract base class for file operations

    Defines the interface methods that all file system operators must implement.
    """

    def __init__(self):
        pass

    @abstractmethod
    async def access(self, path: PathLike) -> None:
        """Check file access permissions

        Args:
            path: File path

        Raises:
            PermissionError: No access permission
            FileNotFoundError: File does not exist
        """
        pass

    @abstractmethod
    async def read_file(self, path: PathLike, encoding: Optional[str] = None) -> Union[bytes, str]:
        """Read file content

        Args:
            path: File path
            encoding: Character encoding, returns string if specified, otherwise returns bytes

        Returns:
            File content (string or bytes)
        """
        pass

    @abstractmethod
    async def mkdir(self, path: PathLike, parents: bool = False, exist_ok: bool = False) -> Optional[str]:
        """Create directory

        Args:
            path: Directory path
            parents: Whether to create parent directories
            exist_ok: Whether to raise error if directory already exists

        Returns:
            Created directory path (if parents=True)
        """
        pass

    @abstractmethod
    async def write_file(
        self,
        path: PathLike,
        data: Union[str, bytes],
        encoding: Optional[str] = None,
    ) -> None:
        """Write file

        Args:
            path: File path
            data: Data to write
            encoding: Character encoding (used when data is string)
        """
        pass

    @abstractmethod
    async def readdir(self, path: PathLike, with_file_types: bool = False) -> Union[List[str], List[os.DirEntry]]:
        """Read directory contents

        Args:
            path: Directory path
            with_file_types: Whether to return DirEntry objects

        Returns:
            List of file names or DirEntry objects
        """
        pass

    @abstractmethod
    async def stat(self, path: PathLike) -> os.stat_result:
        """Get file status information

        Args:
            path: File path

        Returns:
            File status information
        """
        pass

    @abstractmethod
    async def exists(self, path: PathLike) -> bool:
        """Check if file or directory exists

        Args:
            path: File or directory path

        Returns:
            Whether it exists
        """
        pass

    @abstractmethod
    async def unlink(self, path: PathLike) -> None:
        """Delete file

        Args:
            path: File path
        """
        pass

    @abstractmethod
    async def rmdir(self, path: PathLike) -> None:
        """Delete directory

        Args:
            path: Directory path
        """
        pass

    @abstractmethod
    async def rename(self, old_path: PathLike, new_path: PathLike) -> None:
        """Rename file or directory

        Args:
            old_path: Original path
            new_path: New path
        """
        pass


class LocalFileOperator(BaseFileOperator):
    """Local file system operator

    Implementation using standard library file system operations.
    """

    def __init__(self):
        super().__init__()

    async def access(self, path: PathLike) -> None:
        """Check file access permissions"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not os.access(path, os.R_OK):
            raise PermissionError(f"No read permission: {path}")

    async def read_file(self, path: PathLike, encoding: Optional[str] = None) -> Union[bytes, str]:
        """Read file content"""
        path = Path(path)
        if encoding:
            return path.read_text(encoding=encoding)
        else:
            return path.read_bytes()

    async def mkdir(self, path: PathLike, parents: bool = False, exist_ok: bool = False) -> Optional[str]:
        """Create directory"""
        path = Path(path)
        path.mkdir(parents=parents, exist_ok=exist_ok)
        if parents:
            return str(path)
        return None

    async def write_file(
        self,
        path: PathLike,
        data: Union[str, bytes],
        encoding: Optional[str] = None,
    ) -> None:
        """Write file"""
        path = Path(path)
        if isinstance(data, str):
            path.write_text(data, encoding=encoding or "utf-8")
        else:
            path.write_bytes(data)

    async def readdir(self, path: PathLike, with_file_types: bool = False) -> Union[List[str], List[os.DirEntry]]:
        """Read directory contents"""
        path = Path(path)
        if with_file_types:
            return list(os.scandir(path))
        else:
            return [entry.name for entry in os.scandir(path)]

    async def stat(self, path: PathLike) -> os.stat_result:
        """Get file status information"""
        return os.stat(path)

    async def exists(self, path: PathLike) -> bool:
        """Check if file or directory exists"""
        return Path(path).exists()

    async def unlink(self, path: PathLike) -> None:
        """Delete file"""
        Path(path).unlink()

    async def rmdir(self, path: PathLike) -> None:
        """Delete directory"""
        Path(path).rmdir()

    async def rename(self, old_path: PathLike, new_path: PathLike) -> None:
        """Rename file or directory"""
        Path(old_path).rename(new_path)
