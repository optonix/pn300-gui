"""Serielle Leitung, 9600 8N1. Öffnen und Schreiben, sonst nichts."""

from __future__ import annotations

import serial


class SerialTransport:
    def __init__(self, port: str, baudrate: int = 9600) -> None:
        self.port = port
        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
        )

    def send(self, command: str) -> str:
        self._serial.write(f"{command}\r\n".encode("ascii"))
        return self._serial.readline().decode("ascii", errors="replace").strip()

    def close(self) -> None:
        if self._serial.is_open:
            self._serial.close()
