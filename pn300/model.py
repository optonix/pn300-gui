"""Zustand der Quellen A und B."""

from __future__ import annotations

V_MAX = 30.0
I_MAX = 2.3
I_MIN = 0.001
I_MAX_PAR = 4.6
I_MIN_PAR = 0.3
MODES = ("IND", "TRACK", "PAR")


class SupplyState:
    def __init__(self) -> None:
        self.mains = True
        self.channel = "A"
        self.mode = "IND"
        self.output_on = False
        self.remote = False
        self.lockout = False
        self.va = 5.00
        self.ia = 0.500
        self.vb = 5.00
        self.ib = 0.500
        self.measured_va = 5.00
        self.measured_ia = 0.0
        self.measured_vb = 5.00
        self.measured_ib = 0.0
        self.cont_a = "CV"
        self.cont_b = "CV"
        self.protection = "LIM"
        self.edit: str | None = None
        self.draft = ""
        self.mem_slot = 0
        self.memories: dict[int, tuple[float, float, float, float, str]] = {}
        self.message = ""
        self.error = ""
        self.identity = ""
        self.baudrate = 9600
        self.rtscts = False

    def selected_v(self) -> float:
        return self.va if self.channel == "A" else self.vb

    def selected_i(self) -> float:
        return self.ia if self.channel == "A" else self.ib

    def i_limit(self) -> float:
        return I_MAX_PAR if self.mode == "PAR" else I_MAX

    def i_floor(self) -> float:
        return I_MIN_PAR if self.mode == "PAR" else I_MIN
