"""FastAPI server for receiving print requests."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from pydantic import BaseModel, Field

from .auth import verify_signature
from .config import Config, PrinterProfile, get_config
from .dedupe import DedupeStore
from .template import build_receipt
from .transport import FileTransport, SerialTransport, UsbTransport

logger = logging.getLogger(__name__)

# Global print lock to serialize print operations
_print_lock = asyncio.Lock()

# Global dedupe store (initialized at startup if enabled)
_dedupe_store: DedupeStore | None = None


class PrintRequest(BaseModel):
    """Request body for print endpoint."""

    idea_text: str = Field(..., min_length=1, max_length=10000)
    idea_id: str | None = Field(default=None, max_length=100)
    request_id: str | None = Field(default=None, max_length=100)


class PrintResponse(BaseModel):
    """Response body for print endpoint."""

    success: bool
    message: str
    idea_id: str | None = None


class HealthResponse(BaseModel):
    """Response body for health endpoint."""

    status: str
    transport: str
    dedupe_enabled: bool


def get_transport(config: Config):
    """Get the appropriate transport based on configuration."""
    if config.printer_transport == "file":
        return FileTransport(config.file_output_path)
    elif config.printer_transport == "serial":
        return SerialTransport(
            port=config.printer_port,
            baudrate=config.printer_baud,
        )
    elif config.printer_transport == "usb":
        if not config.printer_usb_vendor or not config.printer_usb_product:
            raise ValueError("USB transport requires PRINTER_USB_VENDOR and PRINTER_USB_PRODUCT")
        vendor = config.printer_usb_vendor
        product = config.printer_usb_product
        vid = int(vendor, 16) if vendor.startswith("0x") else int(vendor)
        pid = int(product, 16) if product.startswith("0x") else int(product)
        return UsbTransport(vendor_id=vid, product_id=pid)
    else:
        raise ValueError(f"Unknown transport: {config.printer_transport}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global _dedupe_store
    config = get_config()

    if config.dedupe_enabled:
        _dedupe_store = DedupeStore(config.dedupe_db_path)
        logger.info(f"Dedupe store initialized at {config.dedupe_db_path}")

    logger.info(f"Server starting with transport: {config.printer_transport}")
    yield

    logger.info("Server shutting down")


app = FastAPI(
    title="idea-print",
    description="Receipt printer agent for thermal printers",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    config = get_config()
    return HealthResponse(
        status="ok",
        transport=config.printer_transport,
        dedupe_enabled=config.dedupe_enabled,
    )


async def verify_auth(
    request: Request,
    x_timestamp: Annotated[str | None, Header()] = None,
    x_signature: Annotated[str | None, Header()] = None,
) -> None:
    """Dependency to verify request authentication."""
    config = get_config()

    # Skip auth if no secret configured (development mode)
    if not config.hmac_secret:
        logger.warning("HMAC_SECRET not set, skipping authentication")
        return

    body = await request.body()

    result = verify_signature(
        body=body,
        signature=x_signature or "",
        timestamp=x_timestamp or "",
        secret=config.hmac_secret,
        window_seconds=config.timestamp_window_seconds,
    )

    if not result.success:
        logger.warning(f"Auth failed: {result.error}")
        raise HTTPException(status_code=401, detail=result.error)


@app.post("/print", response_model=PrintResponse, dependencies=[Depends(verify_auth)])
async def print_receipt(request: Request, body: PrintRequest):
    """Print a receipt with the given idea text."""
    config = get_config()

    # Check for duplicate if dedupe is enabled
    if _dedupe_store and body.request_id:
        if not _dedupe_store.check_and_mark(body.request_id):
            logger.info(f"Duplicate request: {body.request_id}")
            return PrintResponse(
                success=True,
                message="Duplicate request (already processed)",
                idea_id=body.idea_id,
            )

    # Build receipt
    profile = PrinterProfile()
    receipt_bytes = build_receipt(
        idea_text=body.idea_text,
        idea_id=body.idea_id,
        timestamp=datetime.now(),
        profile=profile,
    )

    # Acquire lock and print
    async with _print_lock:
        try:
            transport = get_transport(config)
            with transport:
                transport.write(receipt_bytes)

            logger.info(f"Printed receipt for idea: {body.idea_id or 'unnamed'}")

            return PrintResponse(
                success=True,
                message="Receipt printed successfully",
                idea_id=body.idea_id,
            )

        except Exception as e:
            logger.error(f"Print failed: {e}")
            raise HTTPException(status_code=500, detail=f"Print failed: {str(e)}")


def create_app() -> FastAPI:
    """Create and return the FastAPI application."""
    return app
