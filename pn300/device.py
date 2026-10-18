"""Fassade für die Oberfläche. Simulator oder COM-Port, gleiche Aufrufe."""

from __future__ import annotations

from pn300 import protocol
from pn300.errors import parse_error
from pn300.model import SupplyState
from pn300.simulator import Simulator
from pn300.transport import SerialTransport


class Device:
    def __init__(self) -> None:
        self.state = SupplyState()
        self.port_name = "Simulator"
        self._link: Simulator | SerialTransport = Simulator(self.state)
        self.last_error = ""
        self.enter_remote()

    def use_port(self, name: str, baudrate: int | None = None, rtscts: bool | None = None) -> None:
        self.close()
        self.port_name = name or "Simulator"
        self.last_error = ""
        if baudrate:
            self.state.baudrate = baudrate
        if rtscts is not None:
            self.state.rtscts = rtscts
        if self.port_name == "Simulator":
            if not isinstance(self._link, Simulator):
                self._link = Simulator(self.state)
            return
        try:
            self._link = SerialTransport(self.port_name, self.state.baudrate, self.state.rtscts)
            self._send(protocol.DCL + protocol.REN + "*CLS")
            self.state.remote = True
            self.state.output_on = False
            self.poll()
        except Exception as exc:
            self.last_error = str(exc)
            self.port_name = "Simulator"
            self._link = Simulator(self.state)

    def close(self) -> None:
        self._link.close()

    def _send(self, command: str) -> str:
        try:
            answer = self._link.send(command)
            self.last_error = ""
            return answer
        except Exception as exc:
            self.last_error = str(exc)
            return ""

    def check_error(self) -> str:
        found = ""
        for _ in range(2):
            code, text = parse_error(self._send("ERR?"))
            if code == 0:
                break
            found = text
        self.state.error = found
        if found:
            self.last_error = found
        return found

    def poll(self) -> None:
        state = self.state
        selected = state.channel
        self._send("SEL_A")
        state.measured_va = self._number(self._send("VOUT?"), state.measured_va)
        state.measured_ia = self._number(self._send("IOUT?"), state.measured_ia)
        state.va = self._number(self._send("VSET?"), state.va)
        state.ia = self._number(self._send("ISET?"), state.ia)
        cont = protocol.parse_token(self._send("CONT?"), ("CONT_CV", "CONT_CC"))
        if cont:
            state.cont_a = "CV" if cont == "CONT_CV" else "CC"
        self._send("SEL_B")
        state.measured_vb = self._number(self._send("VOUT?"), state.measured_vb)
        state.measured_ib = self._number(self._send("IOUT?"), state.measured_ib)
        state.vb = self._number(self._send("VSET?"), state.vb)
        state.ib = self._number(self._send("ISET?"), state.ib)
        cont = protocol.parse_token(self._send("CONT?"), ("CONT_CV", "CONT_CC"))
        if cont:
            state.cont_b = "CV" if cont == "CONT_CV" else "CC"
        mode = protocol.parse_token(self._send("OPER?"), ("OPER_IND", "OPER_TRAC", "OPER_PAR"))
        if mode:
            state.mode = {"OPER_IND": "IND", "OPER_TRAC": "TRACK", "OPER_PAR": "PAR"}[mode]
        output = protocol.parse_output(self._send("OUT?"))
        if output is not None:
            state.output_on = output
        protection = protocol.parse_token(self._send("PROT?"), ("PROT_LIM", "PROT_CUT"))
        if protection:
            state.protection = "LIM" if protection == "PROT_LIM" else "CUT"
        self._send(protocol.select_channel(selected))
        self.check_error()

    def _number(self, answer: str, previous: float) -> float:
        parsed = protocol.parse_number(answer)
        return previous if parsed is None else parsed

    def set_voltage(self, channel: str, value: float) -> None:
        self._send(protocol.join_commands(protocol.select_channel(channel), protocol.voltage_set(value)))
        if self.check_error() or isinstance(self._link, Simulator):
            return
        if channel == "A" or self.state.mode in ("TRACK", "PAR"):
            self.state.va = value
        if channel == "B" or self.state.mode in ("TRACK", "PAR"):
            self.state.vb = value

    def set_current(self, channel: str, value: float) -> None:
        self._send(protocol.join_commands(protocol.select_channel(channel), protocol.current_set(value)))
        if self.check_error() or isinstance(self._link, Simulator):
            return
        if channel == "A" or self.state.mode == "PAR":
            self.state.ia = value
        if channel == "B" or self.state.mode == "PAR":
            self.state.ib = value

    def set_mode(self, mode: str) -> None:
        self._send(protocol.operating_mode(mode))
        if self.check_error() or isinstance(self._link, Simulator):
            return
        self.state.mode = mode
        if mode == "TRACK":
            self.state.vb = self.state.va
        if mode == "PAR":
            self.state.vb = self.state.va
            current = min(max(self.state.ia, 0.3), 4.6)
            self.state.ia = self.state.ib = current
            self.set_current("A", current)

    def set_function(self, kind: str) -> None:
        channel = self.state.channel
        self._send(protocol.join_commands(protocol.select_channel(channel), protocol.function_mode(kind)))
        if self.check_error() or isinstance(self._link, Simulator):
            return
        if channel == "A" or self.state.mode == "PAR":
            self.state.cont_a = kind
        if channel == "B" or self.state.mode == "PAR":
            self.state.cont_b = kind

    def set_protection(self, kind: str) -> None:
        self._send(protocol.protection(kind))
        if self.check_error() or isinstance(self._link, Simulator):
            return
        self.state.protection = kind

    def set_output(self, enabled: bool) -> bool:
        self._send(protocol.output_on() if enabled else protocol.output_off())
        parsed = protocol.parse_output(self._send(protocol.output_query()))
        error = self.check_error()
        if parsed is not None:
            self.state.output_on = parsed
        elif not error:
            self.state.output_on = enabled
        return self.state.output_on

    def simulator_mains(self, on: bool) -> None:
        if self.port_name == "Simulator" and isinstance(self._link, Simulator):
            self._link.mains(on)

    def save(self, slot: int) -> None:
        self._send(protocol.save_preset(slot))
        self.check_error()

    def recall(self, slot: int) -> None:
        self._send(protocol.recall_preset(slot))
        self.poll()

    def reset(self) -> None:
        self._send("*RST;*CLS")
        self.poll()

    def identify(self) -> str:
        self.state.identity = self._send("*IDN?")
        return self.state.identity

    def lock_local(self) -> None:
        self._send(protocol.LLO)
        self.state.lockout = True
        self.state.remote = True

    def enter_remote(self) -> None:
        self._send(protocol.REN)
        self.state.remote = True
        self.state.output_on = False

    def set_local(self) -> None:
        self._send(protocol.GTL)
        self.state.remote = False
