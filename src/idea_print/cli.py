"""Command-line interface for idea-print."""

import sys
from pathlib import Path

import click

from .config import Config, PrinterProfile, get_config
from .template import build_receipt, build_test_receipt
from .transport import FileTransport, SerialTransport, UsbTransport
from .transport.serial import list_serial_ports
from .transport.usb import list_usb_printers


@click.group()
@click.version_option()
def main():
    """idea-print: Receipt printer agent for thermal printers."""
    pass


@main.command("list-ports")
def list_ports():
    """List available serial ports."""
    try:
        ports = list_serial_ports()
    except ImportError:
        click.echo("Error: pyserial not installed", err=True)
        sys.exit(1)

    if not ports:
        click.echo("No serial ports found")
        return

    click.echo("Available serial ports:\n")
    for port in ports:
        click.echo(f"  {port['device']}")
        click.echo(f"    Description: {port['description']}")
        click.echo(f"    Hardware ID: {port['hwid']}")
        click.echo()


@main.command("list-usb")
def list_usb():
    """List USB devices (potential printers)."""
    try:
        devices = list_usb_printers()
    except ImportError:
        click.echo("Error: pyusb not installed", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if not devices:
        click.echo("No USB devices found")
        return

    click.echo("USB devices:\n")
    for dev in devices:
        click.echo(f"  {dev['vendor_id']}:{dev['product_id']}")
        click.echo(f"    Manufacturer: {dev['manufacturer']}")
        click.echo(f"    Product: {dev['product']}")
        click.echo(f"    Serial: {dev['serial']}")
        click.echo()


@main.command("render")
@click.option(
    "--idea-text",
    "-t",
    required=True,
    help="The idea text to print",
)
@click.option(
    "--idea-id",
    "-i",
    default=None,
    help="Optional idea ID",
)
@click.option(
    "--out",
    "-o",
    required=True,
    type=click.Path(),
    help="Output file path",
)
@click.option(
    "--chars-per-line",
    default=48,
    help="Characters per line (default: 48)",
)
def render(idea_text: str, idea_id: str | None, out: str, chars_per_line: int):
    """Render a receipt to a file without printing."""
    profile = PrinterProfile(chars_per_line=chars_per_line)
    receipt_bytes = build_receipt(
        idea_text=idea_text,
        idea_id=idea_id,
        profile=profile,
    )

    Path(out).write_bytes(receipt_bytes)
    click.echo(f"Rendered {len(receipt_bytes)} bytes to {out}")


@main.command("print")
@click.option(
    "--port",
    "-p",
    required=True,
    help="Serial port (e.g., /dev/cu.usbserial-XXX)",
)
@click.option(
    "--baud",
    "-b",
    default=9600,
    help="Baud rate (default: 9600)",
)
@click.option(
    "--idea-text",
    "-t",
    default=None,
    help="The idea text to print (omit for test print)",
)
@click.option(
    "--idea-id",
    "-i",
    default=None,
    help="Optional idea ID",
)
@click.option(
    "--chars-per-line",
    default=48,
    help="Characters per line (default: 48)",
)
def print_cmd(
    port: str,
    baud: int,
    idea_text: str | None,
    idea_id: str | None,
    chars_per_line: int,
):
    """Print a receipt to a serial printer."""
    profile = PrinterProfile(chars_per_line=chars_per_line)

    if idea_text:
        receipt_bytes = build_receipt(
            idea_text=idea_text,
            idea_id=idea_id,
            profile=profile,
        )
    else:
        click.echo("No idea text provided, printing test receipt...")
        receipt_bytes = build_test_receipt(profile=profile)

    try:
        transport = SerialTransport(port=port, baudrate=baud)
        with transport:
            transport.write(receipt_bytes)
        click.echo(f"Printed {len(receipt_bytes)} bytes to {port}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("print-usb")
@click.option(
    "--vendor-id",
    "-v",
    required=True,
    help="USB Vendor ID (e.g., 0x0483)",
)
@click.option(
    "--product-id",
    "-p",
    required=True,
    help="USB Product ID (e.g., 0x5720)",
)
@click.option(
    "--idea-text",
    "-t",
    default=None,
    help="The idea text to print (omit for test print)",
)
@click.option(
    "--idea-id",
    "-i",
    default=None,
    help="Optional idea ID",
)
@click.option(
    "--chars-per-line",
    default=48,
    help="Characters per line (default: 48)",
)
def print_usb(
    vendor_id: str,
    product_id: str,
    idea_text: str | None,
    idea_id: str | None,
    chars_per_line: int,
):
    """Print a receipt to a USB printer."""
    # Parse hex values
    try:
        vid = int(vendor_id, 16) if vendor_id.startswith("0x") else int(vendor_id)
        pid = int(product_id, 16) if product_id.startswith("0x") else int(product_id)
    except ValueError:
        click.echo("Error: Invalid vendor or product ID", err=True)
        sys.exit(1)

    profile = PrinterProfile(chars_per_line=chars_per_line)

    if idea_text:
        receipt_bytes = build_receipt(
            idea_text=idea_text,
            idea_id=idea_id,
            profile=profile,
        )
    else:
        click.echo("No idea text provided, printing test receipt...")
        receipt_bytes = build_test_receipt(profile=profile)

    try:
        transport = UsbTransport(vendor_id=vid, product_id=pid)
        with transport:
            transport.write(receipt_bytes)
        click.echo(f"Printed {len(receipt_bytes)} bytes to USB device {vendor_id}:{product_id}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("serve")
@click.option(
    "--host",
    "-h",
    default=None,
    help="Host to bind to (default: from SERVER_HOST env or 0.0.0.0)",
)
@click.option(
    "--port",
    "-p",
    default=None,
    type=int,
    help="Port to bind to (default: from SERVER_PORT env or 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def serve(host: str | None, port: int | None, reload: bool):
    """Start the HTTP server."""
    import uvicorn

    config = get_config()
    host = host or config.server_host
    port = port or config.server_port

    click.echo(f"Starting server on {host}:{port}")
    click.echo(f"Transport: {config.printer_transport}")

    if not config.hmac_secret:
        click.echo("WARNING: HMAC_SECRET not set, authentication disabled!", err=True)

    uvicorn.run(
        "idea_print.server:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
