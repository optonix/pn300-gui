class PN300State:
    def __init__(self):
        self.voltage_a = 0.00
        self.current_a = 0.001
        self.voltage_b = 0.00
        self.current_b = 0.001
        self.mode = "IND"  # IND, TRAC, PAR
        self.output_on = False
        self.cv_cc_a = "CV"
        self.cv_cc_b = "CV"
        self.selected_channel = "A"
        self.remote = False
        self.presets = {
            1: {"voltage_a": 5.00, "current_a": 0.500, "voltage_b": 5.00, "current_b": 0.500},
            2: {"voltage_a": 12.00, "current_a": 1.000, "voltage_b": 12.00, "current_b": 1.000},
            3: {"voltage_a": 24.00, "current_a": 1.500, "voltage_b": 24.00, "current_b": 1.500},
        }

    def get_display_values(self):
        ch = self.selected_channel
        v = self.voltage_a if ch == "A" else self.voltage_b
        i = self.current_a if ch == "A" else self.current_b
        status = self.cv_cc_a if ch == "A" else self.cv_cc_b
        return v, i, status

    def set_voltage(self, channel: str, value: float):
        value = min(30.0, max(0.0, float(value)))
        if channel.upper() == "A":
            self.voltage_a = value
        else:
            self.voltage_b = value
        return value

    def set_current(self, channel: str, value: float):
        value = min(2.3, max(0.0, float(value)))
        if channel.upper() == "A":
            self.current_a = value
        else:
            self.current_b = value
        return value

    def save_preset(self, num: int):
        self.presets[num] = {
            "voltage_a": self.voltage_a,
            "current_a": self.current_a,
            "voltage_b": self.voltage_b,
            "current_b": self.current_b,
        }

    def recall_preset(self, num: int):
        data = self.presets.get(num)
        if not data:
            return False
        self.voltage_a = data["voltage_a"]
        self.current_a = data["current_a"]
        self.voltage_b = data["voltage_b"]
        self.current_b = data["current_b"]
        return True
