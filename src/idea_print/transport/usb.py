"""USB transport for thermal printers using pyusb."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import usb.core


class UsbTransport:
    """Transport for direct USB communication with thermal printers."""

    def __init__(
        self,
        vendor_id: int,
        product_id: int,
        out_endpoint: int | None = None,
        interface: int = 0,
    ):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.out_endpoint = out_endpoint
        self.interface = interface
        self._device: "usb.core.Device | None" = None
        self._endpoint = None

    def open(self) -> None:
        """Open the USB device."""
        import usb.core
        import usb.util

        self._device = usb.core.find(
            idVendor=self.vendor_id,
            idProduct=self.product_id,
        )

        if self._device is None:
            raise RuntimeError(
                f"USB device not found: {self.vendor_id:04x}:{self.product_id:04x}"
            )

        # Detach kernel driver if necessary
        try:
            if self._device.is_kernel_driver_active(self.interface):
                self._device.detach_kernel_driver(self.interface)
        except (usb.core.USBError, NotImplementedError):
            pass  # Not all platforms support this

        # Set configuration
        try:
            self._device.set_configuration()
        except usb.core.USBError:
            pass  # May already be configured

        # Find the OUT endpoint
        cfg = self._device.get_active_configuration()
        intf = cfg[(self.interface, 0)]

        if self.out_endpoint:
            self._endpoint = usb.util.find_descriptor(
                intf,
                bEndpointAddress=self.out_endpoint,
            )
        else:
            # Find first OUT endpoint
            self._endpoint = usb.util.find_descriptor(
                intf,
                custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
                == usb.util.ENDPOINT_OUT,
            )

        if self._endpoint is None:
            raise RuntimeError("Could not find OUT endpoint")

    def close(self) -> None:
        """Close the USB device."""
        if self._device:
            import usb.util

            usb.util.dispose_resources(self._device)
            self._device = None
            self._endpoint = None

    def write(self, data: bytes) -> int:
        """Write data to the USB device."""
        if not self._device or not self._endpoint:
            raise RuntimeError("Transport not open")
        return self._endpoint.write(data)

    def __enter__(self) -> "UsbTransport":
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def list_usb_printers() -> list[dict]:
    """List USB devices that might be printers."""
    import usb.core

    printers = []

    # Common thermal printer vendor IDs
    # 0x0483 = STMicroelectronics (many thermal printers)
    # 0x0416 = WinChipHead (CH340)
    # 0x1a86 = QinHeng Electronics
    # 0x04b8 = Epson
    # 0x0dd4 = Custom Engineering

    for device in usb.core.find(find_all=True):
        try:
            manufacturer = device.manufacturer or "Unknown"
            product = device.product or "Unknown"

            printers.append({
                "vendor_id": f"0x{device.idVendor:04x}",
                "product_id": f"0x{device.idProduct:04x}",
                "manufacturer": manufacturer,
                "product": product,
                "serial": device.serial_number or "N/A",
            })
        except (usb.core.USBError, ValueError):
            # Can't read device info, skip it
            continue

    return printers
