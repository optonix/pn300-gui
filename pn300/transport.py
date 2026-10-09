"""Serielle Leitung. Senden endet mit LF, Antworten kommen mit CR+LF."""

from __future__ import annotations


class SerialTransport:
    def __init__(self, port: str, baudrate: int = 9600, rtscts: bool = False) -> None:
        import serial

        self.port = port
        self.baudrate = baudrate
        self.rtscts = rtscts
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
            rtscts=rtscts,
        )

    def send(self, command: str) -> str:
        self._serial.write(f"{command}\n".encode("ascii"))
        if command.endswith("?"):
            return self._serial.readline().decode("ascii", errors="replace").strip()
        return ""

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()
