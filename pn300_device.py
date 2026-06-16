import serial
import time
import logging
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PN300Device:
    def __init__(self, port: str = "COM3", baudrate: int = 9600):
        self.port = port
        self.baudrate = baudrate
        self.ser: Optional[serial.Serial] = None
        self.connected = False

    def connect(self) -> bool:
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.connected = True
            logging.info(f"✅ Verbunden mit PN300 auf {self.port}")
            # Testverbindung
            idn = self.get_idn()
            logging.info(f"Geräte-ID: {idn}")
            return True
        except Exception as e:
            logging.error(f"❌ Verbindungsfehler: {e}")
            return False

    def send_command(self, cmd: str) -> str:
        if not self.connected or not self.ser:
            return "ERROR: Not connected"
        try:
            self.ser.write(f"{cmd}\r\n".encode('ascii'))
            time.sleep(0.3)
            response = self.ser.readline().decode('ascii', errors='ignore').strip()
            logging.info(f"→ {cmd} | ← {response}")
            return response if response else "OK"
        except Exception as e:
            logging.error(f"Kommunikationsfehler: {e}")
            return f"ERROR: {e}"

    # === Grundbefehle ===
    def get_idn(self) -> str:
        return self.send_command("*IDN?")

    def set_voltage(self, channel: str, voltage: float) -> str:
        ch = channel.upper()
        return self.send_command(f"VSET{ch} {voltage:.2f}")

    def set_current(self, channel: str, current: float) -> str:
        ch = channel.upper()
        return self.send_command(f"ISET{ch} {current:.3f}")

    def get_voltage(self, channel: str) -> str:
        ch = channel.upper()
        return self.send_command(f"VOUT{ch}?")

    def get_current(self, channel: str) -> str:
        ch = channel.upper()
        return self.send_command(f"IOUT{ch}?")

    def set_mode(self, mode: str) -> str:
        mode = mode.upper()
        return self.send_command(f"OPER:{mode}")

    def output_on(self) -> str:
        return self.send_command("OUT ON")

    def output_off(self) -> str:
        return self.send_command("OUT OFF")

    # === Erweiterte Befehle ===
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
            self.ser.close()
            self.connected = False
