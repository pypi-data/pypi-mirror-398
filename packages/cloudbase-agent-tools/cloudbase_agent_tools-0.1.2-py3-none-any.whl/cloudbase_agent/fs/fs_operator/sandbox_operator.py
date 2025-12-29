"""Sandbox File Operator for E2B integration

Provides file system operations within E2B sandboxed environments.
"""

import os
from typing import List, Optional, Union

try:
    from e2b_code_interpreter import Sandbox

    HAS_E2B = True
except ImportError:
    HAS_E2B = False
    Sandbox = None

from .base_operator import BaseFileOperator, PathLike


class Dirent:
    """Directory entry compatible with fs.Dirent"""

    def __init__(self, name: str, path: str, is_file: bool):
        self.name = name
        self.path = path
        self._is_file = is_file

    def is_file(self) -> bool:
        return self._is_file

    def is_dir(self) -> bool:
        return not self._is_file

    def is_directory(self) -> bool:
        return not self._is_file

    def is_symlink(self) -> bool:
        return False

    def is_block_device(self) -> bool:
        return False

    def is_character_device(self) -> bool:
        return False

    def is_fifo(self) -> bool:
        return False

    def is_socket(self) -> bool:
        return False


class SandboxFileStat:
    """File stat compatible with os.stat_result"""

    def __init__(self, size: int, mtime: float, is_file: bool):
        self.st_size = size
        self.st_mtime = mtime
        self.st_atime = mtime
        self.st_ctime = mtime
        self._is_file = is_file
        # File mode: 0o100644 for files, 0o040755 for directories
        self.st_mode = 0o100644 if is_file else 0o040755

    def __repr__(self):
        return f"SandboxFileStat(size={self.st_size}, mtime={self.st_mtime})"


