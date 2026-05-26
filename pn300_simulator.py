class PN300State:
    def __init__(self):
        self.voltage_a = 0.00
        self.current_a = 0.001
        self.voltage_b = 0.00
        self.current_b = 0.001
        self.mode = "IND"          # IND, TRAC, PAR
        self.output_on = False
        self.cv_cc_a = "CV"
        self.cv_cc_b = "CV"
        self.selected_channel = "A"
        self.remote = False

    def format_display(self):
        ch = "A" if self.selected_channel == "A" else "B"
        v = self.voltage_a if ch == "A" else self.voltage_b
        i = self.current_a if ch == "A" else self.current_b
        status = self.cv_cc_a if ch == "A" else self.cv_cc_b
        return f"{v:5.2f}V  {i:6.3f}A  {status}"
