from pathlib import Path
import os
from typing import Union

CWD = Path.cwd()


class SafePath:
    """A Path-like class that restricts operations to cwd and its
    descendants"""

    def __init__(self, path_str: Union[str, "SafePath"] = "."):

        self._cwd = CWD.resolve()

        if isinstance(path_str, SafePath):
            self._path = path_str._path
        else:
            # Convert to Path and resolve to handle .. and . components
            try:
                resolved_path = (self._cwd / path_str).resolve()
            except (OSError, ValueError):
                raise ValueError(f"Invalid path: {path_str}")

            # Validate it's within cwd - could probably shorten this
            if not resolved_path.is_relative_to(self._cwd):
                raise ValueError(f"Path outside allowed directory: {path_str}")

            self._path = resolved_path

    def __str__(self):
        return str(self._path.relative_to(self._cwd))

    def __repr__(self):
        return f"SafePath('{self}')"

    def __truediv__(self, other):
        """Support path / 'subdir' syntax"""
        new_path_str = str(self._path / str(other))
        return SafePath(new_path_str)

    # File content operations
    def read_text(self, encoding="utf-8"):
        if not self._path.is_file():
            raise FileNotFoundError(f"File not found: {self}")
        return self._path.read_text(encoding=encoding)

    def write_text(self, content, encoding="utf-8"):
        # Ensure parent directories exist
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(content, encoding=encoding)
        return self

    def read_bytes(self):
        if not self._path.is_file():
            raise FileNotFoundError(f"File not found: {self}")
        return self._path.read_bytes()

    def write_bytes(self, data):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_bytes(data)
        return self

    # Path properties and checks
    def exists(self):
        return self._path.exists()

    def is_file(self):
        return self._path.is_file()

    def is_dir(self):
        return self._path.is_dir()

    def is_absolute(self):
        return self._path.is_absolute()

    @property
    def name(self):
        return self._path.name

    @property
    def stem(self):
        return self._path.stem

    @property
    def suffix(self):
        return self._path.suffix

    @property
    def parent(self):
        return SafePath(str(self._path.parent))

    # Directory operations
    def mkdir(self, parents=True, exist_ok=True):
        self._path.mkdir(parents=parents, exist_ok=exist_ok)
        return self

    def iterdir(self):
        if not self._path.is_dir():
            raise NotADirectoryError(f"Not a directory: {self}")
        return [SafePath(str(p)) for p in self._path.iterdir()]

    def glob(self, pattern):
        return [SafePath(str(p)) for p in self._path.glob(pattern)]

    def rglob(self, pattern):
        return [SafePath(str(p)) for p in self._path.rglob(pattern)]

    # File metadata
    def stat(self):
        return self._path.stat()

    @property
    def size(self):
        if not self._path.is_file():
            raise FileNotFoundError(f"File not found: {self}")
        return self._path.stat().st_size
