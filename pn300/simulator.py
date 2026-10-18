"""Dieselbe Aufrufseite wie die serielle Leitung, ohne Gerät.

Verhalten nach Operating Instructions PN 300, 1/99, Kapitel 6 und 7.
"""

from __future__ import annotations

from pn300.errors import LCD_ALERTS
from pn300.model import SupplyState
from pn300.protocol import DCL, GTL, LLO, REN

PON = 1 << 7
CME = 1 << 5
EXE = 1 << 4
DDE = 1 << 3
QYE = 1 << 2
OPC = 1 << 0
ACC = 1 << 1
ACV = 1 << 0
BCC = 1 << 5
BCV = 1 << 4
LOAD_BIT = 1 << 6
HEAT_BIT = 1 << 7
LIMIT_BITS = ACC | ACV | BCC | BCV

# Strom, den der Simulator bei anliegender Sollspannung ziehen will.
LOAD_AMPS = 0.1

LOCAL_OK = {
    "*IDN?",
    "*CLS",
    "*ESR?",
    "*ESE",
    "*ESE?",
    "*STB?",
    "*SRE",
    "*SRE?",
    "ERR?",
    "DER?",
}


class Simulator:
    def __init__(self, state: SupplyState | None = None) -> None:
        self.state = state or SupplyState()
        self.sent: list[str] = []
        self.errors: list[int] = []
        self.esr = PON
        self.ese = 0
        self.sre = 0
        self.der = 0

    def close(self) -> None:
        return None

    def mains(self, on: bool) -> None:
        self._outputs_off()
        self.state.alert = None
        if not on:
            self.state.lockout = False
            self.errors.clear()

    def send(self, command: str) -> str:
        self.sent.append(command)
        if len(command) > 64:
            self._push(181)
            return ""
        answer = ""
        for part in command.split(";"):
            produced = self._one(part)
            if produced:
                answer = produced
        return answer

    def _one(self, command: str) -> str:
        text = self._controls(command.strip())
        if not text:
            return ""
        if not self.state.remote and not self._allowed_locally(text):
            self._push(132)
            return ""
        name, _, arg = text.partition(" ")
        return self._command(name, arg.strip())

    def _controls(self, text: str) -> str:
        index = 0
        while index < len(text) and text[index] in {DCL, REN, LLO, GTL}:
            mark = text[index]
            if mark == DCL:
                self.errors.clear()
            elif mark == REN:
                self.state.remote = True
                self._outputs_off()
            elif mark == LLO:
                self.state.lockout = True
            elif mark == GTL:
                self.state.remote = False
            index += 1
        return text[index:].strip()

    def _allowed_locally(self, text: str) -> bool:
        name = text.partition(" ")[0]
        return name in LOCAL_OK

    def _command(self, name: str, arg: str) -> str:
        state = self.state
        if name == "OPER_IND":
            state.mode = "IND"
        elif name == "OPER_TRAC":
            state.mode = "TRACK"
            state.vb = state.va
        elif name == "OPER_PAR":
            state.mode = "PAR"
            state.vb = state.va
            current = min(max(state.ia, 0.3), 4.6)
            state.ia = state.ib = current
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
            self._try_voltage(arg)
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
            self._try_current(arg)
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
            state.alert = None
            self._measure()
            return "OUT_ON" if state.output_on else "OUT_OFF"
        elif name == "OUT_OFF":
            self._outputs_off()
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
            self._save(arg)
        elif name == "*RCL":
            self._recall(arg)
        elif name == "*RST":
            self._reset()
        elif name == "*IDN?":
            return "GRUNDIG,PN300,0,0"
        elif name == "*CLS":
            self._clear_status()
        elif name == "ERR?":
            return str(self.errors.pop(0) if self.errors else 0)
        elif name == "DER?":
            return f"DER {self.der}"
        elif name == "*ESR?":
            value = self.esr
            self.esr = 0
            return f"ESR {value}"
        elif name == "*ESE":
            self._mask("ese", arg)
        elif name == "*ESE?":
            return str(self.ese)
        elif name == "*STB?":
            return f"STB {self._stb()}"
        elif name == "*SRE":
            self._mask("sre", arg)
        elif name == "*SRE?":
            return str(self.sre)
        elif name == "*TST?":
            return "0"
        elif name == "*WAI":
            return ""
        elif name == "*OPC":
            self.esr |= OPC
        elif name == "*OPC?":
            self.esr |= OPC
            return "1"
        else:
            self._push(151)
        return ""

    def _try_voltage(self, arg: str) -> None:
        try:
            value = float(arg)
        except ValueError:
            self._push(134)
            return
        if not 0.0 <= value <= 30.0:
            self._push(134)
            return
        self._set_v(value)

    def _try_current(self, arg: str) -> None:
        try:
            value = float(arg)
        except ValueError:
            self._push(134)
            return
        if not self.state.i_floor() - 1e-9 <= value <= self.state.i_limit() + 1e-9:
            self._push(134)
            return
        self._set_i(value)

    def _set_v(self, value: float) -> None:
        state = self.state
        if state.channel == "A" or state.mode in ("TRACK", "PAR"):
            state.va = value
        if state.channel == "B" or state.mode in ("TRACK", "PAR"):
            state.vb = value
        self._measure()

    def _set_i(self, value: float) -> None:
        state = self.state
        if state.channel == "A" or state.mode == "PAR":
            state.ia = value
        if state.channel == "B" or state.mode == "PAR":
            state.ib = value
        self._measure()

    def _set_cont(self, kind: str) -> None:
        state = self.state
        if state.channel == "A" or state.mode == "PAR":
            state.cont_a = kind
        if state.channel == "B" or state.mode == "PAR":
            state.cont_b = kind
        self._measure()

    def _outputs_off(self) -> None:
        state = self.state
        state.output_on = False
        state.measured_va = state.measured_vb = 0.0
        state.measured_ia = state.measured_ib = 0.0
        self.der &= ~LIMIT_BITS

    def _measure(self) -> None:
        if not self.state.output_on:
            self._outputs_off()
            return
        for channel in ("A", "B"):
            if not self.state.output_on:
                return
            self._measure_channel(channel)

    def _measure_channel(self, channel: str) -> None:
        state = self.state
        vset = state.va if channel == "A" else state.vb
        iset = state.ia if channel == "A" else state.ib
        cont = state.cont_a if channel == "A" else state.cont_b
        demand = LOAD_AMPS if vset > 0 else 0.0
        if cont == "CV" and demand > iset + 1e-9:
            self._protect(channel, "I")
            return
        if cont == "CC":
            voltage = iset * vset / LOAD_AMPS if vset > 0 else 0.0
            if voltage > vset + 1e-9 or (iset > 0 and vset <= 0):
                self._protect(channel, "V")
                return
            self._clear_limit(channel)
            self._store(channel, min(voltage, vset), iset)
            return
        self._clear_limit(channel)
        self._store(channel, vset, demand)

    def _protect(self, channel: str, kind: str) -> None:
        self._mark_limit(channel, kind)
        if self.state.protection == "LIM":
            switched = "CC" if kind == "I" else "CV"
            if channel == "A":
                self.state.cont_a = switched
            else:
                self.state.cont_b = switched
            self._store_limited(channel, switched)
            return
        code = 21 if kind == "I" else 22
        self.state.output_on = False
        self.state.measured_va = self.state.measured_vb = 0.0
        self.state.measured_ia = self.state.measured_ib = 0.0
        self.state.alert = LCD_ALERTS[code]
        self._push(code)

    def _store_limited(self, channel: str, cont: str) -> None:
        state = self.state
        vset = state.va if channel == "A" else state.vb
        iset = state.ia if channel == "A" else state.ib
        if cont == "CC":
            voltage = min(vset, iset * vset / LOAD_AMPS) if vset > 0 else 0.0
            self._store(channel, voltage, iset)
            return
        demand = LOAD_AMPS if vset > 0 else 0.0
        self._store(channel, vset, min(demand, iset))

    def _store(self, channel: str, voltage: float, current: float) -> None:
        if channel == "A":
            self.state.measured_va = voltage
            self.state.measured_ia = current
        else:
            self.state.measured_vb = voltage
            self.state.measured_ib = current

    def _mark_limit(self, channel: str, kind: str) -> None:
        bit = {"A": {"V": ACV, "I": ACC}, "B": {"V": BCV, "I": BCC}}[channel][kind]
        other = {"A": {"V": ACC, "I": ACV}, "B": {"V": BCC, "I": BCV}}[channel][kind]
        self.der = (self.der & ~other) | bit

    def _clear_limit(self, channel: str) -> None:
        mask = (ACV | ACC) if channel == "A" else (BCV | BCC)
        self.der &= ~mask

    def _save(self, arg: str) -> None:
        slot = self._slot(arg)
        if slot is None:
            return
        state = self.state
        state.memories[slot] = (
            state.va,
            state.ia,
            state.vb,
            state.ib,
            state.mode,
            state.cont_a,
            state.cont_b,
            state.protection,
        )

    def _recall(self, arg: str) -> None:
        slot = self._slot(arg)
        if slot is None:
            return
        saved = self.state.memories.get(slot)
        if saved is None:
            self.der |= LOAD_BIT
            self.state.alert = LCD_ALERTS[96]
            self._push(96)
            return
        state = self.state
        state.va, state.ia, state.vb, state.ib, state.mode, state.cont_a, state.cont_b, state.protection = saved
        self.der &= ~LOAD_BIT
        self._measure()

    def _slot(self, arg: str) -> int | None:
        try:
            slot = int(arg)
        except ValueError:
            self._push(134)
            return None
        if not 0 <= slot <= 5:
            self._push(134)
            return None
        return slot

    def _reset(self) -> None:
        state = self.state
        state.output_on = False
        state.mode = "IND"
        state.cont_a = state.cont_b = "CV"
        state.va = state.vb = 0.0
        state.ia = state.ib = 2.3
        state.protection = "LIM"
        state.alert = None
        state.measured_va = state.measured_vb = 0.0
        state.measured_ia = state.measured_ib = 0.0
        self.errors.clear()
        self.ese = 0
        self.sre = 0
        self.der = 0
        self.esr = PON

    def _clear_status(self) -> None:
        self.esr &= PON
        self.ese &= PON
        self.sre = 0
        self.errors.clear()

    def _mask(self, target: str, arg: str) -> None:
        try:
            value = int(arg)
        except ValueError:
            self._push(134)
            return
        if not 0 <= value <= 255:
            self._push(134)
            return
        if target == "ese":
            self.ese = value
        else:
            self.sre = value

    def _stb(self) -> int:
        stb = 0
        if self.esr & self.ese:
            stb |= 1 << 5
        masked = stb & self.sre & ~(1 << 6)
        if masked:
            stb |= 1 << 6
        return stb

    def _push(self, code: int) -> None:
        if len(self.errors) < 2:
            self.errors.append(code)
        if code == 151:
            self.esr |= CME
        elif code in {132, 134}:
            self.esr |= EXE
        elif code in {21, 22, 91, 96}:
            self.esr |= DDE
        elif code in {111, 114, 117, 120, 181}:
            self.esr |= QYE
        if code == 91:
            self.der |= HEAT_BIT
