"""Base transport interface."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Transport(Protocol):
    """Protocol for printer transport implementations."""

    def open(self) -> None:
        """Open the transport connection."""
        ...

    def close(self) -> None:
        """Close the transport connection."""
        ...

    def write(self, data: bytes) -> int:
        """Write data to the printer. Returns bytes written."""
        ...

    def __enter__(self) -> "Transport":
        """Context manager entry."""
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        ...
