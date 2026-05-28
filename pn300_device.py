import serial
import time
from typing import Optional

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
            print(f"✅ Verbunden mit PN300 auf {self.port}")
            return True
        except Exception as e:
            print(f"❌ Verbindungsfehler: {e}")
            return False

    def send_command(self, cmd: str) -> str:
        if not self.connected or not self.ser:
            return "ERROR: Not connected"
        try:
            self.ser.write(f"{cmd}\r\n".encode())
            time.sleep(0.2)
            response = self.ser.readline().decode().strip()
            return response if response else "OK"
        except:
            return "ERROR: Communication failed"

    def get_idn(self):
        return self.send_command("*IDN?")

    def set_voltage(self, channel: str, voltage: float):
        return self.send_command(f"VSET{channel} {voltage:.2f}")

    def set_current(self, channel: str, current: float):
        return self.send_command(f"ISET{channel} {current:.3f}")

    def set_mode(self, mode: str):
        return self.send_command(f"OPER:{mode}")

    def output_on(self):
        return self.send_command("OUT ON")

    def output_off(self):
        return self.send_command("OUT OFF")