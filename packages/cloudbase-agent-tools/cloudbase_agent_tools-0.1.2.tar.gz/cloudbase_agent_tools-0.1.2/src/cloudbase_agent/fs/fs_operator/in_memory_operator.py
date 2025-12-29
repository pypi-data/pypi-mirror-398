"""In-memory file system operator

In-memory file system operations implemented using pyfakefs library, for testing and sandbox environments.
"""

import os
from typing import List, Optional, Union

from .base_operator import BaseFileOperator, PathLike

try:
    from pyfakefs.fake_filesystem import FakeFilesystem
except ImportError:
    FakeFilesystem = None


class InMemoryFileOperator(BaseFileOperator):
    """In-memory file system operator

    Implementation using in-memory file system provided by pyfakefs.
    Requires installation: pip install pyfakefs

    Args:
        filesystem: FakeFilesystem instance
    """

    def __init__(self, filesystem: "FakeFilesystem"):
        super().__init__()
        if FakeFilesystem is None:
            raise ImportError("pyfakefs is required for InMemoryFileOperator. Install it with: pip install pyfakefs")
        self.filesystem = filesystem

    async def access(self, path: PathLike) -> None:
        """Check file access permissions"""
        path_str = str(path)
        if not self.filesystem.exists(path_str):
            raise FileNotFoundError(f"File not found: {path}")
        # pyfakefs allows all access by default

    async def read_file(self, path: PathLike, encoding: Optional[str] = None) -> Union[bytes, str]:
        """Read file content"""
        path_str = str(path)
        if encoding:
            return self.filesystem.get_object(path_str).contents
        else:
            return self.filesystem.get_object(path_str).byte_contents

    async def mkdir(self, path: PathLike, parents: bool = False, exist_ok: bool = False) -> Optional[str]:
        """Create directory"""
        path_str = str(path)
        self.filesystem.makedirs(path_str, exist_ok=exist_ok) if parents else self.filesystem.makedir(path_str)
        if parents:
            return path_str
        return None

    async def write_file(
        self,
        path: PathLike,
        data: Union[str, bytes],
        encoding: Optional[str] = None,
    ) -> None:
        """Write file"""
        path_str = str(path)
        # Remove existing file if it exists
        if self.filesystem.exists(path_str):
            self.filesystem.remove(path_str)

        if isinstance(data, str):
            self.filesystem.create_file(path_str, contents=data, encoding=encoding or "utf-8")
        else:
            self.filesystem.create_file(path_str, contents=data)

    async def readdir(self, path: PathLike, with_file_types: bool = False) -> Union[List[str], List[os.DirEntry]]:
        """Read directory contents"""
        path_str = str(path)
        entries = self.filesystem.listdir(path_str)

        if with_file_types:
            # Create DirEntry-like objects
            result = []
            for entry in entries:
                entry_path = os.path.join(path_str, entry)
                result.append(self._create_dir_entry(entry, entry_path))
            return result
        else:
            return entries

    def _create_dir_entry(self, name: str, path: str):
        """Create DirEntry-like object"""

        class FakeDirEntry:
            def __init__(self, name: str, path: str, filesystem):
                self.name = name
                self.path = path
                self._filesystem = filesystem

            def is_file(self) -> bool:
                return self._filesystem.isfile(self.path)

            def is_dir(self) -> bool:
                return self._filesystem.isdir(self.path)

            def is_symlink(self) -> bool:
                return self._filesystem.islink(self.path)

            def stat(self):
                return self._filesystem.stat(self.path)

        return FakeDirEntry(name, path, self.filesystem)

    async def stat(self, path: PathLike) -> os.stat_result:
        """Get file status information"""
        return self.filesystem.stat(str(path))

    async def exists(self, path: PathLike) -> bool:
        """Check if file or directory exists"""
        return self.filesystem.exists(str(path))

    async def unlink(self, path: PathLike) -> None:
        """Delete file"""
        self.filesystem.remove(str(path))

    async def rmdir(self, path: PathLike) -> None:
        """Delete directory"""
        self.filesystem.rmdir(str(path))

    async def rename(self, old_path: PathLike, new_path: PathLike) -> None:
        """Rename file or directory"""
        self.filesystem.rename(str(old_path), str(new_path))
