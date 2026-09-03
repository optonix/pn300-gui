import logging
import time
from typing import List, Optional

import serial
from serial.tools import list_ports

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class PN300Device:
    """RS-232 Schnittstelle zum Digimess / Grundig PN 300."""

    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.connected = False

    @staticmethod
    def list_ports() -> List[str]:
        return [p.device for p in list_ports.comports()]

    def connect(self, port: Optional[str] = None) -> bool:
        if port:
            self.port = port
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(
                self.port,
                self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
            )
            self.connected = True
            logging.info("Verbunden mit PN300 auf %s", self.port)
            return True
        except Exception as e:
            self.connected = False
            logging.error("Verbindungsfehler: %s", e)
            return False

    def send_command(self, cmd: str) -> str:
        if not self.connected or not self.ser:
            return "ERROR: Not connected"
        try:
            self.ser.reset_input_buffer()
            self.ser.write(f"{cmd}\r\n".encode("ascii"))
            time.sleep(0.25)
            response = self.ser.readline().decode("ascii", errors="ignore").strip()
            logging.info("→ %s | ← %s", cmd, response)
            return response if response else "OK"
        except Exception as e:
            logging.error("Kommunikationsfehler: %s", e)
            return f"ERROR: {e}"

    def get_idn(self) -> str:
        return self.send_command("*IDN?")

    def set_voltage(self, channel: str, voltage: float) -> str:
        return self.send_command(f"VSET{channel.upper()} {voltage:.2f}")

    def set_current(self, channel: str, current: float) -> str:
        return self.send_command(f"ISET{channel.upper()} {current:.3f}")

    def get_voltage(self, channel: str) -> str:
        return self.send_command(f"VOUT{channel.upper()}?")

    def get_current(self, channel: str) -> str:
        return self.send_command(f"IOUT{channel.upper()}?")

    def set_mode(self, mode: str) -> str:
        return self.send_command(f"OPER:{mode.upper()}")

    def output_on(self) -> str:
        return self.send_command("OUT ON")

    def output_off(self) -> str:
        return self.send_command("OUT OFF")

    def save_preset(self, num: int) -> str:
        return self.send_command(f"*SAV {num}")

    def recall_preset(self, num: int) -> str:
        return self.send_command(f"*RCL {num}")

    def get_status(self) -> str:
        return self.send_command("STB?")

    def get_error(self) -> str:
        return self.send_command("ESR?")

    def reset(self) -> str:
        return self.send_command("*RST")

    def close(self):
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self.connected = False
