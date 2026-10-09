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
            self._link = Simulator(self.state)
            self.state.remote = False
            return
        try:
            self._link = SerialTransport(self.port_name, self.state.baudrate, self.state.rtscts)
            self._send(protocol.DCL + protocol.REN + "*CLS")
            self.state.remote = True
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
        code, text = parse_error(self._send("ERR?"))
        self.state.error = text
        if text:
            self.last_error = text
        return text

    def poll(self) -> None:
        state = self.state
        self._send("SEL_A")
        state.measured_va = protocol.parse_number(self._send("VOUT?")) or state.measured_va
        state.measured_ia = protocol.parse_number(self._send("IOUT?")) or state.measured_ia
        state.va = protocol.parse_number(self._send("VSET?")) or state.va
        state.ia = protocol.parse_number(self._send("ISET?")) or state.ia
        cont = protocol.parse_token(self._send("CONT?"), ("CONT_CV", "CONT_CC"))
        if cont:
            state.cont_a = "CV" if cont == "CONT_CV" else "CC"
        self._send("SEL_B")
        state.measured_vb = protocol.parse_number(self._send("VOUT?")) or state.measured_vb
        state.measured_ib = protocol.parse_number(self._send("IOUT?")) or state.measured_ib
        state.vb = protocol.parse_number(self._send("VSET?")) or state.vb
        state.ib = protocol.parse_number(self._send("ISET?")) or state.ib
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
        self.check_error()

    def set_voltage(self, channel: str, value: float) -> None:
        self._send(protocol.join_commands(protocol.select_channel(channel), protocol.voltage_set(value)))
        self.check_error()

    def set_current(self, channel: str, value: float) -> None:
        self._send(protocol.join_commands(protocol.select_channel(channel), protocol.current_set(value)))
        self.check_error()

    def set_mode(self, mode: str) -> None:
        self._send(protocol.operating_mode(mode))
        self.check_error()

    def set_function(self, kind: str) -> None:
        self._send(protocol.join_commands(protocol.select_channel(self.state.channel), protocol.function_mode(kind)))
        self.check_error()

    def set_protection(self, kind: str) -> None:
        self._send(protocol.protection(kind))
        self.check_error()

    def set_output(self, enabled: bool) -> bool:
        self._send(protocol.output_on() if enabled else protocol.output_off())
        parsed = protocol.parse_output(self._send(protocol.output_query()))
        self.check_error()
        self.state.output_on = enabled if parsed is None else parsed
        return self.state.output_on

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

    def set_local(self) -> None:
        self._send(protocol.GTL)
        self.state.remote = False
        self.state.lockout = False
