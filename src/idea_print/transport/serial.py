"""Serial port transport for thermal printers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from serial import Serial


class SerialTransport:
    """Transport for serial port communication with thermal printers."""

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 5.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: "Serial | None" = None

    def open(self) -> None:
        """Open the serial port."""
        import serial

        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Close the serial port."""
        if self._serial:
            self._serial.close()
            self._serial = None

    def write(self, data: bytes) -> int:
        """Write data to the serial port."""
        if not self._serial:
            raise RuntimeError("Transport not open")
        return self._serial.write(data)

    def __enter__(self) -> "SerialTransport":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def list_serial_ports() -> list[dict[str, str]]:
    """List available serial ports."""
    from serial.tools import list_ports

    ports = []
    for port in list_ports.comports():
        ports.append(
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
            }
        )
    return ports
