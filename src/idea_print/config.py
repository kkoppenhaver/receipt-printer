"""Configuration and environment variable loading."""

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class PrinterProfile:
    """Configuration for a thermal printer."""

    chars_per_line: int = 30
    encoding: str = "cp437"
    cut_type: Literal["full", "partial", "none"] = "full"
    feed_lines_before_cut: int = 4


@dataclass
class Config:
    """Application configuration loaded from environment variables."""

    hmac_secret: str = field(default_factory=lambda: os.environ.get("HMAC_SECRET", ""))
    printer_transport: str = field(
        default_factory=lambda: os.environ.get("PRINTER_TRANSPORT", "serial")
    )
    printer_port: str = field(
        default_factory=lambda: os.environ.get("PRINTER_PORT", "/dev/ttyUSB0")
    )
    printer_baud: int = field(
        default_factory=lambda: int(os.environ.get("PRINTER_BAUD", "9600"))
    )
    file_output_path: str = field(
        default_factory=lambda: os.environ.get("FILE_OUTPUT_PATH", "receipt.bin")
    )
    printer_usb_vendor: str = field(
        default_factory=lambda: os.environ.get("PRINTER_USB_VENDOR", "")
    )
    printer_usb_product: str = field(
        default_factory=lambda: os.environ.get("PRINTER_USB_PRODUCT", "")
    )
    server_host: str = field(
        default_factory=lambda: os.environ.get("SERVER_HOST", "0.0.0.0")
    )
    server_port: int = field(
        default_factory=lambda: int(os.environ.get("SERVER_PORT", "8000"))
    )
    timestamp_window_seconds: int = field(
        default_factory=lambda: int(os.environ.get("TIMESTAMP_WINDOW", "300"))
    )
    dedupe_enabled: bool = field(
        default_factory=lambda: os.environ.get("DEDUPE_ENABLED", "false").lower()
        == "true"
    )
    dedupe_db_path: str = field(
        default_factory=lambda: os.environ.get("DEDUPE_DB_PATH", "dedupe.db")
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls()


def get_config() -> Config:
    """Get the current configuration."""
    return Config.from_env()