class SandboxFileOperator(BaseFileOperator):
    """File operator for E2B sandbox environments

    Provides file system operations within E2B sandboxed environments,
    ensuring secure and isolated file access.

    Args:
        sandbox: E2B Sandbox instance

    Raises:
        ImportError: If e2b_code_interpreter is not installed
        ValueError: If sandbox instance is not provided
    """

    def __init__(self, sandbox: Optional[Sandbox] = None):
        if not HAS_E2B:
            raise ImportError(
                "e2b_code_interpreter is required for SandboxFileOperator. "
                "Install with: pip install e2b-code-interpreter"
            )

        if not sandbox:
            raise ValueError("Sandbox instance is required")

        super().__init__()
        self.sandbox = sandbox

    async def access(self, path: PathLike, mode: int = os.F_OK) -> None:
        """Check file access

        Args:
            path: Path to check
            mode: Access mode (ignored for sandbox)

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        path_str = str(path)
        exists = await self.exists(path_str)
        if not exists:
            raise FileNotFoundError(f"No such file or directory: '{path_str}'")

    async def read_file(self, path: PathLike, encoding: Optional[str] = None) -> Union[str, bytes]:
        """Read file contents from sandbox

        Args:
            path: Path to file
            encoding: Optional encoding (e.g., 'utf-8')

        Returns:
            File contents as string (if encoding specified) or bytes
        """
        path_str = str(path)
        content_bytes = self.sandbox.files.read(path_str)

        if encoding:
            if isinstance(content_bytes, bytes):
                return content_bytes.decode(encoding)
            return str(content_bytes)
        else:
            if isinstance(content_bytes, bytes):
                return content_bytes
            return content_bytes.encode("utf-8")

    async def write_file(self, path: PathLike, data: Union[str, bytes], encoding: Optional[str] = None) -> None:
        """Write file contents to sandbox

        Args:
            path: Path to file
            data: Content to write (string or bytes)
            encoding: Optional encoding (defaults to 'utf-8' for strings)
        """
        path_str = str(path)

        # Convert data to appropriate format
        if isinstance(data, str):
            final_data = data.encode(encoding or "utf-8")
        else:
            final_data = data

        self.sandbox.files.write(path_str, final_data)

    async def mkdir(self, path: PathLike, parents: bool = False, exist_ok: bool = False) -> Optional[str]:
        """Create directory in sandbox

        Args:
            path: Path to directory
            parents: Create parent directories if needed
            exist_ok: Don't raise error if directory exists

        Returns:
            Path string if created with parents=True, None otherwise
        """
        path_str = str(path)

        if parents:
            # E2B makeDir creates parent directories by default
            success = self.sandbox.files.make_dir(path_str)
            return path_str if success else None
        else:
            self.sandbox.files.make_dir(path_str)
            return None

    async def readdir(self, path: PathLike, with_file_types: bool = False) -> Union[List[str], List[Dirent]]:
        """Read directory contents from sandbox

        Args:
            path: Path to directory
            with_file_types: Return Dirent objects instead of strings

        Returns:
            List of file names or Dirent objects
        """
        path_str = str(path)
        items = self.sandbox.files.list(path_str)

        if with_file_types:
            # Return Dirent-like objects
            result = []
            for item in items:
                # E2B returns items with 'name', 'path', and 'type' properties
                # Handle FileType object - check if it's a file
                if hasattr(item, "type"):
                    # E2B FileType is an enum, check its value or compare directly
                    if hasattr(item.type, "value"):
                        is_file = item.type.value.lower() == "file"
                    else:
                        # Fallback: convert to string and check
                        file_type_str = str(item.type).lower()
                        is_file = "file" in file_type_str
                else:
                    is_file = True
                dirent = Dirent(
                    name=item.name,
                    path=item.path if hasattr(item, "path") else os.path.join(path_str, item.name),
                    is_file=is_file,
                )
                result.append(dirent)
            return result
        else:
            # Return just names
            return [item.name for item in items]

    async def stat(self, path: PathLike) -> SandboxFileStat:
        """Get file statistics from sandbox

        Args:
            path: Path to file

        Returns:
            File stat object
        """
        path_str = str(path)
        info = self.sandbox.files.get_info(path_str)

        # Extract info
        size = info.size if hasattr(info, "size") else 0
        mtime = info.modified_time if hasattr(info, "modified_time") else 0

        # Handle FileType object - check if it's a file
        if hasattr(info, "type"):
            # E2B FileType is an enum, check its value or compare directly
            if hasattr(info.type, "value"):
                is_file = info.type.value.lower() == "file"
            else:
                # Fallback: convert to string and check
                file_type_str = str(info.type).lower()
                is_file = "file" in file_type_str
        else:
            is_file = True

        # Convert timestamp if needed
        if isinstance(mtime, str):
            # Parse ISO timestamp
            from datetime import datetime

            try:
                dt = datetime.fromisoformat(mtime.replace("Z", "+00:00"))
                mtime = dt.timestamp()
            except:
                mtime = 0

        return SandboxFileStat(size=size, mtime=mtime, is_file=is_file)

    async def exists(self, path: PathLike) -> bool:
        """Check if file exists in sandbox

        Args:
            path: Path to check

        Returns:
            True if file exists
        """
        path_str = str(path)
        return self.sandbox.files.exists(path_str)

    async def unlink(self, path: PathLike) -> None:
        """Remove file from sandbox

        Args:
            path: Path to file
        """
        path_str = str(path)
        self.sandbox.files.remove(path_str)

    async def rmdir(self, path: PathLike) -> None:
        """Remove directory from sandbox

        Args:
            path: Path to directory
        """
        path_str = str(path)
        self.sandbox.files.remove(path_str)

    async def rename(self, old_path: PathLike, new_path: PathLike) -> None:
        """Rename file in sandbox

        Args:
            old_path: Current path
            new_path: New path
        """
        old_path_str = str(old_path)
        new_path_str = str(new_path)
        self.sandbox.files.rename(old_path_str, new_path_str)
