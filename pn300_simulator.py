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

    def get_display_values(self):
        ch = self.selected_channel
        v = self.voltage_a if ch == "A" else self.voltage_b
        i = self.current_a if ch == "A" else self.current_b
        status = self.cv_cc_a if ch == "A" else self.cv_cc_b
        return v, i, status