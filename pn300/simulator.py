"""Dieselbe Aufrufseite wie die serielle Leitung, ohne Gerät."""

from __future__ import annotations

from pn300.model import SupplyState
from pn300.protocol import DCL, GTL, LLO, REN


class Simulator:
    def __init__(self, state: SupplyState | None = None) -> None:
        self.state = state or SupplyState()
        self.sent: list[str] = []
        self.error_code = 0

    def send(self, command: str) -> str:
        self.sent.append(command)
        answers = []
        for part in command.split(";"):
            answers.append(self._one(part))
        return next((item for item in reversed(answers) if item), "")

    def _one(self, command: str) -> str:
        text = command.strip()
        if text.startswith(DCL) or text.startswith(REN) or text.startswith(LLO) or text.startswith(GTL):
            if DCL in text:
                self.error_code = 0
            if REN in text:
                self.state.remote = True
            if LLO in text:
                self.state.lockout = True
                self.state.remote = True
            if GTL in text:
                self.state.remote = False
                self.state.lockout = False
            text = text.strip("\t\x19\x01\x14")
            if not text:
                return ""
        if not self.state.remote and text not in {"*IDN?", "ERR?"} and not text.startswith("*"):
            self.error_code = 132
        name, _, arg = text.partition(" ")
        state = self.state
        if name == "OPER_IND":
            state.mode = "IND"
        elif name == "OPER_TRAC":
            state.mode = "TRACK"
            state.vb = state.va
        elif name == "OPER_PAR":
            state.mode = "PAR"
            state.vb = state.va
            state.ib = state.ia
        elif name == "OPER?":
            return {"IND": "OPER_IND", "TRACK": "OPER_TRAC", "PAR": "OPER_PAR"}[state.mode]
        elif name == "SEL_A":
            state.channel = "A"
        elif name == "SEL_B":
            state.channel = "B"
        elif name == "SEL?":
            return "SEL_A" if state.channel == "A" else "SEL_B"
        elif name == "CONT_CV":
            self._set_cont("CV")
        elif name == "CONT_CC":
            self._set_cont("CC")
        elif name == "CONT?":
            kind = state.cont_a if state.channel == "A" else state.cont_b
            return "CONT_CV" if kind == "CV" else "CONT_CC"
        elif name == "VSET":
            self._set_v(float(arg))
        elif name == "VSET_MIN":
            self._set_v(0.0)
        elif name == "VSET_MAX":
            self._set_v(30.0)
        elif name == "VSET?":
            value = state.va if state.channel == "A" else state.vb
            return f"V {value:.2f}"
        elif name == "VOUT?":
            value = state.measured_va if state.channel == "A" else state.measured_vb
            return f"V {value:.2f}"
        elif name == "ISET":
            self._set_i(float(arg))
        elif name == "ISET_MIN":
            self._set_i(state.i_floor())
        elif name == "ISET_MAX":
            self._set_i(state.i_limit())
        elif name == "ISET?":
            value = state.ia if state.channel == "A" else state.ib
            return f"A {value:.3f}"
        elif name == "IOUT?":
            value = state.measured_ia if state.channel == "A" else state.measured_ib
            return f"A {value:.3f}"
        elif name == "OUT_ON":
            state.output_on = True
            self._measure()
            return "OUT_ON"
        elif name == "OUT_OFF":
            state.output_on = False
            state.measured_ia = 0.0
            state.measured_ib = 0.0
            return "OUT_OFF"
        elif name == "OUT?":
            return "OUT_ON" if state.output_on else "OUT_OFF"
        elif name == "PROT_LIM":
            state.protection = "LIM"
        elif name == "PROT_CUT":
            state.protection = "CUT"
        elif name == "PROT?":
            return "PROT_LIM" if state.protection == "LIM" else "PROT_CUT"
        elif name == "*SAV":
            slot = int(arg)
            state.memories[slot] = (state.va, state.ia, state.vb, state.ib, state.mode)
        elif name == "*RCL":
            slot = int(arg)
            if slot not in state.memories:
                self.error_code = 96
                return ""
            state.va, state.ia, state.vb, state.ib, state.mode = state.memories[slot]
        elif name == "*RST":
            state.output_on = False
            state.mode = "IND"
            state.cont_a = state.cont_b = "CV"
            state.va = state.vb = 0.0
            state.ia = state.ib = 2.3
            state.protection = "LIM"
        elif name == "*IDN?":
            return "GRUNDIG,PN300,0,SIM"
        elif name == "*CLS":
            self.error_code = 0
        elif name == "ERR?":
            code = self.error_code
            self.error_code = 0
            return str(code)
        elif name == "*OPC?":
            return "1"
        return ""

    def _set_cont(self, kind: str) -> None:
        if self.state.channel == "A" or self.state.mode == "PAR":
            self.state.cont_a = kind
        if self.state.channel == "B" or self.state.mode == "PAR":
            self.state.cont_b = kind

    def _set_v(self, value: float) -> None:
        if self.state.channel == "A" or self.state.mode in ("TRACK", "PAR"):
            self.state.va = value
        if self.state.channel == "B" or self.state.mode in ("TRACK", "PAR"):
            self.state.vb = value
        self._measure()

    def _set_i(self, value: float) -> None:
        if self.state.channel == "A" or self.state.mode == "PAR":
            self.state.ia = value
        if self.state.channel == "B" or self.state.mode == "PAR":
            self.state.ib = value
        self._measure()

    def _measure(self) -> None:
        state = self.state
        state.measured_va = state.va if state.output_on else 0.0
        state.measured_vb = state.vb if state.output_on else 0.0
        state.measured_ia = min(state.ia, 0.1) if state.output_on else 0.0
        state.measured_ib = min(state.ib, 0.1) if state.output_on else 0.0

    def close(self) -> None:
        return None
