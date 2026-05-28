import serial
import time
import logging
from typing import Optional

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
            self.send_command("*IDN?")  # Test
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

    def get_idn(self): return self.send_command("*IDN?")
    def set_voltage(self, ch: str, v: float): return self.send_command(f"VSET{ch} {v:.2f}")
    def set_current(self, ch: str, i: float): return self.send_command(f"ISET{ch} {i:.3f}")
    def get_voltage(self, ch: str): return self.send_command(f"VOUT{ch}?")
    def get_current(self, ch: str): return self.send_command(f"IOUT{ch}?")
    def set_mode(self, mode: str): return self.send_command(f"OPER:{mode}")
    def output_on(self): return self.send_command("OUT ON")
    def output_off(self): return self.send_command("OUT OFF")
    def save_preset(self, num: int): return self.send_command(f"*SAV {num}")
    def recall_preset(self, num: int): return self.send_command(f"*RCL {num}")