"""File-based transport for development and testing."""

from pathlib import Path
from typing import BinaryIO


class FileTransport:
    """Transport that writes to a file (for testing/development)."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._file: BinaryIO | None = None

    def open(self) -> None:
        """Open the file for writing."""
        self._file = open(self.path, "wb")

    def close(self) -> None:
        """Close the file."""
        if self._file:
            self._file.close()
            self._file = None

    def write(self, data: bytes) -> int:
        """Write data to the file."""
        if not self._file:
            raise RuntimeError("Transport not open")
        return self._file.write(data)

    def __enter__(self) -> "FileTransport":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
