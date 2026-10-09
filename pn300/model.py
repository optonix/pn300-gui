"""Zustand der Quellen A und B."""

from __future__ import annotations

V_MAX = 30.0
I_MAX = 2.3
I_MAX_PAR = 4.6
MODES = ("IND", "TRACK", "PAR")


class SupplyState:
    def __init__(self) -> None:
        self.mains = True
        self.channel = "A"
        self.mode = "IND"
        self.output_on = False
        self.remote = False
        self.va = 5.00
        self.ia = 0.500
        self.vb = 5.00
        self.ib = 0.500
        self.edit: str | None = None
        self.draft = ""
        self.mem_slot = 1
        self.memories: dict[int, tuple[float, float, float, float, str]] = {}
        self.message = ""

    def selected_v(self) -> float:
        return self.va if self.channel == "A" else self.vb

    def selected_i(self) -> float:
        return self.ia if self.channel == "A" else self.ib

    def i_limit(self) -> float:
        return I_MAX_PAR if self.mode == "PAR" else I_MAX
