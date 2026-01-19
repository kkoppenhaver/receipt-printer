# idea-print

A Python receipt printer agent that runs an HTTP server accepting print requests, authenticates them via HMAC, renders ESC/POS receipts, and sends them to a thermal printer.

Built for capturing ideas on paper via [Retool](https://retool.com) or any HTTP client.

## Features

- **ESC/POS rendering** - Generates proper thermal printer commands with text wrapping
- **Multiple transports** - Serial, USB, or file output for testing
- **HMAC authentication** - Secure webhook endpoints with signature verification
- **Request deduplication** - Optional SQLite-based idempotency store
- **CLI tools** - Render receipts, list ports, print directly, or run the server

## Installation

### Requirements

- Python 3.10+
- libusb (for USB printer support)

### macOS

```bash
brew install libusb
pip install idea-print
```

### Raspberry Pi / Linux

```bash
sudo apt-get install libusb-1.0-0-dev
pip install idea-print
```

### From source

```bash
git clone https://github.com/YOUR_USERNAME/idea-print.git
cd idea-print
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick Start

### 1. Find your printer

```bash
# List serial ports
idea-print list-ports

# List USB devices
idea-print list-usb
```

### 2. Print a test receipt

```bash
# USB printer (use vendor:product IDs from list-usb)
idea-print print-usb --vendor-id 0x0483 --product-id 0x5720

# Serial printer
idea-print print --port /dev/ttyUSB0
```

### 3. Print an idea

```bash
idea-print print-usb \
  --vendor-id 0x0483 \
  --product-id 0x5720 \
  --idea-text "Build something amazing today!" \
  --idea-id "IDEA-001"
```

## Running the Server

```bash
# Set your HMAC secret for authentication
export HMAC_SECRET="your-secret-key"

# Configure printer (USB example)
export PRINTER_TRANSPORT=usb
export PRINTER_USB_VENDOR=0x0483
export PRINTER_USB_PRODUCT=0x5720

# Start the server
idea-print serve --host 0.0.0.0 --port 8000
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HMAC_SECRET` | (none) | Secret key for request authentication |
| `PRINTER_TRANSPORT` | `serial` | Transport type: `serial`, `usb`, or `file` |
| `PRINTER_PORT` | `/dev/ttyUSB0` | Serial port path |
| `PRINTER_BAUD` | `9600` | Serial baud rate |
| `PRINTER_USB_VENDOR` | (none) | USB vendor ID (hex, e.g., `0x0483`) |
| `PRINTER_USB_PRODUCT` | (none) | USB product ID (hex, e.g., `0x5720`) |
| `FILE_OUTPUT_PATH` | `receipt.bin` | Output path for file transport |
| `SERVER_HOST` | `0.0.0.0` | Server bind address |
| `SERVER_PORT` | `8000` | Server bind port |
| `TIMESTAMP_WINDOW` | `300` | Max age of request timestamp (seconds) |
| `DEDUPE_ENABLED` | `false` | Enable request deduplication |
| `DEDUPE_DB_PATH` | `dedupe.db` | SQLite database path for deduplication |

## API Endpoints

### `GET /health`

Health check endpoint.

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "ok",
  "transport": "usb",
  "dedupe_enabled": false
}
```

### `POST /print`

Print a receipt. Requires HMAC authentication if `HMAC_SECRET` is set.

**Headers:**
- `X-Timestamp`: Unix timestamp of request
- `X-Signature`: HMAC-SHA256 signature (hex)

**Body:**
```json
{
  "idea_text": "Your brilliant idea here",
  "idea_id": "optional-id",
  "request_id": "optional-idempotency-key"
}
```

**Example with authentication:**

```bash
SECRET="your-secret-key"
TIMESTAMP=$(date +%s)
BODY='{"idea_text": "Hello from the API!"}'
SIGNATURE=$(echo -n "${TIMESTAMP}${BODY}" | openssl dgst -sha256 -hmac "$SECRET" | cut -d' ' -f2)

curl -X POST http://localhost:8000/print \
  -H "Content-Type: application/json" \
  -H "X-Timestamp: $TIMESTAMP" \
  -H "X-Signature: $SIGNATURE" \
  -d "$BODY"
```

## CLI Reference

```
idea-print --help

Commands:
  list-ports  List available serial ports
  list-usb    List USB devices (potential printers)
  render      Render a receipt to a file without printing
  print       Print a receipt to a serial printer
  print-usb   Print a receipt to a USB printer
  serve       Start the HTTP server
```

### Render to file (for testing)

```bash
idea-print render \
  --idea-text "Test idea" \
  --idea-id "TEST-001" \
  --out receipt.bin

# Inspect the output
xxd receipt.bin | head
```

## Raspberry Pi Setup

### 1. Install dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libusb-1.0-0-dev
```

### 2. USB permissions

Create a udev rule for your printer:

```bash
# Find your printer's vendor/product ID
lsusb

# Create udev rule (replace IDs with yours)
sudo tee /etc/udev/rules.d/99-thermal-printer.rules << EOF
SUBSYSTEM=="usb", ATTR{idVendor}=="0483", ATTR{idProduct}=="5720", MODE="0666"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 3. Run as a service

```bash
sudo tee /etc/systemd/system/idea-print.service << EOF
[Unit]
Description=Idea Print Server
After=network.target

[Service]
Type=simple
User=pi
Environment=HMAC_SECRET=your-secret-here
Environment=PRINTER_TRANSPORT=usb
Environment=PRINTER_USB_VENDOR=0x0483
Environment=PRINTER_USB_PRODUCT=0x5720
ExecStart=/home/pi/.local/bin/idea-print serve
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable idea-print
sudo systemctl start idea-print
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with auto-reload
idea-print serve --reload
```

## License

MIT
