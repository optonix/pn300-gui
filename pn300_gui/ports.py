"""COM-Ports für die Schnittstellenzeile."""

from __future__ import annotations

SIMULATOR = "Simulator"


def list_serial_ports() -> list[str]:
    found = [SIMULATOR]
    try:
        from serial.tools import list_ports
    except ImportError:
        return found
    found.extend(port.device for port in list_ports.comports())
    return found
